import { describe, expect, it, beforeEach, vi } from 'vitest'
import {
  getDemoReports,
  getReportDetailContent,
  mergeWithDemoReports,
  saveDemoReport,
  removeDemoReport,
} from './demoReports'

describe('demoReports', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', {
      store: {},
      getItem(key) {
        return this.store[key] ?? null
      },
      setItem(key, value) {
        this.store[key] = value
      },
      removeItem(key) {
        delete this.store[key]
      },
    })
  })

  it('saveDemoReport persists and mergeWithDemoReports prepends demo items', () => {
    const saved = saveDemoReport({
      id: 9001,
      report_name: '演示报告',
      report_type: 'auto_redteam',
      model_name: 'llama3',
      attack_success_rate: 0.5,
      defense_success_rate: 0.5,
    })
    expect(saved._demo_mode).toBe(true)
    expect(getDemoReports()).toHaveLength(1)

    const merged = mergeWithDemoReports([{ id: 1, report_name: '远程报告' }])
    expect(merged[0].id).toBe(9001)
    expect(merged[1].id).toBe(1)
  })

  it('getReportDetailContent parses stored JSON content', () => {
    const saved = saveDemoReport({
      id: 77,
      report_name: '演示',
      report_type: 'auto_redteam',
      model_name: 'llama3',
      content: { demo: true, steps: 3 },
    })
    expect(getReportDetailContent(saved)).toEqual({ demo: true, steps: 3 })
  })

  it('removeDemoReport deletes stored entry', () => {
    saveDemoReport({ id: 42, report_name: 'x', report_type: 'auto_redteam', model_name: 'm' })
    removeDemoReport(42)
    expect(getDemoReports()).toHaveLength(0)
  })
})