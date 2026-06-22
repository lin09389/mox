import { describe, expect, it, beforeEach, vi } from 'vitest'
import {
  getDemoReports,
  getReportDetailContent,
  mergeWithDemoReports,
  saveDemoReport,
} from '../utils/demoReports'

const DEMO_LOGS = [
  { step_num: 1, state: 'thinking', thought: '分析目标模型防护边界。' },
  { step_num: 2, state: 'acting', action_name: 'jailbreak' },
]

function simulateAutoRedteamDemo(targetModel = 'llama3') {
  const reportId = Date.now()
  const taskId = `demo-${reportId}`
  const saved = saveDemoReport({
    id: reportId,
    report_name: `自动红队演示报告 (${targetModel})`,
    report_type: 'auto_redteam',
    model_name: targetModel,
    attack_success_rate: 0.82,
    defense_success_rate: 0.18,
    format: 'json',
    content: {
      task_id: taskId,
      target_model: targetModel,
      status: 'completed',
      demo: true,
      logs: DEMO_LOGS,
      vulnerabilities: [{ attack_name: '演示越狱突破', severity: 0.82 }],
    },
  })
  return { saved, taskId, reportId }
}

function parseGovernanceHighlight(link) {
  const url = new URL(link, 'http://localhost')
  const raw = url.searchParams.get('highlight')
  if (!raw) return null
  const parsed = Number.parseInt(raw, 10)
  return Number.isFinite(parsed) ? parsed : null
}

describe('demo redteam → governance report highlight flow', () => {
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

  it('simulates auto redteam demo save and builds governance highlight link', async () => {
    const { buildGovernanceReportLink } = await import('../api/index.js')
    const { saved, reportId } = simulateAutoRedteamDemo('gemma3:4b')

    expect(saved._demo_mode).toBe(true)
    expect(getDemoReports()).toHaveLength(1)

    const link = buildGovernanceReportLink(reportId)
    expect(link).toBe(`/governance?tab=reports&highlight=${reportId}`)

    const highlightId = parseGovernanceHighlight(link)
    expect(highlightId).toBe(reportId)

    const reports = mergeWithDemoReports([])
    const match = reports.find((item) => item.id === highlightId)
    expect(match).toBeTruthy()
    expect(match.report_type).toBe('auto_redteam')
    expect(match.model_name).toBe('gemma3:4b')
  })

  it('resolves highlighted demo report content for preview', () => {
    const { saved, reportId } = simulateAutoRedteamDemo()
    const link = `/governance?tab=reports&highlight=${reportId}`
    const highlightId = parseGovernanceHighlight(link)

    const reports = mergeWithDemoReports([])
    const selected = reports.find((item) => item.id === highlightId)
    const detail = getReportDetailContent(selected)

    expect(selected?.id).toBe(saved.id)
    expect(detail.demo).toBe(true)
    expect(detail.status).toBe('completed')
    expect(detail.logs).toHaveLength(2)
    expect(detail.vulnerabilities[0].attack_name).toBe('演示越狱突破')
  })
})