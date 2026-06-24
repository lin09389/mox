import { Skull, Shield, Target } from 'lucide-react'
import { MetricCard, ProgressMeter } from '../ui/AppFrame'
import { AgentExecutionCard } from '../attack'
import { normalizeRedTeamReport } from '../../utils/reportDetail'

export default function RedTeamReportDetail({ content }) {
  const report = normalizeRedTeamReport(content)
  const successPercent = Math.round((report.summary.successRate || 0) * 100)

  return (
    <div className="space-y-5">
      {report.models && Object.keys(report.models).length > 0 && (
        <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-4">
          <p className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)] mb-3">三模型配置</p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(report.models).map(([role, model]) => (
              <span
                key={role}
                className="badge border font-mono text-xs bg-[var(--bg-glass-strong)] border-[var(--border-glass)] px-2.5 py-1"
              >
                {role}: {model || '-'}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <MetricCard icon={Target} label="场景总数" value={report.summary.total} hint="红队剧本" tone="electric" />
        <MetricCard icon={Skull} label="攻击成功" value={report.summary.successful} hint={`${successPercent}%`} tone="lava" />
        <MetricCard icon={Shield} label="防御成功" value={report.summary.failed} hint={`${100 - successPercent}%`} tone="neon" />
      </div>

      <div className="p-4 rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)]">
        <ProgressMeter value={successPercent} tone={successPercent >= 40 ? 'warning' : 'success'} label="攻击成功率" />
      </div>

      {(report.agentSummary.scenarios_with_tools > 0 || report.agentSummary.policy_bypassed > 0) && (
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="ws-lab-stat">
            <p className="ws-lab-stat-label">Agent 工具场景</p>
            <p className="ws-lab-stat-value ws-lab-stat-value--electric">{report.agentSummary.scenarios_with_tools || 0}</p>
          </div>
          <div className="ws-lab-stat">
            <p className="ws-lab-stat-label">策略绕过</p>
            <p className={`ws-lab-stat-value ${report.agentSummary.policy_bypassed ? 'ws-lab-stat-value--danger' : 'ws-lab-stat-value--success'}`}>
              {report.agentSummary.policy_bypassed || 0}
            </p>
          </div>
        </div>
      )}

      {report.results.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">场景结果</p>
          {report.results.map((item, index) => (
            <div
              key={`${item.technique}-${index}`}
              className={`rounded-xl border p-4 space-y-3 ${item.success ? 'bg-rose-500/5 border-rose-500/20' : 'bg-[var(--bg-glass)] border-[var(--border-glass)]'}`}
            >
              <div className="flex items-center justify-between gap-2">
                <p className={`text-sm font-bold font-mono ${item.success ? 'text-rose-500' : 'text-[var(--text-main)]'}`}>
                  {item.technique}
                </p>
                <span className={`badge border text-[10px] font-bold uppercase ${item.success ? 'bg-rose-500/10 text-rose-500 border-rose-500/20' : 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'}`}>
                  {item.success ? '击穿' : '防御'}
                </span>
              </div>
              <p className="text-xs text-[var(--text-muted)]">{item.scenario}</p>
              <div className="flex flex-wrap gap-2 text-[10px] font-mono text-[var(--text-muted)]">
                <span>尝试 {item.attempts ?? '-'}</span>
                <span>得分 {(item.score ?? 0).toFixed?.(2) ?? item.score}</span>
                <span>置信 {(item.confidence ?? 0).toFixed?.(2) ?? item.confidence}</span>
              </div>
              {item.agent_execution && <AgentExecutionCard execution={item.agent_execution} />}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}