import { AlertTriangle, ArrowRight, Signal, Sparkles } from 'lucide-react'
import { motion } from 'framer-motion'
import { headerVariants, hoverCardVariants, tapEffect } from '../../utils/animations'

export function PageHeader({
  eyebrow = 'CONTROL CENTER',
  title,
  description,
  actions,
  badge,
}) {
  return (
    <motion.header
      initial="hidden"
      animate="show"
      variants={headerVariants}
      className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-4"
    >
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--bg-glass)] border border-[var(--border-glass)] text-xs font-bold text-[var(--accent-primary)] uppercase tracking-widest mb-1">
          {eyebrow}
        </div>
        <h1 className="text-3xl md:text-4xl font-bold font-display text-[var(--text-main)] tracking-tight">
          {title}
        </h1>
        {description ? <p className="text-[var(--text-muted)] mt-2 font-medium max-w-xl">{description}</p> : null}
      </div>
      {(badge || actions) && (
        <motion.div
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.12, duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
          className="flex flex-wrap items-center justify-start gap-3 md:justify-end"
        >
          {badge}
          {actions}
        </motion.div>
      )}
    </motion.header>
  )
}

export function StatusPill({ online, onlineLabel = 'API 已连接', offlineLabel = '演示模式' }) {
  return (
    <div
      className={`badge ${
        online ? 'badge-success' : 'badge-warning'
      } px-3 py-1.5 text-[12px]`}
    >
      <span className={`status-dot ${online ? 'status-dot-online' : 'status-dot-demo'}`} />
      {online ? onlineLabel : offlineLabel}
    </div>
  )
}

export function HeroStat({ label, value, hint, tone = 'neutral' }) {
  const tones = {
    neutral: 'bg-[var(--bg-glass-strong)] text-[var(--text-main)] border-[var(--border-glass-strong)]',
    electric: 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-500/20',
    success: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
    danger: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20',
    warning: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20',
  }

  return (
    <motion.div 
      variants={hoverCardVariants}
      initial="rest"
      whileHover="hover"
      className={`rounded-2xl border px-5 py-5 ${tones[tone]} backdrop-blur-md`}
    >
      <p className="text-[10px] font-bold uppercase tracking-[0.2em] opacity-80 mb-2">{label}</p>
      <p className="font-display text-3xl font-bold tracking-tight">{value}</p>
      {hint ? <p className="mt-2 text-xs font-medium opacity-80">{hint}</p> : null}
    </motion.div>
  )
}

export function MetricCard({ icon: Icon, label, value, hint, trend, trendLabel, tone = 'electric' }) {
  const styles = {
    electric: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20 shadow-[0_0_15px_rgba(6,182,212,0.15)]',
    lava: 'bg-rose-500/10 text-rose-500 border-rose-500/20 shadow-[0_0_15px_rgba(244,63,94,0.15)]',
    neon: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.15)]',
    amber: 'bg-amber-500/10 text-amber-500 border-amber-500/20 shadow-[0_0_15px_rgba(245,158,11,0.15)]',
    graphite: 'bg-[var(--bg-glass-strong)] text-[var(--text-muted)] border-[var(--border-glass-strong)]',
  }

  return (
    <motion.section 
      variants={hoverCardVariants}
      initial="rest"
      whileHover="hover"
      className="card card-hover flex flex-col justify-between h-[160px]"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.1em] text-[var(--text-muted)]">{label}</p>
          <p className="font-mono text-3xl font-bold tracking-tight text-[var(--text-main)] mt-2">{value}</p>
        </div>
        <div className={`rounded-xl border p-3 ${styles[tone]}`}>
          {Icon && <Icon className="h-6 w-6" />}
        </div>
      </div>
      {hint ? (
        <div className="mt-auto pt-3 border-t border-[var(--border-glass)]">
          <p className="text-xs font-medium text-[var(--text-muted)]">{hint}</p>
        </div>
      ) : null}
    </motion.section>
  )
}

export function PanelHeader({ title, description, action }) {
  return (
    <div className="mb-5 flex items-start justify-between gap-4">
      <div className="space-y-1">
        <h2 className="text-lg font-bold font-display text-[var(--text-main)]">{title}</h2>
        {description ? <p className="text-sm font-medium text-[var(--text-muted)]">{description}</p> : null}
      </div>
      {action}
    </div>
  )
}

export function EmptyState({
  icon: Icon = Sparkles,
  title,
  description,
  action,
  tone = 'neutral',
}) {
  const tones = {
    neutral: 'bg-[var(--bg-glass-strong)] text-[var(--text-muted)] border-[var(--border-glass-strong)]',
    electric: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20',
    warning: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
    danger: 'bg-rose-500/10 text-rose-500 border-rose-500/20',
    success: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
  }

  return (
    <div className="flex min-h-[240px] flex-col items-center justify-center rounded-2xl border border-dashed border-[var(--border-glass-strong)] bg-[var(--bg-glass)] px-6 py-10 text-center">
      <div className={`mb-4 rounded-2xl p-4 border ${tones[tone]}`}>
        {Icon && <Icon className="h-8 w-8" />}
      </div>
      <h3 className="text-lg font-bold text-[var(--text-main)]">{title}</h3>
      {description ? <p className="mt-2 max-w-md text-sm font-medium text-[var(--text-muted)]">{description}</p> : null}
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  )
}

export function ProgressMeter({ value = 0, tone = 'electric', label }) {
  const tones = {
    electric: 'from-cyan-400 to-cyan-600',
    danger: 'from-rose-400 to-rose-600',
    success: 'from-emerald-400 to-emerald-600',
    warning: 'from-amber-400 to-amber-600',
  }

  return (
    <div className="space-y-2">
      {label ? (
        <div className="flex items-center justify-between text-xs font-bold text-[var(--text-muted)]">
          <span>{label}</span>
          <span className="font-mono text-[var(--text-main)]">{value}%</span>
        </div>
      ) : null}
      <div className="h-2 overflow-hidden rounded-full bg-[var(--bg-glass-strong)] border border-[var(--border-glass)]">
        <div
          className={`progress-bar-fill h-full rounded-full bg-gradient-to-r ${tones[tone]} transition-[width] duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]`}
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </div>
    </div>
  )
}

export function InsightList({ items }) {
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <motion.div
          key={item.label}
          variants={hoverCardVariants}
          initial="rest"
          whileHover="hover"
          className="flex items-start justify-between gap-4 rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass-strong)] px-5 py-4 transition-colors hover:bg-[var(--bg-glass)]"
        >
          <div className="space-y-1">
            <p className="text-sm font-bold text-[var(--text-main)]">{item.label}</p>
            <p className="text-xs font-medium text-[var(--text-muted)]">{item.description}</p>
          </div>
          <span className={`badge ${item.tone || 'badge-neutral'} shrink-0`}>{item.value}</span>
        </motion.div>
      ))}
    </div>
  )
}

export function InfoCallout({ tone = 'electric', title, description, cta, icon: Icon = Signal }) {
  const tones = {
    electric: 'border-cyan-500/20 bg-cyan-500/5',
    warning: 'border-amber-500/20 bg-amber-500/5',
    danger: 'border-rose-500/20 bg-rose-500/5',
  }
  
  const iconTones = {
    electric: 'text-cyan-500',
    warning: 'text-amber-500',
    danger: 'text-rose-500',
  }

  return (
    <div className={`rounded-2xl border p-5 sm:p-6 backdrop-blur-md ${tones[tone]}`}>
      <div className="flex items-start gap-4">
        <div className={`rounded-xl bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] p-3 shadow-sm ${iconTones[tone]}`}>
          <Icon className="h-6 w-6" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-base font-bold text-[var(--text-main)]">{title}</h3>
          <p className="mt-1.5 text-sm font-medium text-[var(--text-muted)]">{description}</p>
          {cta ? <div className="mt-5">{cta}</div> : null}
        </div>
      </div>
    </div>
  )
}

export function TableMobileFallback({
  items,
  renderTitle,
  renderMeta,
  renderRight,
  getCardClassName,
  getItemId,
  onItemActivate,
}) {
  return (
    <div className="space-y-3 md:hidden">
      {items.map((item) => (
        <div
          key={item.id}
          id={getItemId?.(item)}
          role={onItemActivate ? 'button' : undefined}
          tabIndex={onItemActivate ? 0 : undefined}
          onClick={onItemActivate ? () => onItemActivate(item) : undefined}
          onKeyDown={
            onItemActivate
              ? (event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault()
                    onItemActivate(item)
                  }
                }
              : undefined
          }
          className={`card p-4 ${onItemActivate ? 'cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/50' : ''} ${getCardClassName?.(item) || ''}`}
        >
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-2 min-w-0 flex-1">
              <p className="text-sm font-bold text-[var(--text-main)]">{renderTitle(item)}</p>
              <div className="space-y-1 text-xs font-medium text-[var(--text-muted)]">{renderMeta(item)}</div>
            </div>
            {renderRight?.(item)}
          </div>
        </div>
      ))}
    </div>
  )
}

export function DemoNotice({ text = '当前为演示数据，适合体验页面布局与流程。' }) {
  return (
    <div className="badge badge-warning px-3 py-1.5">
      <AlertTriangle className="h-3.5 w-3.5" />
      {text}
    </div>
  )
}

export function QuickLink({ label, description }) {
  return (
    <motion.div 
      whileTap={tapEffect}
      variants={hoverCardVariants}
      initial="rest"
      whileHover="hover"
      className="flex items-center justify-between gap-3 rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass-strong)] px-4 py-3 transition-colors hover:border-[var(--accent-primary)] hover:bg-cyan-500/5 group cursor-pointer"
    >
      <div>
        <p className="text-sm font-bold text-[var(--text-main)] group-hover:text-[var(--accent-primary)] transition-colors">{label}</p>
        <p className="text-xs font-medium text-[var(--text-muted)] mt-0.5">{description}</p>
      </div>
      <ArrowRight className="h-4 w-4 text-[var(--text-muted)] group-hover:text-[var(--accent-primary)] transition-colors" />
    </motion.div>
  )
}

export function Skeleton({ className = '' }) {
  return (
    <div
      className={`skeleton-shimmer rounded-md ${className}`}
    />
  )
}

export function MetricCardSkeleton() {
  return (
    <section className="card flex flex-col justify-between h-[160px]">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-2 w-full">
          <Skeleton className="h-4 w-1/2 rounded" />
          <Skeleton className="h-8 w-3/4 rounded mt-2" />
        </div>
        <Skeleton className="h-12 w-12 rounded-xl shrink-0" />
      </div>
      <div className="mt-auto pt-3 border-t border-[var(--border-glass)]">
        <Skeleton className="h-3 w-2/3 rounded" />
      </div>
    </section>
  )
}

