import { describe, it, expect } from 'vitest'
import { NAV_GROUPS, HUB_COPY } from './copy'

describe('copy constants', () => {
  it('NAV_GROUPS has unique paths', () => {
    const paths = NAV_GROUPS.flatMap((g) => g.items.map((i) => i.path))
    expect(new Set(paths).size).toBe(paths.length)
  })

  it('HUB_COPY defines all hub sections', () => {
    expect(HUB_COPY.attack.title).toBeTruthy()
    expect(HUB_COPY.testing.title).toBeTruthy()
    expect(HUB_COPY.evaluation.title).toBeTruthy()
    expect(HUB_COPY.governance.title).toBeTruthy()
  })
})