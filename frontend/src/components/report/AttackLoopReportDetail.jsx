import { Bot, Target, Zap } from 'lucide-react'
import { MetricCard } from '../ui/AppFrame'
import { normalizeAttackLoopReport } from '../../utils/reportDetail'

export default function AttackLoopReportDetail({ content }) {
  const report = normalizeAttackLoopReport(content)
  const successRate = report.totalTests
    ? Math.round((report.successfulTests / report.totalTests) * 100)
    : 0

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-3">
        <MetricCard icon={Target} label="测试总数" value={report.totalTests} hint="矩阵跑批" tone="electric" />
        <MetricCard icon={Zap} label="攻击成功" value={report.successfulTests} hint={`${successRate}%`} tone="lava" />
        <MetricCard icon={Bot} label="平均得分" value={report.avgScore.toFixed?.(2) ?? report.avgScore} hint="success_score" tone="neon" />
      </div>

      {report.agentSummary.total_with_tools > 0 && (
        <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4">
          <p className="text-xs font-bold uppercase tracking-widest text-cyan-500 mb-3">Agent 执行摘要</p>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="ws-lab-stat">
              <p className="ws-lab-stat-label">含工具场景</p>
              <p className="ws-lab-stat-value ws-lab-stat-value--electric">{report.agentSummary.total_with_tools}</p>
            </div>
            <div className="ws-lab-stat">
              <p className="ws-lab-stat-label">策略绕过</p>
              <p className="ws-lab-stat-value ws-lab-stat-value--danger">{report.agentSummary.policy_bypassed || 0}</p>
            </div>
            <div className="ws-lab-stat">
              <p className="ws-lab-stat-label">LangChain 运行</p>
              <p className="ws-lab-stat-value">{report.agentSummary.langchain_runs || 0}</p>
            </div>
          </div>
        </div>
      )}

      {report.topDangerous.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">高危攻击向量</p>
          {report.topDangerous.map((item) => (
            <div key={item.type} className="flex items-center justify-between rounded-lg border border-[var(--border-glass)] bg-[var(--bg-glass)] px-3 py-2 text-xs">
              <span className="font-bold text-[var(--text-main)]">{item.name || item.type}</span>
              <span className="font-mono text-rose-500">{Math.round(item.success_rate)}%</span>
            </div>
          ))}
        </div>
      )}

      {report.agentRuns.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">Agent 执行记录</p>
          {report.agentRuns.slice(0, 10).map((run) => (
            <div key={run.test_id} className="rounded-lg border border-[var(--border-glass)] bg-[var(--bg-glass)] px-3 py-2 text-xs space-y-1">
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono font-bold text-[var(--text-main)]">{run.attack_name || run.attack_type}</span>
                <span className="badge border font-mono text-[10px] bg-cyan-500/10 text-cyan-500 border-cyan-500/20">
                  {run.agent_mode || '-'}
                </span>
              </div>
              <p className="text-[var(--text-muted)]">{run.model} · {(run.tool_calls || []).join(', ') || '无工具调用'}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}