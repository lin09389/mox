import { AlertTriangle, ArrowRight, Signal, Sparkles } from 'lucide-react'

export function PageHeader({
  eyebrow = 'CONTROL CENTER',
  title,
  description,
  actions,
  badge,
}) {
  return (
    <header className="section-header">
      <div className="space-y-2">
        <p className="section-kicker">{eyebrow}</p>
        <h1 className="section-title">{title}</h1>
        {description ? <p className="section-subtitle">{description}</p> : null}
      </div>
      {(badge || actions) && (
        <div className="flex flex-wrap items-center justify-start gap-3 md:justify-end">
          {badge}
          {actions}
        </div>
      )}
    </header>
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
    neutral: 'bg-white/70 text-graphite-950 border-white/70',
    electric: 'bg-electric-50/90 text-electric-800 border-electric-100',
    success: 'bg-neon-50/90 text-neon-800 border-neon-100',
    danger: 'bg-lava-50/90 text-lava-800 border-lava-100',
    warning: 'bg-amber-50/90 text-amber-800 border-amber-100',
  }

  return (
    <div className={`rounded-[20px] border px-4 py-4 ${tones[tone]}`}>
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] opacity-70">{label}</p>
      <p className="mt-2 font-display text-2xl font-bold tracking-tight">{value}</p>
      {hint ? <p className="mt-1 text-xs opacity-75">{hint}</p> : null}
    </div>
  )
}

export function MetricCard({ icon: Icon, label, value, hint, tone = 'electric' }) {
  const styles = {
    electric: 'bg-electric-50 text-electric-700 border-electric-100',
    lava: 'bg-lava-50 text-lava-700 border-lava-100',
    neon: 'bg-neon-50 text-neon-700 border-neon-100',
    amber: 'bg-amber-50 text-amber-700 border-amber-100',
    graphite: 'bg-graphite-100 text-graphite-700 border-graphite-200',
  }

  return (
    <section className="card card-hover">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-graphite-500">{label}</p>
          <p className="metric-value mt-3">{value}</p>
          {hint ? <p className="mt-2 text-sm text-graphite-500">{hint}</p> : null}
        </div>
        <div className={`rounded-2xl border p-3 ${styles[tone]}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </section>
  )
}

export function PanelHeader({ title, description, action }) {
  return (
    <div className="mb-5 flex items-start justify-between gap-4">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold text-graphite-950">{title}</h2>
        {description ? <p className="text-sm text-graphite-500">{description}</p> : null}
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
    neutral: 'bg-graphite-100 text-graphite-500',
    electric: 'bg-electric-50 text-electric-600',
    warning: 'bg-amber-50 text-amber-600',
    danger: 'bg-lava-50 text-lava-600',
    success: 'bg-neon-50 text-neon-600',
  }

  return (
    <div className="flex min-h-[240px] flex-col items-center justify-center rounded-[20px] border border-dashed border-graphite-200 bg-white/50 px-6 py-10 text-center">
      <div className={`mb-4 rounded-2xl p-4 ${tones[tone]}`}>
        <Icon className="h-7 w-7" />
      </div>
      <h3 className="text-lg font-semibold text-graphite-900">{title}</h3>
      {description ? <p className="mt-2 max-w-md text-sm text-graphite-500">{description}</p> : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  )
}

export function ProgressMeter({ value = 0, tone = 'electric', label }) {
  const tones = {
    electric: 'from-electric-400 to-electric-600',
    danger: 'from-lava-400 to-lava-600',
    success: 'from-neon-400 to-neon-600',
    warning: 'from-amber-300 to-amber-500',
  }

  return (
    <div className="space-y-2">
      {label ? <div className="flex items-center justify-between text-xs text-graphite-500"><span>{label}</span><span>{value}%</span></div> : null}
      <div className="h-2.5 overflow-hidden rounded-full bg-graphite-100">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${tones[tone]} transition-all duration-500`}
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
        <div
          key={item.label}
          className="flex items-start justify-between gap-4 rounded-[18px] border border-graphite-200/70 bg-white/70 px-4 py-3"
        >
          <div className="space-y-1">
            <p className="text-sm font-medium text-graphite-900">{item.label}</p>
            <p className="text-xs text-graphite-500">{item.description}</p>
          </div>
          <span className={`badge ${item.tone || 'badge-neutral'}`}>{item.value}</span>
        </div>
      ))}
    </div>
  )
}

export function InfoCallout({ tone = 'electric', title, description, cta, icon: Icon = Signal }) {
  const tones = {
    electric: 'border-electric-100 bg-electric-50/80',
    warning: 'border-amber-100 bg-amber-50/80',
    danger: 'border-lava-100 bg-lava-50/80',
  }

  return (
    <div className={`rounded-[22px] border p-4 sm:p-5 ${tones[tone]}`}>
      <div className="flex items-start gap-3">
        <div className="rounded-2xl bg-white/80 p-3 text-graphite-800">
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-base font-semibold text-graphite-950">{title}</h3>
          <p className="mt-1 text-sm text-graphite-600">{description}</p>
          {cta ? <div className="mt-4">{cta}</div> : null}
        </div>
      </div>
    </div>
  )
}

export function TableMobileFallback({ items, renderTitle, renderMeta, renderRight }) {
  return (
    <div className="space-y-3 md:hidden">
      {items.map((item) => (
        <div key={item.id} className="card p-4">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-2">
              <p className="text-sm font-semibold text-graphite-900">{renderTitle(item)}</p>
              <div className="space-y-1 text-xs text-graphite-500">{renderMeta(item)}</div>
            </div>
            {renderRight(item)}
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
    <div className="flex items-center justify-between gap-3 rounded-[18px] border border-graphite-200/70 bg-white/70 px-4 py-3 transition-all duration-200 hover:border-electric-200 hover:bg-white">
      <div>
        <p className="text-sm font-medium text-graphite-900">{label}</p>
        <p className="text-xs text-graphite-500">{description}</p>
      </div>
      <ArrowRight className="h-4 w-4 text-graphite-400" />
    </div>
  )
}
