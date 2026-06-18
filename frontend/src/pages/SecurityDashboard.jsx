import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  Activity,
  ArrowRight,
  BarChart3,
  Clock3,
  Radar,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from 'lucide-react'
import { getDefenseLogs, getRecentAttacks, getStats } from '../api/security'
import { HeroStat, InfoCallout, InsightList, MetricCard, PageHeader, PanelHeader, QuickLink } from '../components/ui/AppFrame'
import { useAutoRefresh } from '../hooks/useAutoRefresh'

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

export default function SecurityDashboard() {
  const [stats, setStats] = useState(normalizeStats())
  const [recentAttacks, setRecentAttacks] = useState([])
  const [defenseLogs, setDefenseLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(new Date())

  const loadData = async () => {
    try {
      const [statsData, attacksData, logsData] = await Promise.all([
        getStats(),
        getRecentAttacks(),
        getDefenseLogs(),
      ])

      setStats(normalizeStats(statsData))
      setRecentAttacks(attacksData ?? [])
      setDefenseLogs(logsData ?? [])
      setLastUpdate(new Date())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  useAutoRefresh(loadData, 30000)

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
    <div className="page-shell">
      <PageHeader
        eyebrow="SECURITY OVERVIEW"
        title="专业监控台"
        description="把当前请求规模、拦截表现、攻击成功率和近期高风险活动放在同一视野中，便于快速判断是否需要进入专项页面。"
        badge={
          <div className="badge badge-neutral px-3 py-1.5">
            <Clock3 className="h-3.5 w-3.5" />
            最近更新 {lastUpdate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
          </div>
        }
      />

      <section className="hero-panel">
        <div className="relative z-10 grid gap-4 xl:grid-cols-[1.3fr_0.9fr]">
          <div className="space-y-4">
            <span className="badge badge-neutral">
              <Radar className="h-3.5 w-3.5" />
              30 秒自动刷新监控数据
            </span>
            <h2 className="font-display text-3xl font-bold tracking-tight text-graphite-950 sm:text-4xl">
              先看风险信号，再进入具体模块处理。
            </h2>
            <p className="max-w-2xl text-sm text-graphite-600 sm:text-base">
              这版首页把随机图表替换成更稳定的监控信号视图。你可以先判断风险热度，再决定是去攻击页复测、防御页排查，还是到历史页做回归分析。
            </p>
            <div className="flex flex-wrap gap-3">
              <Link to="/attack" className="btn-primary">
                进入攻击测试
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/history" className="btn-secondary">
                查看历史记录
              </Link>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
            <HeroStat
              label="实时拦截"
              value={stats.blockedRequests.toLocaleString()}
              hint="当前累计被防线拦截的请求数"
              tone="danger"
            />
            <HeroStat
              label="风险热度"
              value={`${Math.round(stats.attackSuccessRate * 100)}%`}
              hint="攻击成功率越高，越需要尽快回归"
              tone="warning"
            />
            <HeroStat
              label="防御韧性"
              value={`${Math.round(stats.defenseSuccessRate * 100)}%`}
              hint="反映防护策略当前有效性"
              tone="success"
            />
          </div>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {overview.map((item) => (
          <MetricCard
            key={item.label}
            icon={item.icon}
            label={item.label}
            value={item.value}
            hint={item.hint}
            tone={item.tone}
          />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="card">
          <PanelHeader
            title="风险信号"
            description="把当前应该优先注意的几项信息做成可读的简短结论。"
          />
          <InsightList items={signalItems} />
        </section>

        <InfoCallout
          title="下一步建议"
          description="如果攻击成功率升高，优先进入攻击测试页复刻案例；如果防御成功率下降，优先查看防御日志确认是哪一层失效。"
          icon={Sparkles}
          cta={
            <div className="space-y-3">
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
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="card">
          <PanelHeader
            title="近期攻击事件"
            description="只保留最有用的信息：类型、结果和触发时间。"
          />

          {loading ? (
            <div className="flex min-h-[220px] items-center justify-center">
              <div className="spinner-lg" />
            </div>
          ) : recentAttacks.length === 0 ? (
            <div className="panel-muted flex min-h-[220px] items-center justify-center text-sm text-graphite-500">
              目前没有新的攻击事件。
            </div>
          ) : (
            <div className="space-y-3">
              {recentAttacks.slice(0, 5).map((attack, index) => (
                <motion.div
                  key={`${attack.type}-${index}`}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  whileHover={{ scale: 1.015, x: 2, boxShadow: 'var(--shadow-soft)' }}
                  transition={{ delay: index * 0.04, duration: 0.2 }}
                  className="rounded-[18px] border border-graphite-200/70 bg-white/75 dark:bg-graphite-100/40 px-4 py-3 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold text-graphite-900">
                        {attack.type || '未知攻击类型'}
                      </p>
                      <p className="mt-1 text-xs text-graphite-500">
                        {(attack.prompt || '无提示词内容').slice(0, 64)}
                      </p>
                    </div>
                    <div className="space-y-2 text-right">
                      <span className={`badge ${attack.success ? 'badge-danger' : 'badge-success'}`}>
                        {attack.success ? '攻击成功' : '已拦截'}
                      </span>
                      <p className="text-xs text-graphite-400">{formatRelativeTime(attack.created_at || new Date())}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </section>

        <section className="card">
          <PanelHeader
            title="防御日志快照"
            description="帮助判断当前是输入过滤、输出过滤还是其他策略在承压。"
          />

          {loading ? (
            <div className="flex min-h-[220px] items-center justify-center">
              <div className="spinner-lg" />
            </div>
          ) : defenseLogs.length === 0 ? (
            <div className="panel-muted flex min-h-[220px] items-center justify-center text-sm text-graphite-500">
              暂无防御日志，等待新的请求进入。
            </div>
          ) : (
            <div className="space-y-3">
              {defenseLogs.slice(0, 5).map((log, index) => (
                <motion.div
                  key={`${log.defense_type}-${index}`}
                  initial={{ opacity: 0, x: 8 }}
                  animate={{ opacity: 1, x: 0 }}
                  whileHover={{ scale: 1.015, x: -2, boxShadow: 'var(--shadow-soft)' }}
                  transition={{ delay: index * 0.04, duration: 0.2 }}
                  className="rounded-[18px] border border-graphite-200/70 bg-white/75 dark:bg-graphite-100/40 px-4 py-3 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold text-graphite-900">
                        {log.defense_type || '防御模块'}
                      </p>
                      <p className="mt-1 text-xs text-graphite-500">
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
      </div>

      <section className="card">
        <PanelHeader
          title="快捷入口"
          description="把常用路径放在首页，减少多层导航查找。"
        />
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <Link to="/owasp"><QuickLink label="OWASP 测试" description="用标准化风险类目做专项验证。" /></Link>
          <Link to="/redteam"><QuickLink label="红队演练" description="按更接近真实攻击链的方式复测。" /></Link>
          <Link to="/benchmark"><QuickLink label="基准评测" description="对比不同模型或数据集表现。" /></Link>
          <Link to="/reports"><QuickLink label="评估报告" description="沉淀结果，用于分享与复盘。" /></Link>
        </div>
      </section>
    </div>
  )
}
