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
import { HeroStat, InfoCallout, InsightList, MetricCard, PageHeader, PanelHeader, QuickLink, animContainer, animItem } from '../components/ui/AppFrame'
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
    <motion.div 
      className="page-shell"
      variants={animContainer}
      initial="hidden"
      animate="show"
    >
      <motion.div variants={animItem}>
        <PageHeader
          eyebrow="SECURITY OVERVIEW"
          title="监控大盘"
          description="全局视角监控风险指标，实时把控平台安全态势。"
          badge={
            <div className="flex items-center gap-2 rounded-full border border-graphite-200 bg-white px-3 py-1.5 text-xs font-medium text-graphite-600 shadow-sm">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-neon-400 opacity-75"></span>
                <span className="relative inline-flex h-2 w-2 rounded-full bg-neon-500"></span>
              </span>
              最近更新 {lastUpdate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </div>
          }
        />
      </motion.div>

      <motion.section variants={animItem} className="hero-panel mb-4">
        <div className="relative z-10 grid gap-8 xl:grid-cols-[1fr_auto]">
          <div className="space-y-6 max-w-2xl">
            <div className="space-y-2">
              <motion.h2 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-graphite-950"
              >
                风险信号实时感知
              </motion.h2>
              <motion.p 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="text-sm sm:text-base text-graphite-600 leading-relaxed"
              >
                主动监控拦截表现与攻击成功率。基于实时数据做出研判，快速定位潜在风险并采取防御措施。
              </motion.p>
            </div>
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="flex flex-wrap items-center gap-4"
            >
              <Link to="/attack" className="btn-primary">
                进入攻击测试
                <ArrowRight className="h-4 w-4 ml-1 transition-transform group-hover:translate-x-1" />
              </Link>
              <Link to="/history" className="btn-secondary">
                查看历史记录
              </Link>
            </motion.div>
          </div>

          <motion.div 
            variants={animContainer}
            initial="hidden"
            animate="show"
            className="flex flex-col sm:flex-row gap-4 xl:w-[400px]"
          >
            <HeroStat
              label="风险热度"
              value={`${Math.round(stats.attackSuccessRate * 100)}%`}
              hint="攻击成功率"
              tone="warning"
            />
            <HeroStat
              label="防御韧性"
              value={`${Math.round(stats.defenseSuccessRate * 100)}%`}
              hint="防护策略有效性"
              tone="success"
            />
          </motion.div>
        </div>
      </motion.section>

      <motion.div variants={animContainer} className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
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
      </motion.div>

      <motion.div variants={animContainer} className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr] mt-2">
        <motion.section variants={animItem} className="card flex flex-col">
          <PanelHeader
            title="风险评估信号"
            description="基于核心指标的自动化分析研判。"
          />
          <div className="flex-1 flex flex-col justify-center">
            <InsightList items={signalItems} />
          </div>
        </motion.section>

        <motion.div variants={animItem}>
          <InfoCallout
            title="专项行动建议"
            description="基于当前风险信号，建议采取以下针对性操作："
            icon={Sparkles}
            cta={
              <motion.div variants={animContainer} initial="hidden" animate="show" className="space-y-3">
                <Link to="/attack" className="block">
                  <QuickLink label="高危复测" description="复刻高风险案例并对比成功分数变化。" />
                </Link>
                <Link to="/defense" className="block">
                  <QuickLink label="规则排查" description="确认输入过滤和输出审查是否漏检。" />
                </Link>
                <Link to="/history" className="block">
                  <QuickLink label="长线追踪" description="查看近期异常事件是否具有持续性。" />
                </Link>
              </motion.div>
            }
          />
        </motion.div>
      </motion.div>

      <motion.div variants={animContainer} className="grid gap-6 xl:grid-cols-2 mt-2">
        <motion.section variants={animItem} className="card">
          <PanelHeader
            title="近期安全事件"
            description="最新发生的攻击行为记录。"
            action={
              <Link to="/history" className="text-sm font-medium text-electric-700 hover:text-electric-700 flex items-center gap-1 group">
                全部事件 <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
              </Link>
            }
          />

          {loading ? (
            <div className="flex min-h-[260px] items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-graphite-200 border-t-electric-600" />
            </div>
          ) : recentAttacks.length === 0 ? (
            <div className="flex min-h-[260px] items-center justify-center rounded-xl border border-dashed border-graphite-200 bg-graphite-50/50">
              <p className="text-sm text-graphite-500">目前没有新的攻击事件记录</p>
            </div>
          ) : (
            <motion.div variants={animContainer} initial="hidden" animate="show" className="space-y-3">
              {recentAttacks.slice(0, 5).map((attack, index) => (
                <motion.div
                  key={`${attack.type}-${index}`}
                  variants={animItem}
                  whileHover={{ scale: 1.01, backgroundColor: 'rgba(255,255,255,1)' }}
                  className="group flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border border-white/60 bg-white/40 px-5 py-4 transition-colors hover:border-white hover:shadow-soft backdrop-blur-sm cursor-default"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-bold text-graphite-900 truncate group-hover:text-electric-700 transition-colors">
                      {attack.type || '未知攻击类型'}
                    </p>
                    <p className="mt-1.5 text-xs font-medium text-graphite-500 truncate">
                      {(attack.prompt || '无提示词内容')}
                    </p>
                  </div>
                  <div className="flex items-center sm:flex-col sm:items-end sm:justify-center gap-2.5 shrink-0">
                    <span className={`badge ${attack.success ? 'badge-danger' : 'badge-success'}`}>
                      {attack.success ? '攻击成功' : '已拦截'}
                    </span>
                    <p className="text-[11px] text-graphite-600 font-semibold tracking-wide">
                      {formatRelativeTime(attack.created_at || new Date())}
                    </p>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}
        </motion.section>

        <motion.section variants={animItem} className="card">
          <PanelHeader
            title="防御引擎日志"
            description="各防护模块的实时检测状态。"
            action={
              <Link to="/defense" className="text-sm font-medium text-electric-700 hover:text-electric-700 flex items-center gap-1 group">
                防御设置 <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
              </Link>
            }
          />

          {loading ? (
            <div className="flex min-h-[260px] items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-graphite-200 border-t-electric-600" />
            </div>
          ) : defenseLogs.length === 0 ? (
            <div className="flex min-h-[260px] items-center justify-center rounded-xl border border-dashed border-graphite-200 bg-graphite-50/50">
              <p className="text-sm text-graphite-500">暂无防御拦截日志</p>
            </div>
          ) : (
            <motion.div variants={animContainer} initial="hidden" animate="show" className="space-y-3">
              {defenseLogs.slice(0, 5).map((log, index) => (
                <motion.div
                  key={`${log.defense_type}-${index}`}
                  variants={animItem}
                  whileHover={{ scale: 1.01, backgroundColor: 'rgba(255,255,255,1)' }}
                  className="group flex items-center justify-between gap-4 rounded-xl border border-white/60 bg-white/40 px-5 py-4 transition-colors hover:border-white hover:shadow-soft backdrop-blur-sm cursor-default"
                >
                  <div className="flex items-center gap-4 min-w-0">
                    <motion.div 
                      whileHover={{ rotate: 15, scale: 1.15 }}
                      transition={{ type: 'spring' }}
                      className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border bg-white shadow-sm ${log.blocked ? 'border-lava-100 text-lava-600 shadow-lava-500/10' : 'border-neon-100 text-neon-600 shadow-neon-500/10'}`}
                    >
                      {log.blocked ? <ShieldAlert className="h-5 w-5" /> : <ShieldCheck className="h-5 w-5" />}
                    </motion.div>
                    <div className="min-w-0">
                      <p className="text-sm font-bold text-graphite-900 truncate group-hover:text-electric-700 transition-colors">
                        {log.defense_type || '防御模块'}
                      </p>
                      <p className="text-xs font-medium text-graphite-500 mt-1">
                        置信度: <span className="font-bold text-graphite-700">{(Number(log.confidence || 0) * 100).toFixed(1)}%</span>
                      </p>
                    </div>
                  </div>
                  <span className={`badge shrink-0 ${log.blocked ? 'badge-danger' : 'badge-success'}`}>
                    {log.blocked ? '触发拦截' : '检测通过'}
                  </span>
                </motion.div>
              ))}
            </motion.div>
          )}
        </motion.section>
      </motion.div>
    </motion.div>
  )
}

