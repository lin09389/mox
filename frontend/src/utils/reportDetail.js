/** 将报告 content 规范化为可渲染对象 */

export function parseReportContent(raw) {
  if (!raw) return null
  if (typeof raw === 'string') {
    try {
      return JSON.parse(raw)
    } catch {
      return { raw }
    }
  }
  return raw
}

export function detectReportViewType(reportType, content) {
  if (!content || typeof content !== 'object' || content.raw) {
    return 'raw'
  }
  if (reportType === 'redteam' && Array.isArray(content.results)) {
    return 'redteam'
  }
  if (reportType === 'auto_redteam' && (content.logs || content.vulnerabilities)) {
    return 'auto_redteam'
  }
  if (content.agent_execution_summary || Array.isArray(content.agent_execution_runs)) {
    return 'attack_loop'
  }
  if (reportType === 'owasp' && Array.isArray(content.results)) {
    return 'owasp'
  }
  return 'raw'
}

export function normalizeRedTeamReport(content) {
  const summary = content?.summary || {}
  return {
    summary: {
      total: summary.total_scenarios ?? content?.results?.length ?? 0,
      successful: summary.successful ?? 0,
      failed: summary.failed ?? 0,
      successRate: summary.success_rate ?? 0,
      avgScore: summary.avg_score ?? 0,
      avgConfidence: summary.avg_confidence ?? 0,
    },
    models: content?.models || {},
    agentSummary: content?.agent_summary || {},
    byTechnique: content?.by_technique || {},
    byDifficulty: content?.by_difficulty || {},
    results: Array.isArray(content?.results) ? content.results : [],
  }
}

export function normalizeAttackLoopReport(content) {
  return {
    totalTests: content?.total_tests ?? 0,
    successfulTests: content?.successful_tests ?? 0,
    failedTests: content?.failed_tests ?? 0,
    avgScore: content?.avg_score ?? 0,
    agentSummary: content?.agent_execution_summary || {},
    agentRuns: Array.isArray(content?.agent_execution_runs) ? content.agent_execution_runs : [],
    topDangerous: Array.isArray(content?.top_dangerous_attacks) ? content.top_dangerous_attacks : [],
    attackStats: content?.attack_stats || {},
    modelStats: content?.model_stats || {},
  }
}

export function normalizeAutoRedteamReport(content) {
  return {
    taskId: content?.task_id,
    targetModel: content?.target_model,
    status: content?.status,
    currentStep: content?.current_step,
    logs: Array.isArray(content?.logs) ? content.logs : [],
    vulnerabilities: Array.isArray(content?.vulnerabilities) ? content.vulnerabilities : [],
  }
}

export function normalizeOwaspReport(content) {
  return {
    results: Array.isArray(content?.results) ? content.results : [],
  }
}