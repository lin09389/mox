import { describe, it, expect, beforeAll } from 'vitest'
import { execSync } from 'node:child_process'
import { readFileSync, writeFileSync, readdirSync, mkdirSync } from 'node:fs'
import { resolve, dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { NAV_GROUPS, HUB_COPY } from './copy'
import { wsTypeCardVariants, wsRunBtnVariants } from '../utils/animations'
import { WorkspaceTypeCard, WorkspaceRunButton } from '../components/workspace/WorkspaceTheme'

const FRONTEND = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..')
const SCRATCH =
  process.env.GOAL_SCRATCH ||
  'C:\\Users\\JHJ\\AppData\\Local\\Temp\\grok-goal-8568e8927c42\\implementer'

function extractRule(css, selector) {
  const candidates = [
    selector,
    selector.replace(/::/g, ':'),
    selector.replace(/="([^"]+)"/, '=$1'),
    selector.replace(/::/g, ':').replace(/="([^"]+)"/, '=$1'),
  ]
  for (const sel of [...new Set(candidates)]) {
    const escaped = sel.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const match = css.match(new RegExp(`${escaped}\\s*\\{([^}]+)\\}`))
    if (match) return `${sel}{${match[1].trim()}}`
  }
  return null
}

function ruleHasNoTransform(rule) {
  return rule ? !/\btransform\s*:/.test(rule) : true
}

describe('copy constants', () => {
  it('navigation paths are unique and hub copy is defined', () => {
    const paths = NAV_GROUPS.flatMap((g) => g.items.map((i) => i.path))
    expect(new Set(paths).size).toBe(paths.length)
    expect(HUB_COPY.attack.title).toBeTruthy()
    expect(HUB_COPY.testing.title).toBeTruthy()
    expect(HUB_COPY.evaluation.title).toBeTruthy()
    expect(HUB_COPY.governance.title).toBeTruthy()
  })
})

describe('built CSS polish verification', () => {
  let distCss = ''
  let cssFileName = ''

  beforeAll(() => {
    execSync('npm run build', { cwd: FRONTEND, stdio: 'pipe', encoding: 'utf8' })
    cssFileName = readdirSync(join(FRONTEND, 'dist', 'assets')).find((f) => f.endsWith('.css'))
    if (!cssFileName) throw new Error('No CSS asset in dist/')
    distCss = readFileSync(join(FRONTEND, 'dist', 'assets', cssFileName), 'utf8')
  }, 120000)

  it('dist CSS, motion variants, DOM markup, and evidence artifacts', () => {
    mkdirSync(SCRATCH, { recursive: true })

    const distSummary = execSync(
      `powershell -NoProfile -Command "Get-ChildItem '${join(FRONTEND, 'dist', 'index.html')}', '${join(FRONTEND, 'dist', 'assets', '*.css')}' | Select-Object Name, @{N='SizeBytes';E={$_.Length}}, FullName | Format-Table -AutoSize | Out-String -Width 240"`,
      { cwd: FRONTEND, encoding: 'utf8' }
    )
    writeFileSync(join(SCRATCH, 'dist-summary.txt'), distSummary, 'utf8')
    expect(distSummary).toMatch(/SizeBytes/)
    expect(distSummary).toMatch(/index\.html/)
    expect(distSummary).toMatch(/\.css/)

    const baseSelectors = [
      '.ws-run-btn',
      '.ws-type-card',
      '.ws-type-card:hover',
      '.ws-hub-hero',
      '.ws-hub-tab-indicator',
      '[data-ws-theme="attack"]',
    ]
    const pseudoSelectors = ['.ws-run-btn::before', '.ws-hub-hero::after', '.ws-type-card::before']

    const snippets = ['=== EXTRACTED DIST CSS RULE BODIES ===']
    for (const sel of baseSelectors) {
      const rule = extractRule(distCss, sel)
      expect(rule, `missing built rule for ${sel}`).toBeTruthy()
      expect(rule.length, `empty body for ${sel}`).toBeGreaterThan(10)
      snippets.push('')
      snippets.push(rule)
    }

    snippets.push('')
    snippets.push('=== PSEUDO-ELEMENT SPECULAR LAYERS ===')
    for (const sel of pseudoSelectors) {
      const rule = extractRule(distCss, sel)
      expect(rule, `missing pseudo rule for ${sel}`).toBeTruthy()
      expect(rule.length, `empty pseudo body for ${sel}`).toBeGreaterThan(10)
      snippets.push('')
      snippets.push(rule)
    }

    const wsRunRule = extractRule(distCss, '.ws-run-btn')
    const runBefore = extractRule(distCss, '.ws-run-btn::before')
    expect(wsRunRule).toContain('var(--ws-accent)')
    expect(runBefore).toMatch(/linear-gradient|opacity|inset/)

    const btnPrimaryIdx = distCss.indexOf('.btn-primary')
    const wsRunIdx = distCss.indexOf('.ws-run-btn')
    expect(btnPrimaryIdx).toBeGreaterThan(-1)
    expect(wsRunIdx).toBeGreaterThan(btnPrimaryIdx)

    const typeHover = extractRule(distCss, '.ws-type-card:hover')
    const runHover = extractRule(distCss, '.ws-run-btn:hover:not(:disabled)')
    expect(ruleHasNoTransform(typeHover)).toBe(true)
    expect(ruleHasNoTransform(runHover)).toBe(true)

    expect(distCss).not.toContain('.attack-type-card:hover')
    expect(distCss).not.toContain('.attack-run-btn')

    expect(wsTypeCardVariants.hover.transition.type).toBe('spring')
    expect(wsRunBtnVariants.hover.transition.type).toBe('spring')

    const cardMarkup = renderToStaticMarkup(
      createElement(WorkspaceTypeCard, {
        title: 'Prompt Injection',
        description: 'Direct override',
      })
    )
    const btnMarkup = renderToStaticMarkup(
      createElement(WorkspaceRunButton, null, '执行攻击')
    )
    expect(cardMarkup).toContain('ws-type-card')
    expect(cardMarkup).toContain('type-card--motion')
    expect(btnMarkup).toContain('ws-run-btn')

    const wsThemeSrc = readFileSync(join(FRONTEND, 'src', 'components', 'workspace', 'WorkspaceTheme.jsx'), 'utf8')
    expect(wsThemeSrc).toContain('whileHover')
    expect(wsThemeSrc).toContain('wsRunBtnVariants')
    expect(wsThemeSrc).toContain('wsTypeCardVariants')
    expect(wsThemeSrc).toContain('useReducedMotion')

    const attackTheme = readFileSync(join(FRONTEND, 'src', 'components', 'attack', 'AttackTheme.jsx'), 'utf8')
    expect(attackTheme).toContain('WorkspaceTypeCard')
    expect(attackTheme).toContain('WorkspaceRunButton')

    snippets.push('')
    snippets.push('=== CASCADE CHECK ===')
    snippets.push(`btn-primary offset: ${btnPrimaryIdx}`)
    snippets.push(`ws-run-btn offset: ${wsRunIdx}`)
    snippets.push(`ws-run-btn uses --ws-accent: ${wsRunRule.includes('var(--ws-accent)')}`)
    snippets.push(`ws-run-btn:hover has no CSS transform: ${ruleHasNoTransform(runHover)}`)
    snippets.push(`motion spring variants: typeCard=${wsTypeCardVariants.hover.transition.type} runBtn=${wsRunBtnVariants.hover.transition.type}`)

    writeFileSync(join(SCRATCH, 'built-theme-snippet.txt'), snippets.join('\n'), 'utf8')

    const grepLines = [
      'AttackTheme delegates to Workspace primitives',
      attackTheme.includes('WorkspaceTypeCard') ? 'OK' : 'MISSING',
      attackTheme.includes('WorkspaceRunButton') ? 'OK' : 'MISSING',
      `dist ${cssFileName}`,
      ...baseSelectors.map((s) => `${s}: ${Boolean(extractRule(distCss, s))}`),
      ...pseudoSelectors.map((s) => `${s}: ${Boolean(extractRule(distCss, s))}`),
      `cardMarkup ws-type-card: ${cardMarkup.includes('ws-type-card')}`,
      `btnMarkup ws-run-btn: ${btnMarkup.includes('ws-run-btn')}`,
      `spring hover: typeCard=${wsTypeCardVariants.hover.transition.type} runBtn=${wsRunBtnVariants.hover.transition.type}`,
    ]
    writeFileSync(join(SCRATCH, 'source-grep.txt'), grepLines.join('\n'), 'utf8')
  })
})