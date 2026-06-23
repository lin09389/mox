import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import { ProgressMeter } from '../ui/AppFrame'
import { useHubContext } from '../../context/HubContext'
import { containerVariants, hoverCardVariants, tapEffect, wsTypeCardVariants } from '../../utils/animations'
import { WORKSPACE_THEME_META } from './themeMeta'

export function WorkspacePageShell({ theme: themeProp, children, className = '', showGrid = true }) {
  const hub = useHubContext()
  const theme = themeProp || hub?.theme || 'default'
  const meta = WORKSPACE_THEME_META[theme] || WORKSPACE_THEME_META.default

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      data-ws-theme={theme}
      className={`ws-shell page-shell ${className}`}
    >
      {showGrid && meta.showGrid ? (
        <>
          <div className="ws-shell-grid" aria-hidden />
          <div className="ws-shell-glow" aria-hidden />
        </>
      ) : null}
      {children}
    </motion.div>
  )
}

export function WorkspacePanelIntro({ theme: themeProp, description, action, badge, badgeLabel }) {
  const hub = useHubContext()
  const theme = themeProp || hub?.theme || 'default'
  const meta = WORKSPACE_THEME_META[theme] || WORKSPACE_THEME_META.default
  const BadgeIcon = meta.badgeIcon
  const label = badgeLabel || (hub?.tabLabel ? `${hub.tabLabel} · ${meta.badgeSuffix}` : meta.badgeSuffix)

  return (
    <div className="ws-panel-intro mb-5">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2 max-w-2xl">
          <div className="flex flex-wrap items-center gap-2">
            <span className="ws-threat-badge">
              {BadgeIcon ? <BadgeIcon className="h-3 w-3" /> : null}
              {label}
            </span>
            {meta.showPulse ? <span className="ws-live-pulse" aria-hidden /> : null}
          </div>
          {description ? (
            <p className="text-sm font-medium text-[var(--text-muted)] leading-relaxed">{description}</p>
          ) : null}
          {badge}
        </div>
        {action ? <div className="flex shrink-0 flex-wrap items-center gap-2">{action}</div> : null}
      </div>
    </div>
  )
}

export function WorkspaceConfigPanel({ children, className = '' }) {
  return (
    <section className={`ws-config-panel card p-6 h-fit lg:sticky lg:top-6 ${className}`}>
      {children}
    </section>
  )
}

export function WorkspaceReportPanel({ children, className = '' }) {
  return (
    <section className={`ws-report-panel card p-6 ${className}`}>
      {children}
    </section>
  )
}

export function WorkspaceTypeCard({
  active = false,
  onClick,
  icon: Icon,
  title,
  description,
  meta,
  danger = false,
  className = '',
  type = 'button',
}) {
  const Tag = type === 'button' ? motion.button : type === 'label' ? motion.label : motion.div
  return (
    <Tag
      type={type === 'button' ? 'button' : undefined}
      onClick={onClick}
      variants={wsTypeCardVariants}
      initial="rest"
      whileHover={active || type === 'div' ? undefined : 'hover'}
      whileTap={type === 'button' ? 'tap' : undefined}
      className={`ws-type-card type-card--motion ${active ? 'ws-type-card--active' : ''} ${
        active && danger ? 'ws-type-card--danger' : ''
      } ${className}`}
    >
      {active ? <span className="ws-type-card-scan" aria-hidden /> : null}
      <div className="relative z-10">
        {Icon ? (
          <div className={`ws-type-card-icon ${active ? 'ws-type-card-icon--active' : ''}`}>
            <Icon className="h-4 w-4" />
          </div>
        ) : null}
        <div className="flex items-start justify-between gap-2">
          <p className="ws-type-card-title">{title}</p>
          {meta ? <span className="ws-type-card-meta">{meta}</span> : null}
        </div>
        {description ? <p className="ws-type-card-desc">{description}</p> : null}
      </div>
    </Tag>
  )
}

export function WorkspaceRunButton({
  type = 'submit',
  onClick,
  loading = false,
  disabled = false,
  icon: Icon,
  loadingIcon: LoadingIcon = Loader2,
  loadingText = '执行中...',
  children,
  className = '',
}) {
  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      whileTap={disabled || loading ? undefined : tapEffect}
      className={`ws-run-btn w-full py-3 text-base ${className}`}
    >
      {loading ? (
        <>
          <LoadingIcon className="h-5 w-5 animate-spin" />
          {loadingText}
        </>
      ) : (
        <>
          {Icon ? <Icon className="h-5 w-5" /> : null}
          {children}
        </>
      )}
    </motion.button>
  )
}

export function WorkspaceDemoBanner({ text = '演示模式：本地沙箱推演' }) {
  return (
    <div className="ws-demo-banner">
      <span className="ws-demo-dot" aria-hidden />
      <span>{text}</span>
    </div>
  )
}

export function WorkspaceReportEmpty({
  icon: Icon,
  title,
  description,
  loading = false,
  loadingTitle,
  loadingDescription,
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="ws-report-empty"
    >
      <div className="ws-report-empty-ring">
        {loading ? (
          <span className="ws-report-empty-spinner" aria-hidden />
        ) : Icon ? (
          <Icon className="h-10 w-10 text-[var(--text-muted)] opacity-60" />
        ) : null}
      </div>
      <div className="text-center">
        <h3 className="text-lg font-bold font-display text-[var(--text-main)]">
          {loading ? loadingTitle || title : title}
        </h3>
        <p className="mt-2 text-sm font-medium text-[var(--text-muted)] max-w-sm mx-auto leading-relaxed">
          {loading ? loadingDescription || description : description}
        </p>
      </div>
    </motion.div>
  )
}

export function WorkspaceLabHero({ eyebrow, title, subtitle, stats = [] }) {
  return (
    <section className="ws-lab-hero hero-panel mb-4">
      <span className="ws-lab-hero-scan" aria-hidden />
      <div className="relative z-10 grid gap-6 lg:grid-cols-[1.3fr_0.9fr]">
        <div className="space-y-4">
          {eyebrow ? <span className="ws-threat-badge">{eyebrow}</span> : null}
          {title ? (
            <h2 className="font-display text-2xl font-bold tracking-tight text-[var(--text-main)] leading-snug sm:text-3xl">
              {title}
            </h2>
          ) : null}
          {subtitle ? (
            <p className="max-w-2xl text-sm font-medium text-[var(--text-muted)] sm:text-base leading-relaxed">
              {subtitle}
            </p>
          ) : null}
        </div>
        {stats.length > 0 ? (
          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            {stats.map((item) => (
              <motion.div
                key={item.label}
                variants={hoverCardVariants}
                initial="rest"
                whileHover="hover"
                className="ws-lab-stat"
              >
                <p className="ws-lab-stat-label">{item.label}</p>
                <p className={`ws-lab-stat-value ws-lab-stat-value--${item.tone || 'neutral'}`}>
                  {item.value}
                </p>
                {item.hint ? <p className="ws-lab-stat-hint">{item.hint}</p> : null}
              </motion.div>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  )
}

export function WorkspaceCodeBlock({ children, className = '' }) {
  return (
    <pre className={`ws-code-block ${className}`}>
      <code>{children}</code>
    </pre>
  )
}

export function WorkspaceRiskGauge({ value = 0, label, breached = false }) {
  const pct = Math.max(0, Math.min(100, Math.round(value)))
  return (
    <div className="ws-risk-gauge">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="ws-risk-gauge-label">{label || '风险热度'}</p>
          <p className={`ws-risk-gauge-value ${breached ? 'ws-risk-gauge-value--danger' : ''}`}>
            {pct}
            <span className="text-2xl font-semibold opacity-70">%</span>
          </p>
        </div>
        <div
          className={`ws-risk-ring ${breached ? 'ws-risk-ring--danger' : 'ws-risk-ring--safe'}`}
          style={{ '--risk-pct': `${pct}%` }}
          aria-hidden
        />
      </div>
      <ProgressMeter value={pct} tone={breached ? 'danger' : 'success'} />
    </div>
  )
}