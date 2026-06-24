import { motion } from 'framer-motion'
import { Bot, ShieldAlert, Wrench } from 'lucide-react'

export default function AgentExecutionCard({ execution }) {
  if (!execution) return null

  const {
    agent_mode,
    tool_calls = [],
    policy_bypassed,
    policy_violations = [],
    langchain_steps,
    winning_attacker,
    composite,
  } = execution

  return (
    <motion.article
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className="attack-output-card"
    >
      <div className="attack-output-card-header">
        <div className="attack-output-card-title">
          <Bot className="h-4 w-4 text-[var(--ws-accent)]" />
          Agent 执行轨迹
        </div>
        <span className="badge border px-2.5 py-1 text-xs font-bold bg-cyan-500/10 text-cyan-500 border-cyan-500/20">
          {agent_mode || 'prompt'}
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-3 mb-4">
        <div className="ws-lab-stat">
          <p className="ws-lab-stat-label">工具调用</p>
          <p className="ws-lab-stat-value ws-lab-stat-value--electric">{tool_calls.length}</p>
          <p className="ws-lab-stat-hint">LangChain 真实执行次数</p>
        </div>
        <div className="ws-lab-stat">
          <p className="ws-lab-stat-label">策略绕过</p>
          <p className={`ws-lab-stat-value ${policy_bypassed ? 'ws-lab-stat-value--danger' : 'ws-lab-stat-value--success'}`}>
            {policy_bypassed ? '是' : '否'}
          </p>
          <p className="ws-lab-stat-hint">是否突破运行时策略</p>
        </div>
        <div className="ws-lab-stat">
          <p className="ws-lab-stat-label">循环步数</p>
          <p className="ws-lab-stat-value">{langchain_steps ?? '-'}</p>
          <p className="ws-lab-stat-hint">ReAct 多步深度</p>
        </div>
      </div>

      {tool_calls.length > 0 && (
        <div className="mb-4">
          <p className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)] mb-2 flex items-center gap-1.5">
            <Wrench className="h-3.5 w-3.5" />
            工具链
          </p>
          <div className="flex flex-wrap gap-2">
            {tool_calls.map((name) => (
              <span
                key={name}
                className="badge border font-mono tracking-wide bg-rose-500/10 text-rose-500 border-rose-500/20 px-2.5 py-1"
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
            <ShieldAlert className="h-4 w-4" />
            策略违规
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

      {(composite || winning_attacker) && (
        <p className="text-xs font-medium text-[var(--text-muted)]">
          {composite ? '组合攻击' : '子攻击'}
          {winning_attacker ? ` · ${winning_attacker}` : ''}
        </p>
      )}
    </motion.article>
  )
}