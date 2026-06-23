const DANGEROUS_TOOLS = new Set([
  'write_file',
  'execute_code',
  'database_query',
  'send_email',
  'shell_command',
  'execute_sql',
])

export function buildDemoAgentRuntime(type, tools, success) {
  const dangerous = tools.filter((name) => DANGEROUS_TOOLS.has(name))
  const violations = success
    ? dangerous.map((tool) => `Sandbox bypass: ${tool} executed without policy check`)
    : dangerous.map((tool) => `Tool '${tool}' blocked by agent runtime policy`)

  const toolResults = tools.map((tool) => {
    const isDanger = DANGEROUS_TOOLS.has(tool)
    const blocked = !success && isDanger
    return {
      tool,
      success: success && isDanger,
      blocked,
      reason: blocked ? `Tool '${tool}' not permitted in sandbox` : '',
      output_preview:
        success && isDanger ? `[simulated] ${tool} output for ${type}` : '',
    }
  })

  return {
    tool_calls_detected: tools.length,
    tool_names: tools,
    policy_violations: violations,
    any_tool_blocked: !success && dangerous.length > 0,
    tool_results: toolResults,
  }
}

export function buildDemoAgentResult(type, tools) {
  const risk = 0.45 + Math.random() * 0.45
  const success = risk > 0.65
  const riskyTools = success ? tools.filter((name) => DANGEROUS_TOOLS.has(name)) : []

  return {
    _demo_mode: true,
    attack_type: type,
    result: success ? 'success' : 'failure',
    success,
    success_score: Number(risk.toFixed(2)),
    risk_score: Number(risk.toFixed(2)),
    risky_tools: riskyTools,
    summary: success
      ? '检测到工具链可被利用路径。Agent 在复杂指令下暴露了高危执行权限。'
      : '当前策略已拦截主要攻击链路，Agent 成功遵守了沙箱约束。',
    agent_runtime: buildDemoAgentRuntime(type, tools, success),
  }
}

export function normalizeAgentAttackResult(raw) {
  if (!raw) return null

  const scoreValue = raw.success_score ?? raw.risk_score ?? 0
  const score =
    typeof scoreValue === 'number' ? scoreValue : Number.parseFloat(scoreValue) || 0
  const apiSuccess = raw.result === 'success'
  const isSuccess = apiSuccess || raw.success === true

  const runtimeRisky =
    raw.agent_runtime?.tool_results
      ?.filter((item) => item.blocked || (item.success && !item.blocked))
      .map((item) => item.tool) ?? []

  const riskyTools = raw.risky_tools?.length ? raw.risky_tools : runtimeRisky

  const defaultSummary = isSuccess
    ? '检测到 Agent 在工具调用链路中存在可被利用的路径。'
    : '运行时策略成功拦截了可疑工具调用，沙箱约束有效。'

  return {
    ...raw,
    success: isSuccess,
    risk_score: score,
    success_score: score,
    risky_tools: riskyTools,
    summary: raw.summary || defaultSummary,
    model_response: raw.model_response ?? '',
    agent_runtime: raw.agent_runtime ?? null,
  }
}