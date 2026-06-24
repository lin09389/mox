import { lazy, Suspense, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  Activity,
  ArrowRight,
  BarChart3,
  ChevronDown,
  ChevronUp,
  Clock3,
  Radar,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from 'lucide-react'
import { useDashboardStats, useRecentAttacks, useDefenseLogs, useMonitoringVisualization } from '../hooks/queries'
import { useApiStatus } from '../hooks/useApiStatus'
import { isDemoModeEnabled } from '../api'
import { HeroStat, InfoCallout, InsightList, MetricCard, MetricCardSkeleton, PanelHeader, QuickLink, Skeleton } from '../components/ui/AppFrame'
import { WorkspacePanelIntro } from '../components/workspace'

const ThreatMap3D = lazy(() => import('../components/ui/ThreatMap3D'))
const ThreatRadarChart = lazy(() => import('../components/ui/ThreatRadarChart'))
const ThreatAreaChart = lazy(() => import('../components/ui/ThreatAreaChart'))

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

import { WorkspacePageShell } from '../components/workspace'
import { itemVariants } from '../utils/animations'

export default function SecurityDashboard() {
  const { data: rawStats, isLoading: statsLoading, dataUpdatedAt: statsUpdatedAt } = useDashboardStats()
  const { data: recentAttacks, isLoading: attacksLoading } = useRecentAttacks()
  const { data: defenseLogs, isLoading: logsLoading } = useDefenseLogs()
  const { data: visualization, isLoading: vizLoading } = useMonitoringVisualization()
  const { isConnected } = useApiStatus()

  const stats = useMemo(() => normalizeStats(rawStats), [rawStats])
  const [now] = useState(() => Date.now())
  const [topologyOpen, setTopologyOpen] = useState(false)
  const [chartsOpen, setChartsOpen] = useState(false)
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
    <WorkspacePageShell theme="dashboard">
      <motion.div variants={itemVariants}>
        <WorkspacePanelIntro
          theme="dashboard"
          badgeLabel="态势感知 · 系统总览"
          description="宏观掌控攻击、防御与模型流转链路，快速识别风险信号与下一步演练方向。"
          action={
            <div className="badge badge-neutral bg-[var(--bg-glass-strong)] border-[var(--border-glass-strong)] px-3 py-1.5 shrink-0">
              <Clock3 className="h-3.5 w-3.5" />
              {statsLoading ? '正在连接…' : `最新同步 ${lastUpdate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`}
            </div>
          }
        />
      </motion.div>

      <motion.section variants={itemVariants} className="mb-6 grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-6">
        <div className="relative card overflow-hidden flex flex-col shadow-2xl ring-1 ring-cyan-500/10">
          <div className="flex items-center justify-between gap-3 border-b border-[var(--border-glass)] bg-[var(--bg-glass-strong)] px-4 py-3">
            <h3 className="text-base font-bold text-[var(--text-main)] flex items-center gap-2">
              <Radar className="h-5 w-5 text-cyan-400" />
              全球资产与实时威胁拓扑
            </h3>
            <div className="flex items-center gap-2">
              <span className="badge badge-info bg-cyan-500/20 border-cyan-500/30 text-cyan-400 text-xs">
                {isConnected && !isDemoModeEnabled ? '实时数据' : '演示 / 离线'}
              </span>
              <button
                type="button"
                className="btn-secondary inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold"
                onClick={() => setTopologyOpen((open) => !open)}
                aria-expanded={topologyOpen}
              >
                {topologyOpen ? (
                  <>
                    <ChevronUp className="h-3.5 w-3.5" />
                    收起
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-3.5 w-3.5" />
                    展开 3D
                  </>
                )}
              </button>
            </div>
          </div>

          {topologyOpen ? (
            <div className="min-h-[420px] flex-1 w-full">
              <Suspense fallback={<Skeleton className="h-[420px] w-full rounded-none" />}>
                <ThreatMap3D
                  nodes={visualization?.topology?.nodes}
                  links={visualization?.topology?.links}
                  isLoading={vizLoading}
                />
              </Suspense>
            </div>
          ) : (
            <div className="flex min-h-[140px] flex-col justify-center gap-3 px-5 py-4 text-sm text-[var(--text-muted)]">
              <p>3D 威胁拓扑默认折叠，以减少首屏信息密度与 GPU 占用。</p>
              <div className="flex flex-wrap gap-2 text-xs font-bold">
                <span className="badge badge-neutral">节点 {visualization?.topology?.nodes?.length ?? 0}</span>
                <span className="badge badge-neutral">链路 {visualization?.topology?.links?.length ?? 0}</span>
                <span className="badge badge-neutral">拦截 {stats.blockedRequests.toLocaleString()}</span>
              </div>
            </div>
          )}
        </div>

        {/* Dynamic HUD Charts — collapsed by default on mobile */}
        <div className="card overflow-hidden flex flex-col">
          <div className="flex items-center justify-between gap-3 border-b border-[var(--border-glass)] bg-[var(--bg-glass-strong)] px-4 py-3">
            <h3 className="text-base font-bold text-[var(--text-main)] flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-cyan-400" />
              趋势与雷达
            </h3>
            <button
              type="button"
              className="btn-secondary inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold"
              onClick={() => setChartsOpen((open) => !open)}
              aria-expanded={chartsOpen}
            >
              {chartsOpen ? (
                <>
                  <ChevronUp className="h-3.5 w-3.5" />
                  收起
                </>
              ) : (
                <>
                  <ChevronDown className="h-3.5 w-3.5" />
                  展开图表
                </>
              )}
            </button>
          </div>

          {chartsOpen ? (
            <div className="flex flex-col gap-6 p-4">
              <div className="card p-5 h-[260px] flex flex-col">
                <PanelHeader title="24h 攻击与拦截趋势" description="红队与防御机制的对抗烈度" icon={TrendingUp} />
                <div className="flex-1 mt-2">
                  <Suspense fallback={<Skeleton className="h-full w-full" />}>
                    <ThreatAreaChart series={visualization?.trends?.series} isLoading={vizLoading} />
                  </Suspense>
                </div>
              </div>

              <div className="card p-5 flex-1 flex flex-col">
                <PanelHeader title="安全漏洞雷达" description="当前系统对各类型攻击的暴露面" icon={ShieldAlert} />
                <div className="flex-1 mt-2">
                  <Suspense fallback={<Skeleton className="h-full w-full min-h-[180px]" />}>
                    <ThreatRadarChart items={visualization?.radar?.items} isLoading={vizLoading} />
                  </Suspense>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex min-h-[140px] flex-col justify-center gap-2 px-5 py-4 text-sm text-[var(--text-muted)]">
              <p>趋势与雷达图默认折叠，展开后再加载图表资源。</p>
              <div className="flex flex-wrap gap-2 text-xs font-bold">
                <span className="badge badge-neutral">趋势点 {visualization?.trends?.series?.length ?? 0}</span>
                <span className="badge badge-neutral">雷达维 {visualization?.radar?.items?.length ?? 0}</span>
              </div>
            </div>
          )}
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
              <Link to="/governance?tab=reports" className="block">
                <QuickLink label="评估报告页" description="查看归档报告与风险指标趋势。" />
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
          <Link to="/testing?tab=owasp" className="block"><QuickLink label="OWASP 测试" description="用标准化风险类目做专项验证。" /></Link>
          <Link to="/testing?tab=redteam" className="block"><QuickLink label="红队演练" description="按更接近真实攻击链的方式复测。" /></Link>
          <Link to="/evaluation?tab=benchmark" className="block"><QuickLink label="基准评测" description="对比不同模型或数据集表现。" /></Link>
          <Link to="/governance?tab=reports" className="block"><QuickLink label="评估报告" description="沉淀结果，用于分享与复盘。" /></Link>
        </div>
      </motion.section>
    </WorkspacePageShell>
  )
}
