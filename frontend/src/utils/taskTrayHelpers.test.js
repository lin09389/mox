import { describe, expect, it } from 'vitest'
import { getTaskHref, normalizeRemoteTask } from './taskTrayHelpers'

describe('taskTrayHelpers', () => {
  it('getTaskHref links completed tasks with report_id to governance highlight', () => {
    expect(
      getTaskHref({ source: 'attack_loop', status: 'completed', report_id: 88 })
    ).toBe('/governance?tab=reports&highlight=88')
  })

  it('getTaskHref keeps source route for running tasks even with report_id', () => {
    expect(
      getTaskHref({ source: 'auto_redteam', status: 'running', report_id: 88 })
    ).toBe('/testing?tab=auto-redteam')
  })

  it('normalizeRemoteTask passes report_id and builds governance href when completed', () => {
    const task = normalizeRemoteTask({
      id: 'loop-1',
      source: 'attack_loop',
      status: 'completed',
      report_id: 42,
      progress: 100,
    })
    expect(task.report_id).toBe(42)
    expect(task.href).toBe('/governance?tab=reports&highlight=42')
  })
})