import { AlertTriangle, ArrowRight, Signal, Sparkles } from 'lucide-react'
import { motion } from 'framer-motion'

export const animContainer = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.05,
    },
  },
}

export const animItem = {
  hidden: { opacity: 0, y: 20, scale: 0.96 },
  show: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: 'spring', stiffness: 280, damping: 22 },
  },
}

export function PageHeader({
  eyebrow = 'CONTROL CENTER',
  title,
  description,
  actions,
  badge,
}) {
  return (
    <motion.header 
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 200, damping: 20 }}
      className="mb-8 flex flex-col gap-5 md:flex-row md:items-end md:justify-between border-b border-graphite-200/40 pb-6 relative"
    >
      <div className="absolute -top-10 -left-10 w-40 h-40 bg-electric-400/10 blur-3xl rounded-full pointer-events-none"></div>
      <div className="space-y-3 relative z-10">
        <motion.p 
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="text-[11px] font-bold uppercase tracking-[0.25em] text-electric-700 bg-electric-50 inline-block px-2 py-0.5 rounded-full border border-electric-100"
        >
          {eyebrow}
        </motion.p>
        <motion.h1 
          initial={{ opacity: 0, filter: 'blur(10px)' }}
          animate={{ opacity: 1, filter: 'blur(0px)' }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="font-display text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-graphite-950 via-graphite-800 to-graphite-600 sm:text-4xl"
        >
          {title}
        </motion.h1>
        {description ? <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }} className="max-w-2xl text-sm font-medium text-graphite-500 sm:text-[15px] leading-relaxed">{description}</motion.p> : null}
      </div>
      {(badge || actions) && (
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ type: 'spring', stiffness: 200, damping: 20, delay: 0.1 }}
          className="flex flex-wrap items-center justify-start gap-3 md:justify-end relative z-10"
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
      } px-3 py-1.5 text-[11px] font-medium`}
    >
      <span className={`h-2 w-2 rounded-full ${online ? 'bg-neon-500 shadow-[0_0_0_2px_rgba(34,197,94,0.2)]' : 'bg-amber-500 shadow-[0_0_0_2px_rgba(245,158,11,0.2)]'}`} />
      {online ? onlineLabel : offlineLabel}
    </div>
  )
}

export function HeroStat({ label, value, hint, tone = 'neutral' }) {
  const tones = {
    neutral: 'bg-white/80 text-graphite-950 border-white shadow-sm',
    electric: 'bg-electric-50 text-electric-900 border-electric-100/80 shadow-electric-500/5',
    success: 'bg-neon-50 text-neon-900 border-neon-100/80 shadow-neon-500/5',
    danger: 'bg-lava-50 text-lava-900 border-lava-100/80 shadow-lava-500/5',
    warning: 'bg-amber-50 text-amber-900 border-amber-100/80 shadow-amber-500/5',
  }

  return (
    <motion.div 
      variants={animItem}
      whileHover={{ y: -4, scale: 1.01, transition: { type: 'spring', stiffness: 400, damping: 25 } }}
      className={`rounded-2xl border p-6 backdrop-blur-md cursor-default ${tones[tone]}`}
    >
      <p className="text-[11px] font-bold uppercase tracking-[0.2em] opacity-70">{label}</p>
      <motion.p 
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2, type: 'spring', stiffness: 300, damping: 20 }}
        className="mt-3 font-display text-4xl font-bold tracking-tight"
      >
        {value}
      </motion.p>
      {hint ? <p className="mt-1.5 text-xs font-medium opacity-80">{hint}</p> : null}
    </motion.div>
  )
}

export function MetricCard({ icon: Icon, label, value, hint, tone = 'electric' }) {
  const styles = {
    electric: 'bg-gradient-to-br from-electric-50 to-white text-electric-700 border-electric-100 shadow-electric-500/10',
    lava: 'bg-gradient-to-br from-lava-50 to-white text-lava-600 border-lava-100 shadow-lava-500/10',
    neon: 'bg-gradient-to-br from-neon-50 to-white text-neon-600 border-neon-100 shadow-neon-500/10',
    amber: 'bg-gradient-to-br from-amber-50 to-white text-amber-600 border-amber-100 shadow-amber-500/10',
    graphite: 'bg-gradient-to-br from-graphite-50 to-white text-graphite-600 border-graphite-200 shadow-graphite-500/10',
  }

  return (
    <motion.section 
      variants={animItem}
      whileHover={{ y: -4, scale: 1.02, transition: { type: 'spring', stiffness: 400, damping: 25 } }}
      whileTap={{ scale: 0.98 }}
      className="card group cursor-pointer"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-graphite-500">{label}</p>
          <p className="font-display text-3xl font-bold tracking-tight text-graphite-950 mt-3 group-hover:text-electric-700 transition-colors duration-300">{value}</p>
          {hint ? <p className="mt-2 text-xs font-medium text-graphite-500">{hint}</p> : null}
        </div>
        <motion.div 
          className={`rounded-xl border p-3 ${styles[tone]}`}
          whileHover={{ rotate: 12, scale: 1.15 }}
          transition={{ type: 'spring', stiffness: 300, damping: 15 }}
        >
          <Icon className="h-6 w-6" />
        </motion.div>
      </div>
    </motion.section>
  )
}

export function PanelHeader({ title, description, action }) {
  return (
    <div className="mb-6 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 border-b border-graphite-200 pb-4">
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
    neutral: 'bg-graphite-50 text-graphite-500',
    electric: 'bg-electric-50 text-electric-700',
    warning: 'bg-amber-50 text-amber-600',
    danger: 'bg-lava-50 text-lava-600',
    success: 'bg-neon-50 text-neon-600',
  }

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex min-h-[240px] flex-col items-center justify-center rounded-xl border border-dashed border-graphite-300 bg-graphite-50/50 px-6 py-10 text-center"
    >
      <div className={`mb-4 rounded-xl p-4 ${tones[tone]}`}>
        <Icon className="h-6 w-6" />
      </div>
      <h3 className="text-base font-semibold text-graphite-900">{title}</h3>
      {description ? <p className="mt-2 max-w-sm text-sm text-graphite-500">{description}</p> : null}
      {action ? <div className="mt-6">{action}</div> : null}
    </motion.div>
  )
}

export function ProgressMeter({ value = 0, tone = 'electric', label }) {
  const tones = {
    electric: 'bg-electric-500',
    danger: 'bg-lava-500',
    success: 'bg-neon-500',
    warning: 'bg-amber-500',
  }

  return (
    <div className="space-y-2">
      {label ? <div className="flex items-center justify-between text-xs font-medium text-graphite-600"><span>{label}</span><span>{value}%</span></div> : null}
      <div className="h-2 w-full overflow-hidden rounded-full bg-graphite-100 relative">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.max(0, Math.min(100, value))}%` }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          className={`absolute left-0 top-0 bottom-0 rounded-full ${tones[tone]}`}
        />
      </div>
    </div>
  )
}

export function InsightList({ items }) {
  return (
    <motion.div 
      variants={animContainer}
      initial="hidden"
      animate="show"
      className="space-y-3"
    >
      {items.map((item, idx) => (
        <motion.div
          variants={animItem}
          key={item.label || idx}
          whileHover={{ scale: 1.01, backgroundColor: 'rgba(255,255,255,1)' }}
          className="group flex items-start justify-between gap-4 rounded-xl border border-white/60 bg-white/40 px-5 py-4 transition-shadow hover:shadow-soft backdrop-blur-sm cursor-default"
        >
          <div className="space-y-1.5">
            <p className="text-sm font-semibold text-graphite-900 group-hover:text-electric-700 transition-colors">{item.label}</p>
            <p className="text-xs text-graphite-500 leading-relaxed font-medium">{item.description}</p>
          </div>
          <motion.span 
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3 + idx * 0.1, type: 'spring' }}
            className={`badge shrink-0 ${item.tone || 'badge-neutral'}`}
          >
            {item.value}
          </motion.span>
        </motion.div>
      ))}
    </motion.div>
  )
}

export function InfoCallout({ tone = 'electric', title, description, cta, icon: Icon = Signal }) {
  const tones = {
    electric: 'border-electric-200/60 bg-gradient-to-br from-electric-50/80 to-white/60 text-electric-900 shadow-electric-500/5',
    warning: 'border-amber-200/60 bg-gradient-to-br from-amber-50/80 to-white/60 text-amber-900 shadow-amber-500/5',
    danger: 'border-lava-200/60 bg-gradient-to-br from-lava-50/80 to-white/60 text-lava-900 shadow-lava-500/5',
  }

  const iconTones = {
    electric: 'bg-white text-electric-700 shadow-sm border border-electric-100',
    warning: 'bg-white text-amber-600 shadow-sm border border-amber-100',
    danger: 'bg-white text-lava-600 shadow-sm border border-lava-100',
  }

  return (
    <motion.div 
      variants={animItem}
      whileHover={{ y: -2, scale: 1.01 }}
      className={`rounded-2xl border p-6 backdrop-blur-md ${tones[tone]}`}
    >
      <div className="flex items-start gap-4">
        <motion.div 
          whileHover={{ rotate: [0, -10, 10, 0] }}
          transition={{ duration: 0.5 }}
          className={`rounded-xl p-3 shrink-0 ${iconTones[tone]}`}
        >
          <Icon className="h-6 w-6" />
        </motion.div>
        <div className="min-w-0 flex-1">
          <h3 className="text-base font-bold">{title}</h3>
          <p className="mt-2 text-sm font-medium opacity-80 leading-relaxed">{description}</p>
          {cta ? <div className="mt-6">{cta}</div> : null}
        </div>
      </div>
    </motion.div>
  )
}

export function TableMobileFallback({ items, renderTitle, renderMeta, renderRight }) {
  return (
    <motion.div variants={animContainer} initial="hidden" animate="show" className="space-y-3 md:hidden">
      {items.map((item, idx) => (
        <motion.div variants={animItem} key={item.id || idx} className="card p-4">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-2">
              <p className="text-sm font-semibold text-graphite-900">{renderTitle(item)}</p>
              <div className="space-y-1 text-xs text-graphite-500">{renderMeta(item)}</div>
            </div>
            {renderRight(item)}
          </div>
        </motion.div>
      ))}
    </motion.div>
  )
}

export function DemoNotice({ text = '当前为演示数据，适合体验页面布局与流程。' }) {
  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="badge badge-warning px-3 py-1.5 shadow-sm"
    >
      <AlertTriangle className="h-3 w-3" />
      {text}
    </motion.div>
  )
}

export function QuickLink({ label, description }) {
  return (
    <motion.div 
      variants={animItem}
      whileHover={{ scale: 1.02, y: -2, backgroundColor: 'rgba(255,255,255,1)' }}
      whileTap={{ scale: 0.98 }}
      className="group flex items-center justify-between gap-4 rounded-xl border border-white/60 bg-white/40 px-5 py-4 transition-colors hover:border-white hover:shadow-soft backdrop-blur-sm cursor-pointer"
    >
      <div>
        <p className="text-sm font-semibold text-graphite-900 group-hover:text-electric-700 transition-colors">{label}</p>
        <p className="text-xs text-graphite-500 mt-1 font-medium">{description}</p>
      </div>
      <motion.div 
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        className="rounded-full bg-white border border-graphite-200 p-2 text-graphite-600 shadow-sm transition-colors group-hover:bg-electric-50 group-hover:text-electric-700 group-hover:border-electric-100"
      >
        <ArrowRight className="h-4 w-4" />
      </motion.div>
    </motion.div>
  )
}
