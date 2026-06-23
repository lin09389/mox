import { describe, it, expect, beforeAll } from 'vitest'
import { execSync } from 'node:child_process'
import { readFileSync, writeFileSync, readdirSync, mkdirSync, statSync } from 'node:fs'
import { resolve, dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const FRONTEND = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const SCRATCH =
  process.env.GOAL_SCRATCH ||
  'C:\\Users\\JHJ\\AppData\\Local\\Temp\\grok-goal-8568e8927c42\\implementer'

function extractRule(css, selector) {
  const tryMatch = (sel) => {
    const escaped = sel.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const match = css.match(new RegExp(`${escaped}\\s*\\{([^}]+)\\}`))
    return match ? `${sel}{${match[1].trim()}}` : null
  }
  return tryMatch(selector) || tryMatch(selector.replace(/="([^"]+)"/, '=$1'))
}

function ruleHasNoTransform(rule) {
  return rule ? !/\btransform\s*:/.test(rule) : true
}

describe('built CSS polish verification', () => {
  let distCss = ''
  let cssFileName = ''

  beforeAll(() => {
    execSync('npm run build', { cwd: FRONTEND, stdio: 'pipe', encoding: 'utf8' })
    cssFileName = readdirSync(join(FRONTEND, 'dist', 'assets')).find((f) => f.endsWith('.css'))
    if (!cssFileName) throw new Error('No CSS asset in dist/')
    distCss = readFileSync(join(FRONTEND, 'dist', 'assets', cssFileName), 'utf8')
  }, 120000)

  it('dist CSS contains theme rules, correct cascade, and writes evidence artifacts', () => {
    mkdirSync(SCRATCH, { recursive: true })

    const indexHtml = statSync(join(FRONTEND, 'dist', 'index.html'))
    const cssStat = statSync(join(FRONTEND, 'dist', 'assets', cssFileName))

    const distSummary = [
      'Name               SizeBytes FullName',
      '----               --------- --------',
      `index.html         ${indexHtml.size} ${indexHtml.path || join(FRONTEND, 'dist', 'index.html')}`,
      `${cssFileName} ${cssStat.size} ${join(FRONTEND, 'dist', 'assets', cssFileName)}`,
      '',
      `Total bytes: ${indexHtml.size + cssStat.size}`,
    ].join('\n')
    writeFileSync(join(SCRATCH, 'dist-summary.txt'), distSummary, 'utf8')

    const selectors = [
      '.ws-run-btn',
      '.ws-type-card',
      '.ws-type-card:hover',
      '.ws-hub-hero',
      '.ws-hub-tab-indicator',
      '[data-ws-theme="attack"]',
    ]

    const snippets = ['=== EXTRACTED DIST CSS RULE BODIES ===']
    for (const sel of selectors) {
      const rule = extractRule(distCss, sel)
      expect(rule, `missing built rule for ${sel}`).toBeTruthy()
      expect(rule.length, `empty body for ${sel}`).toBeGreaterThan(10)
      snippets.push('')
      snippets.push(rule)
    }

    const wsRunRule = extractRule(distCss, '.ws-run-btn')
    expect(wsRunRule).toContain('var(--ws-accent)')
    const hasRunSpecular =
      distCss.includes('.ws-run-btn::before') ||
      distCss.includes('.ws-run-btn:before') ||
      wsRunRule.includes('inset 0 1px 0')
    expect(hasRunSpecular).toBe(true)

    const btnPrimaryIdx = distCss.indexOf('.btn-primary')
    const wsRunIdx = distCss.indexOf('.ws-run-btn')
    expect(btnPrimaryIdx).toBeGreaterThan(-1)
    expect(wsRunIdx).toBeGreaterThan(btnPrimaryIdx)

    const typeHover = extractRule(distCss, '.ws-type-card:hover')
    expect(ruleHasNoTransform(typeHover)).toBe(true)

    expect(distCss).not.toContain('.attack-type-card:hover')
    expect(distCss).not.toContain('.attack-run-btn')

    const attackTheme = readFileSync(join(FRONTEND, 'src', 'components', 'attack', 'AttackTheme.jsx'), 'utf8')
    expect(attackTheme).toContain('WorkspaceTypeCard')
    expect(attackTheme).toContain('WorkspaceRunButton')

    snippets.push('')
    snippets.push('=== CASCADE CHECK ===')
    snippets.push(`btn-primary offset: ${btnPrimaryIdx}`)
    snippets.push(`ws-run-btn offset: ${wsRunIdx}`)
    snippets.push(`ws-run-btn uses --ws-accent: ${wsRunRule.includes('var(--ws-accent)')}`)

    writeFileSync(join(SCRATCH, 'built-theme-snippet.txt'), snippets.join('\n'), 'utf8')

    const grepLines = [
      'AttackTheme delegates to Workspace primitives',
      attackTheme.includes('WorkspaceTypeCard') ? 'OK' : 'MISSING',
      attackTheme.includes('WorkspaceRunButton') ? 'OK' : 'MISSING',
      `dist ${cssFileName} size=${cssStat.size}`,
      ...selectors.map((s) => `${s}: ${Boolean(extractRule(distCss, s))}`),
    ]
    writeFileSync(join(SCRATCH, 'source-grep.txt'), grepLines.join('\n'), 'utf8')

    expect(distSummary).toContain('SizeBytes')
    expect(distSummary).toContain(String(cssStat.size))
  })
})