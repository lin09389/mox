import { useMemo } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  Activity,
  ArrowRight,
  BarChart3,
  Clock3,
  Radar,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  AlertTriangle,
  Database
} from 'lucide-react'
import { useDashboardStats, useRecentAttacks, useDefenseLogs } from '../hooks/queries'
import { HeroStat, InfoCallout, InsightList, MetricCard, MetricCardSkeleton, PageHeader, PanelHeader, QuickLink, Skeleton } from '../components/ui/AppFrame'

function normalizeStats(stats) {
  return {
    totalRequests: stats?.totalRequests ?? 0,
    blockedRequests: stats?.blockedRequests ?? 0,
    attackSuccessRate: stats?.attackSuccessRate ?? 0,
    defenseSuccessRate: stats?.defenseSuccessRate ?? 0,
  }
}

function formatRelativeTime(date) {
  const diff = Date.now() - new Date(date).getTime()
  if (Number.isNaN(diff)) return '未知时间'
  if (diff < 60_000) return '刚刚'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} 小时前`
  return new Date(date).toLocaleDateString('zh-CN')
}

import { containerVariants, itemVariants } from '../utils/animations'

export default function SecurityDashboard() {
  const { data: rawStats, isLoading: statsLoading, dataUpdatedAt: statsUpdatedAt } = useDashboardStats()
  const { data: recentAttacks, isLoading: attacksLoading } = useRecentAttacks()
  const { data: defenseLogs, isLoading: logsLoading } = useDefenseLogs()

  const stats = useMemo(() => normalizeStats(rawStats), [rawStats])
  const [now] = useState(() => Date.now())
  const lastUpdate = new Date(statsUpdatedAt || now)

  const overview = useMemo(() => {
    const riskRatio = stats.totalRequests ? stats.blockedRequests / stats.totalRequests : 0
    return [
      {
        icon: Activity,
        label: '总请求量',
        value: stats.totalRequests.toLocaleString(),
        hint: '本周期内进入平台的所有请求',
        tone: 'electric',
      },
      {
        icon: ShieldAlert,
        label: '拦截请求',
        value: stats.blockedRequests.toLocaleString(),
        hint: `占比 ${(riskRatio * 100).toFixed(1)}%`,
        tone: 'lava',
      },
      {
        icon: ShieldCheck,
        label: '防御成功率',
        value: `${(stats.defenseSuccessRate * 100).toFixed(1)}%`,
        hint: '综合防护模块当前表现',
        tone: 'neon',
      },
      {
        icon: TrendingUp,
        label: '攻击成功率',
        value: `${(stats.attackSuccessRate * 100).toFixed(1)}%`,
        hint: '越高越需要尽快处理',
        tone: 'amber',
      },
    ]
  }, [stats])

  const signalItems = useMemo(
    () => [
      {
        label: '当前风险等级',
        description:
          stats.attackSuccessRate > 0.15 ? '攻击成功率偏高，建议优先查看攻击页与历史页。' : '风险处于可控区间，继续保持回归测试。',
        value: stats.attackSuccessRate > 0.15 ? '偏高' : '稳定',
        tone: stats.attackSuccessRate > 0.15 ? 'badge-danger' : 'badge-success',
      },
      {
        label: '防线状态',
        description:
          stats.defenseSuccessRate > 0.9 ? '主要防线正常工作。' : '部分防线可能存在漏检，建议检查防御日志。',
        value: stats.defenseSuccessRate > 0.9 ? '健康' : '需关注',
        tone: stats.defenseSuccessRate > 0.9 ? 'badge-success' : 'badge-warning',
      },
      {
        label: '演练建议',
        description: '定期切换到红队、OWASP 和多模态模块，避免只验证基础攻击。 ',
        value: '继续扩面',
        tone: 'badge-neutral',
      },
    ],
    [stats.attackSuccessRate, stats.defenseSuccessRate]
  )

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="page-shell"
    >
      <motion.div variants={itemVariants}>
        <PageHeader
          eyebrow="SECURITY OVERVIEW"
          title="专业监控台"
          description="把当前请求规模、拦截表现、攻击成功率和近期高风险活动放在同一视野中，便于快速判断是否需要进入专项页面。"
          badge={
            <div className="badge badge-neutral bg-[var(--bg-glass-strong)] border-[var(--border-glass-strong)] px-3 py-1.5">
              <Clock3 className="h-3.5 w-3.5" />
              {statsLoading ? '正在连接...' : `最近更新 ${lastUpdate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`}
            </div>
          }
        />
      </motion.div>

      <motion.section variants={itemVariants} className="hero-panel mb-2">
        <div className="relative z-10 grid gap-6 xl:grid-cols-[1.3fr_0.9fr]">
          <div className="space-y-5">
            <span className="badge badge-info bg-cyan-500/10 border-cyan-500/20 text-cyan-500">
              <Radar className="h-3.5 w-3.5" />
              30 秒自动刷新监控数据
            </span>
            <h2 className="font-display text-3xl font-bold tracking-tight text-[var(--text-main)] sm:text-4xl leading-tight">
              先看风险信号，再进入具体模块处理。
            </h2>
            <p className="max-w-2xl text-sm font-medium text-[var(--text-muted)] sm:text-base leading-relaxed">
              这版首页把随机图表替换成更稳定的监控信号视图。你可以先判断风险热度，再决定是去攻击页复测、防御页排查，还是到历史页做回归分析。
            </p>
            <div className="flex flex-wrap gap-4 pt-2">
              <Link to="/attack" className="btn-primary">
                进入攻击测试
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/history" className="btn-secondary">
                查看历史记录
              </Link>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-1 justify-center">
            {statsLoading ? (
              <>
                 <Skeleton className="h-[120px] w-full" />
                 <div className="hidden xl:grid grid-cols-2 gap-4">
                   <Skeleton className="h-[120px] w-full" />
                   <Skeleton className="h-[120px] w-full" />
                 </div>
              </>
            ) : (
              <>
                <HeroStat
                  label="实时拦截"
                  value={stats.blockedRequests.toLocaleString()}
                  hint="当前累计被防线拦截的请求数"
                  tone="danger"
                />
                <div className="hidden xl:grid grid-cols-2 gap-4">
                  <HeroStat
                    label="风险热度"
                    value={`${Math.round(stats.attackSuccessRate * 100)}%`}
                    hint="越高越需要回归"
                    tone="warning"
                  />
                  <HeroStat
                    label="防御韧性"
                    value={`${Math.round(stats.defenseSuccessRate * 100)}%`}
                    hint="策略当前有效性"
                    tone="success"
                  />
                </div>
                {/* Mobile/Tablet Fallback for Hero Stats */}
                <div className="xl:hidden sm:contents hidden">
                  <HeroStat
                    label="风险热度"
                    value={`${Math.round(stats.attackSuccessRate * 100)}%`}
                    hint="攻击成功率越高越危险"
                    tone="warning"
                  />
                  <HeroStat
                    label="防御韧性"
                    value={`${Math.round(stats.defenseSuccessRate * 100)}%`}
                    hint="防护策略当前有效性"
                    tone="success"
                  />
                </div>
              </>
            )}
          </div>
        </div>
      </motion.section>

      <motion.div variants={itemVariants} className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {statsLoading ? (
          Array.from({ length: 4 }).map((_, i) => <MetricCardSkeleton key={i} />)
        ) : (
          overview.map((item) => (
            <MetricCard
              key={item.label}
              icon={item.icon}
              label={item.label}
              value={item.value}
              hint={item.hint}
              tone={item.tone}
            />
          ))
        )}
      </motion.div>

      <motion.div variants={itemVariants} className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="card p-5">
          <PanelHeader
            title="风险信号"
            description="把当前应该优先注意的几项信息做成可读的简短结论。"
          />
          {statsLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : (
            <InsightList items={signalItems} />
          )}
        </section>

        <InfoCallout
          title="下一步建议"
          description="如果攻击成功率升高，优先进入攻击测试页复刻案例；如果防御成功率下降，优先查看防御日志确认是哪一层失效。"
          icon={Sparkles}
          tone="electric"
          cta={
            <div className="space-y-3 mt-4">
              <Link to="/attack" className="block">
                <QuickLink label="攻击测试页" description="复刻高风险案例并对比成功分数变化。" />
              </Link>
              <Link to="/defense" className="block">
                <QuickLink label="防御检测页" description="确认输入过滤和输出审查是否漏检。" />
              </Link>
              <Link to="/history" className="block">
                <QuickLink label="历史记录页" description="查看近期问题是否持续出现。" />
              </Link>
            </div>
          }
        />
      </motion.div>

      <motion.div variants={itemVariants} className="grid gap-6 xl:grid-cols-2">
        <section className="card p-5">
          <PanelHeader
            title="近期攻击事件"
            description="只保留最有用的信息：类型、结果和触发时间。"
          />

          {attacksLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}
            </div>
          ) : recentAttacks?.length === 0 ? (
            <div className="flex min-h-[220px] flex-col items-center justify-center rounded-xl border border-dashed border-[var(--border-glass-strong)] bg-[var(--bg-glass-strong)] text-sm font-medium text-[var(--text-muted)]">
              目前没有新的攻击事件。
            </div>
          ) : (
            <div className="space-y-3">
              {recentAttacks?.slice(0, 5).map((attack, index) => (
                <motion.div
                  key={`${attack.type}-${index}`}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  whileHover={{ scale: 1.01, x: 2, boxShadow: 'var(--shadow-soft)' }}
                  transition={{ delay: index * 0.04, duration: 0.2 }}
                  className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass-strong)] px-5 py-4 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-bold text-[var(--text-main)]">
                        {attack.type || '未知攻击类型'}
                      </p>
                      <p className="mt-1.5 text-xs font-medium text-[var(--text-muted)]">
                        {(attack.prompt || '无提示词内容').slice(0, 64)}
                      </p>
                    </div>
                    <div className="space-y-2 text-right">
                      <span className={`badge ${attack.success ? 'badge-danger' : 'badge-success'}`}>
                        {attack.success ? '攻击成功' : '已拦截'}
                      </span>
                      <p className="text-xs font-mono text-[var(--text-muted)] opacity-70">{formatRelativeTime(attack.created_at || new Date())}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </section>

        <section className="card p-5">
          <PanelHeader
            title="防御日志快照"
            description="帮助判断当前是输入过滤、输出过滤还是其他策略在承压。"
          />

          {logsLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}
            </div>
          ) : defenseLogs?.length === 0 ? (
            <div className="flex min-h-[220px] flex-col items-center justify-center rounded-xl border border-dashed border-[var(--border-glass-strong)] bg-[var(--bg-glass-strong)] text-sm font-medium text-[var(--text-muted)]">
              暂无防御日志，等待新的请求进入。
            </div>
          ) : (
            <div className="space-y-3">
              {defenseLogs?.slice(0, 5).map((log, index) => (
                <motion.div
                  key={`${log.defense_type}-${index}`}
                  initial={{ opacity: 0, x: 8 }}
                  animate={{ opacity: 1, x: 0 }}
                  whileHover={{ scale: 1.01, x: -2, boxShadow: 'var(--shadow-soft)' }}
                  transition={{ delay: index * 0.04, duration: 0.2 }}
                  className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass-strong)] px-5 py-4 transition-colors"
                >
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm font-bold text-[var(--text-main)]">
                        {log.defense_type || '防御模块'}
                      </p>
                      <p className="mt-1.5 text-xs font-medium text-[var(--text-muted)]">
                        置信度 {(Number(log.confidence || 0) * 100).toFixed(1)}%
                      </p>
                    </div>
                    <span className={`badge ${log.blocked ? 'badge-danger' : 'badge-success'}`}>
                      {log.blocked ? '已拦截' : '已放行'}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </section>
      </motion.div>

      <motion.section variants={itemVariants} className="card p-6">
        <PanelHeader
          title="快捷入口"
          description="把常用路径放在首页，减少多层导航查找。"
        />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4 mt-4">
          <Link to="/owasp" className="block"><QuickLink label="OWASP 测试" description="用标准化风险类目做专项验证。" /></Link>
          <Link to="/redteam" className="block"><QuickLink label="红队演练" description="按更接近真实攻击链的方式复测。" /></Link>
          <Link to="/benchmark" className="block"><QuickLink label="基准评测" description="对比不同模型或数据集表现。" /></Link>
          <Link to="/reports" className="block"><QuickLink label="评估报告" description="沉淀结果，用于分享与复盘。" /></Link>
        </div>
      </motion.section>
    </motion.div>
  )
}
