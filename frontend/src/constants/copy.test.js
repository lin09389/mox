import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { NAV_GROUPS, HUB_COPY } from './copy'

const SRC = resolve(dirname(fileURLToPath(import.meta.url)), '..')

function readSrc(relativePath) {
  return readFileSync(resolve(SRC, relativePath), 'utf8')
}

function ruleBody(css, selector) {
  return css.match(new RegExp(`\\${selector}\\s*\\{([^}]+)\\}`))?.[1] || ''
}

describe('copy constants', () => {
  it('NAV_GROUPS has unique paths', () => {
    const paths = NAV_GROUPS.flatMap((g) => g.items.map((i) => i.path))
    expect(new Set(paths).size).toBe(paths.length)
  })

  it('HUB_COPY and workspace polish contracts hold', () => {
    expect(HUB_COPY.attack.title).toBeTruthy()
    expect(HUB_COPY.testing.title).toBeTruthy()
    expect(HUB_COPY.evaluation.title).toBeTruthy()
    expect(HUB_COPY.governance.title).toBeTruthy()

    const workspaceTheme = readSrc('components/workspace/WorkspaceTheme.jsx')
    const attackTheme = readSrc('components/attack/AttackTheme.jsx')
    const hubShell = readSrc('components/HubShell.jsx')
    const wsCss = readSrc('workspace-theme.css')
    const indexCss = readSrc('index.css')

    expect(workspaceTheme).toMatch(/className=\{`ws-run-btn/)
    expect(workspaceTheme).not.toMatch(/ws-run-btn btn-primary/)
    expect(attackTheme).toMatch(/className=\{`attack-run-btn/)
    expect(attackTheme).not.toMatch(/attack-run-btn btn-primary/)
    expect(attackTheme).toContain("type === 'label' ? motion.label : motion.div")
    expect(attackTheme).toContain('data-ws-theme="attack"')
    expect(hubShell).toContain('layoutId={`${layoutId}-ws-tab-indicator`}')

    expect(ruleBody(wsCss, '.ws-type-card:hover')).not.toContain('transform')
    expect(ruleBody(wsCss, '.ws-type-card--active')).not.toContain('transform')
    expect(ruleBody(indexCss, '.attack-type-card:hover')).not.toContain('transform')
    expect(ruleBody(indexCss, '.attack-type-card--active')).not.toContain('transform')
    expect(wsCss).toMatch(/\.ws-run-btn\s*\{[^}]*position:\s*relative/s)

    for (const page of [
      'pages/RedTeamPage.jsx',
      'pages/BenchmarkPage.jsx',
      'pages/OWASPPage.jsx',
      'pages/BiasDetectionPage.jsx',
      'pages/CodeSecurityPage.jsx',
      'pages/SafetyCardPage.jsx',
    ]) {
      expect(readSrc(page)).toContain('WorkspaceRunButton')
    }
    expect(readSrc('pages/RedTeamPage.jsx')).toContain('WorkspaceTypeCard')
    expect(readSrc('pages/BenchmarkPage.jsx')).toContain('WorkspaceTypeCard')
  })
})