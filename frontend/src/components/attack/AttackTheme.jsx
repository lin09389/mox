import { motion } from 'framer-motion'
import { Loader2, ShieldAlert } from 'lucide-react'
import { ProgressMeter } from '../ui/AppFrame'
import { useHubContext } from '../../context/HubContext'
import { containerVariants, hoverCardVariants, tapEffect, wsTypeCardVariants } from '../../utils/animations'

/** 攻击工作台页面容器：威胁网格背景 + 入场动画 */
export function AttackPageShell({ children, className = '' }) {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      data-ws-theme="attack"
      className={`attack-shell ws-shell page-shell ${className}`}
    >
      <div className="attack-shell-grid" aria-hidden />
      <div className="attack-shell-glow" aria-hidden />
      {children}
    </motion.div>
  )
}

/** 子面板说明条：渗透实验室风格 */
export function AttackPanelIntro({ description, action, badge }) {
  const hub = useHubContext()
  const tabLabel = hub?.tabLabel

  return (
    <div className="attack-panel-intro mb-5">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2 max-w-2xl">
          <div className="flex flex-wrap items-center gap-2">
            <span className="attack-threat-badge">
              <ShieldAlert className="h-3 w-3" />
              {tabLabel ? `${tabLabel} · 渗透向量` : '渗透向量'}
            </span>
            <span className="attack-live-pulse" aria-hidden />
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

/** 左侧配置面板 */
export function AttackConfigPanel({ children, className = '' }) {
  return (
    <section className={`attack-config-panel card p-6 h-fit lg:sticky lg:top-6 ${className}`}>
      {children}
    </section>
  )
}

/** 右侧报告面板 */
export function AttackReportPanel({ children, className = '' }) {
  return (
    <section className={`attack-report-panel card p-6 ${className}`}>
      {children}
    </section>
  )
}

/** 攻击类型选择卡片 */
export function AttackTypeCard({
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
      className={`attack-type-card type-card--motion ${active ? 'attack-type-card--active' : ''} ${
        active && danger ? 'attack-type-card--danger' : ''
      } ${className}`}
    >
      {active ? <span className="attack-type-card-scan" aria-hidden /> : null}
      <div className="relative z-10">
        {Icon ? (
          <div className={`attack-type-card-icon ${active ? 'attack-type-card-icon--active' : ''}`}>
            <Icon className="h-4 w-4" />
          </div>
        ) : null}
        <div className="flex items-start justify-between gap-2">
          <p className="attack-type-card-title">{title}</p>
          {meta ? <span className="attack-type-card-meta">{meta}</span> : null}
        </div>
        {description ? <p className="attack-type-card-desc">{description}</p> : null}
      </div>
    </Tag>
  )
}

/** 渗透执行主按钮 */
export function AttackRunButton({
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
      type="submit"
      disabled={disabled || loading}
      whileTap={disabled || loading ? undefined : tapEffect}
      className={`attack-run-btn w-full py-3 text-base ${className}`}
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

/** 演示模式横幅 */
export function AttackDemoBanner({ text = '演示模式：本地沙箱推演' }) {
  return (
    <div className="attack-demo-banner">
      <span className="attack-demo-dot" aria-hidden />
      <span>{text}</span>
    </div>
  )
}

/** 报告区空状态 / 加载态 */
export function AttackReportEmpty({
  icon: Icon,
  title,
  description,
  loading = false,
  loadingTitle,
  loadingDescription,
}) {
  const DisplayIcon = Icon
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="attack-report-empty"
    >
      <div className="attack-report-empty-ring">
        {loading ? (
          <span className="attack-report-empty-spinner" aria-hidden />
        ) : DisplayIcon ? (
          <DisplayIcon className="h-10 w-10 text-[var(--text-muted)] opacity-60" />
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

/** 风险热度仪表 */
export function AttackRiskGauge({ value = 0, label, breached = false }) {
  const pct = Math.max(0, Math.min(100, Math.round(value)))
  return (
    <div className="attack-risk-gauge">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="attack-risk-gauge-label">{label || '风险热度'}</p>
          <p className={`attack-risk-gauge-value ${breached ? 'attack-risk-gauge-value--danger' : ''}`}>
            {pct}
            <span className="text-2xl font-semibold opacity-70">%</span>
          </p>
        </div>
        <div
          className={`attack-risk-ring ${breached ? 'attack-risk-ring--danger' : 'attack-risk-ring--safe'}`}
          style={{ '--risk-pct': `${pct}%` }}
          aria-hidden
        />
      </div>
      <ProgressMeter value={pct} tone={breached ? 'danger' : 'success'} />
    </div>
  )
}

/** 攻击实验室 Hero 横幅 */
export function AttackLabHero({ eyebrow = '攻击实验室', title, subtitle, stats = [] }) {
  return (
    <section className="attack-lab-hero hero-panel mb-4">
      <span className="attack-lab-hero-scan" aria-hidden />
      <div className="relative z-10 grid gap-6 lg:grid-cols-[1.3fr_0.9fr]">
        <div className="space-y-4">
          <span className="attack-threat-badge">
            <ShieldAlert className="h-3 w-3" />
            {eyebrow}
          </span>
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
                className="attack-lab-stat"
              >
                <p className="attack-lab-stat-label">{item.label}</p>
                <p className={`attack-lab-stat-value attack-lab-stat-value--${item.tone || 'neutral'}`}>
                  {item.value}
                </p>
                {item.hint ? <p className="attack-lab-stat-hint">{item.hint}</p> : null}
              </motion.div>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  )
}

/** 代码/载荷输出块 */
export function AttackCodeBlock({ children, className = '' }) {
  return (
    <pre className={`attack-code-block ${className}`}>
      <code>{children}</code>
    </pre>
  )
}