import { motion } from 'framer-motion'
import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  ShieldAlert,
  Terminal,
  Wrench,
  XCircle,
} from 'lucide-react'

function statusMeta(entry) {
  if (entry.blocked) {
    return {
      label: '策略拦截',
      tone: 'blocked',
      Icon: Ban,
    }
  }
  if (entry.success) {
    return {
      label: '执行成功',
      tone: 'success',
      Icon: CheckCircle2,
    }
  }
  return {
    label: '执行失败',
    tone: 'failed',
    Icon: XCircle,
  }
}

const toneStyles = {
  blocked: 'bg-rose-500/10 text-rose-500 border-rose-500/25',
  success: 'bg-amber-500/10 text-amber-500 border-amber-500/25',
  failed: 'bg-slate-500/10 text-[var(--text-muted)] border-[var(--border-glass-strong)]',
}

export default function AgentRuntimeCard({ runtime }) {
  if (!runtime) return null

  const {
    tool_calls_detected = 0,
    tool_names = [],
    policy_violations = [],
    any_tool_blocked = false,
    tool_results = [],
  } = runtime

  const blockedCount = tool_results.filter((item) => item.blocked).length
  const allowedCount = tool_results.filter((item) => item.success && !item.blocked).length

  return (
    <motion.article
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className="attack-output-card"
    >
      <div className="attack-output-card-header">
        <div className="attack-output-card-title">
          <Terminal className="h-4 w-4 text-[var(--ws-accent)]" />
          工具调用运行时分析
        </div>
        <span
          className={`badge border px-2.5 py-1 text-xs font-bold ${
            any_tool_blocked
              ? 'bg-rose-500/10 text-rose-500 border-rose-500/25'
              : 'bg-emerald-500/10 text-emerald-500 border-emerald-500/25'
          }`}
        >
          {any_tool_blocked ? (
            <>
              <ShieldAlert className="h-3.5 w-3.5" />
              沙箱已拦截
            </>
          ) : (
            <>
              <CheckCircle2 className="h-3.5 w-3.5" />
              策略放行
            </>
          )}
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-3 mb-4">
        <div className="ws-lab-stat">
          <p className="ws-lab-stat-label">检测调用数</p>
          <p className="ws-lab-stat-value ws-lab-stat-value--electric">{tool_calls_detected}</p>
          <p className="ws-lab-stat-hint">模型输出中解析到的工具调用</p>
        </div>
        <div className="ws-lab-stat">
          <p className="ws-lab-stat-label">拦截 / 放行</p>
          <p className={`ws-lab-stat-value ${blockedCount > 0 ? 'ws-lab-stat-value--danger' : 'ws-lab-stat-value--success'}`}>
            {blockedCount} / {allowedCount}
          </p>
          <p className="ws-lab-stat-hint">策略违规与成功执行统计</p>
        </div>
        <div className="ws-lab-stat">
          <p className="ws-lab-stat-label">策略违规</p>
          <p className={`ws-lab-stat-value ${policy_violations.length ? 'ws-lab-stat-value--warning' : 'ws-lab-stat-value--success'}`}>
            {policy_violations.length}
          </p>
          <p className="ws-lab-stat-hint">触发的运行时安全规则</p>
        </div>
      </div>

      {tool_names.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)] mb-2 flex items-center gap-1.5">
            <Wrench className="h-3.5 w-3.5" />
            解析工具
          </p>
          <div className="flex flex-wrap gap-2">
            {tool_names.map((name) => (
              <span
                key={name}
                className="badge border font-mono tracking-wide bg-cyan-500/10 text-cyan-500 border-cyan-500/20 px-2.5 py-1"
              >
                {name}
              </span>
            ))}
          </div>
        </div>
      )}

      {policy_violations.length > 0 && (
        <div className="mb-4 rounded-xl border border-rose-500/20 bg-rose-500/5 p-4">
          <p className="text-sm font-bold text-rose-500 mb-2 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            策略违规明细
          </p>
          <ul className="space-y-2">
            {policy_violations.map((violation, index) => (
              <li
                key={`${violation}-${index}`}
                className="text-sm font-medium text-[var(--text-muted)] bg-[var(--bg-main)]/50 px-3 py-2 rounded-lg border border-[var(--border-glass)]"
              >
                {violation}
              </li>
            ))}
          </ul>
        </div>
      )}

      {tool_results.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">
            逐工具执行结果
          </p>
          {tool_results.map((entry, index) => {
            const meta = statusMeta(entry)
            const StatusIcon = meta.Icon
            return (
              <div
                key={`${entry.tool}-${index}`}
                className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-4 space-y-2"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-mono text-sm font-bold text-[var(--text-main)]">{entry.tool}</span>
                  <span className={`badge border text-xs font-bold px-2.5 py-1 flex items-center gap-1.5 ${toneStyles[meta.tone]}`}>
                    <StatusIcon className="h-3.5 w-3.5" />
                    {meta.label}
                  </span>
                </div>
                {entry.reason ? (
                  <p className="text-sm text-rose-500/90 font-medium">{entry.reason}</p>
                ) : null}
                {entry.output_preview ? (
                  <pre className="ws-code-block text-xs mt-2">
                    <code>{entry.output_preview}</code>
                  </pre>
                ) : null}
              </div>
            )
          })}
        </div>
      )}
    </motion.article>
  )
}