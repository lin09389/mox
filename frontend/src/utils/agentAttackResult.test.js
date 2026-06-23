import { describe, expect, it } from 'vitest'
import {
  buildDemoAgentResult,
  buildDemoAgentRuntime,
  normalizeAgentAttackResult,
} from './agentAttackResult'

describe('agentAttackResult', () => {
  it('normalizes API payload with agent_runtime', () => {
    const normalized = normalizeAgentAttackResult({
      result: 'failure',
      success_score: 0.22,
      model_response: '{"name":"read_file"}',
      agent_runtime: {
        tool_calls_detected: 1,
        tool_names: ['read_file'],
        policy_violations: ['Sensitive path blocked: /etc/passwd'],
        any_tool_blocked: true,
        tool_results: [
          {
            tool: 'read_file',
            success: false,
            blocked: true,
            reason: 'Sensitive path blocked: /etc/passwd',
            output_preview: '',
          },
        ],
      },
    })

    expect(normalized.success).toBe(false)
    expect(normalized.risk_score).toBe(0.22)
    expect(normalized.agent_runtime.tool_calls_detected).toBe(1)
    expect(normalized.risky_tools).toEqual(['read_file'])
  })

  it('builds demo runtime with blocked dangerous tools when attack fails', () => {
    const runtime = buildDemoAgentRuntime('tool_chaining', ['write_file', 'read_file'], false)

    expect(runtime.any_tool_blocked).toBe(true)
    expect(runtime.tool_results.find((item) => item.tool === 'write_file')?.blocked).toBe(true)
    expect(runtime.tool_results.find((item) => item.tool === 'read_file')?.blocked).toBe(false)
  })

  it('demo result includes agent_runtime', () => {
    const demo = buildDemoAgentResult('tool_chaining', ['execute_code'])
    expect(demo.agent_runtime).toBeTruthy()
    expect(demo.agent_runtime.tool_names).toEqual(['execute_code'])
  })
})