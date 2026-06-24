import { describe, expect, it } from 'vitest'
import {
  detectReportViewType,
  normalizeAttackLoopReport,
  normalizeRedTeamReport,
  parseReportContent,
} from './reportDetail'

describe('reportDetail', () => {
  it('parses JSON string content', () => {
    const parsed = parseReportContent('{"results":[]}')
    expect(parsed).toEqual({ results: [] })
  })

  it('detects redteam structured view', () => {
    const view = detectReportViewType('redteam', {
      summary: { total_scenarios: 1 },
      results: [{ technique: 'tool_chaining', success: true }],
    })
    expect(view).toBe('redteam')
  })

  it('detects attack loop structured view', () => {
    const view = detectReportViewType('evaluation', {
      total_tests: 10,
      agent_execution_summary: { total_with_tools: 2 },
      agent_execution_runs: [],
    })
    expect(view).toBe('attack_loop')
  })

  it('normalizes redteam agent execution rows', () => {
    const normalized = normalizeRedTeamReport({
      summary: { total_scenarios: 1, successful: 1, success_rate: 1 },
      models: { target: 'llama3' },
      agent_summary: { scenarios_with_tools: 1, policy_bypassed: 0 },
      results: [
        {
          technique: 'tool_chaining',
          success: true,
          agent_execution: { agent_mode: 'langchain', tool_calls: ['read_file'] },
        },
      ],
    })

    expect(normalized.summary.total).toBe(1)
    expect(normalized.results[0].agent_execution.agent_mode).toBe('langchain')
  })

  it('normalizes attack loop agent summary', () => {
    const normalized = normalizeAttackLoopReport({
      total_tests: 5,
      successful_tests: 2,
      agent_execution_summary: { total_with_tools: 3, langchain_runs: 2 },
      agent_execution_runs: [{ test_id: 't1', agent_mode: 'langchain' }],
    })

    expect(normalized.agentSummary.langchain_runs).toBe(2)
    expect(normalized.agentRuns).toHaveLength(1)
  })
})