import { AlertTriangle, Terminal } from 'lucide-react'
import { normalizeAutoRedteamReport } from '../../utils/reportDetail'

const LOG_STATE_STYLES = {
  thinking: 'text-purple-500 bg-purple-500/10 border-purple-500/20',
  acting: 'text-cyan-500 bg-cyan-500/10 border-cyan-500/20',
  observing: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20',
  error: 'text-rose-500 bg-rose-500/10 border-rose-500/20',
}

export default function AutoRedTeamReportDetail({ content }) {
  const report = normalizeAutoRedteamReport(content)

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2 text-xs font-mono">
        {report.taskId && (
          <span className="badge border bg-[var(--bg-glass-strong)] border-[var(--border-glass)] px-2.5 py-1">
            task: {report.taskId}
          </span>
        )}
        {report.status && (
          <span className="badge border bg-cyan-500/10 text-cyan-500 border-cyan-500/20 px-2.5 py-1">
            {report.status}
          </span>
        )}
        {report.currentStep != null && (
          <span className="badge border bg-[var(--bg-glass-strong)] border-[var(--border-glass)] px-2.5 py-1">
            step {report.currentStep}
          </span>
        )}
      </div>

      {report.vulnerabilities.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)] flex items-center gap-1.5">
            <AlertTriangle className="h-3.5 w-3.5 text-rose-500" />
            发现项
          </p>
          {report.vulnerabilities.map((item, index) => (
            <div key={`${item.attack_name}-${index}`} className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-3">
              <p className="text-sm font-bold text-rose-500">{item.attack_name || item.name || '未知攻击'}</p>
              {item.severity != null && (
                <p className="text-xs font-mono text-[var(--text-muted)] mt-1">严重度 {item.severity}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {report.logs.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)] flex items-center gap-1.5">
            <Terminal className="h-3.5 w-3.5" />
            ReAct 推理轨迹
          </p>
          <div className="max-h-[280px] overflow-auto space-y-2 pr-1">
            {report.logs.map((log, index) => (
              <div key={`${log.step_num}-${index}`} className="rounded-lg border border-[var(--border-glass)] bg-[var(--bg-glass)] p-3 text-xs">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-[var(--text-muted)]">#{log.step_num ?? index + 1}</span>
                  <span className={`badge border text-[10px] font-bold uppercase ${LOG_STATE_STYLES[log.state] || 'bg-[var(--bg-glass-strong)] border-[var(--border-glass)]'}`}>
                    {log.state || 'log'}
                  </span>
                </div>
                {log.thought && <p className="text-[var(--text-main)] leading-relaxed">{log.thought}</p>}
                {log.action_name && (
                  <p className="text-cyan-500 font-mono mt-1">action: {log.action_name}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}