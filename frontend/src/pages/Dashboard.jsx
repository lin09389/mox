import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts'
import toast from 'react-hot-toast'
import { statsApi } from '../api'
import {
  Zap,
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  TrendingUp,
  Clock,
  History,
} from 'lucide-react'

const COLORS = ['#ef4444', '#22c55e', '#f59e0b', '#a855f7']

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
}

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.16, 1, 0.3, 1] } }
}

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white rounded-md border border-graphite-200/60 p-3 shadow-lifted">
        <p className="text-sm font-semibold text-graphite-900 mb-1">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} className="text-xs" style={{ color: entry.color }}>
            {entry.name}: <span className="font-bold">{entry.value}</span>
          </p>
        ))}
      </div>
    )
  }
  return null
}

export default function Dashboard() {
  const [stats, setStats] = useState({
    total_attacks: 0,
    successful_attacks: 0,
    total_defenses: 0,
    blocked_attacks: 0,
    recent_attacks: [],
  })

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const { data } = await statsApi.getOverview()
      setStats(data)
    } catch (error) {
      setStats({
        total_attacks: 156,
        successful_attacks: 42,
        total_defenses: 892,
        blocked_attacks: 734,
        recent_attacks: [
          { id: 1, attack_type: 'prompt_injection', model_name: 'gpt-4', result: 'success', created_at: new Date().toISOString() },
          { id: 2, attack_type: 'jailbreak', model_name: 'claude-3', result: 'failure', created_at: new Date().toISOString() },
          { id: 3, attack_type: 'gcg', model_name: 'gpt-4', result: 'success', created_at: new Date().toISOString() },
        ]
      })
    }
  }

  const attackData = [
    { name: '成功', value: stats.successful_attacks },
    { name: '失败', value: stats.total_attacks - stats.successful_attacks },
  ]

  const defenseData = [
    { name: '拦截', value: stats.blocked_attacks },
    { name: '放行', value: stats.total_defenses - stats.blocked_attacks },
  ]

  const trendData = [
    { day: '周一', attacks: 12, defenses: 45 },
    { day: '周二', attacks: 19, defenses: 52 },
    { day: '周三', attacks: 15, defenses: 48 },
    { day: '周四', attacks: 22, defenses: 61 },
    { day: '周五', attacks: 18, defenses: 55 },
    { day: '周六', attacks: 8, defenses: 32 },
    { day: '周日', attacks: 10, defenses: 38 },
  ]

  const statCards = [
    {
      label: '总攻击次数',
      value: stats.total_attacks,
      icon: Zap,
      color: 'lave',
      percentage: `${((stats.successful_attacks / stats.total_attacks) * 100 || 0).toFixed(1)}% 成功率`
    },
    {
      label: '成功攻击',
      value: stats.successful_attacks,
      icon: AlertTriangle,
      color: 'amber',
      percentage: '突破防护'
    },
    {
      label: '总防御次数',
      value: stats.total_defenses,
      icon: ShieldCheck,
      color: 'electric',
      percentage: null
    },
    {
      label: '成功拦截',
      value: stats.blocked_attacks,
      icon: CheckCircle2,
      color: 'neon',
      percentage: `${((stats.blocked_attacks / stats.total_defenses) * 100 || 0).toFixed(1)}% 拦截率`
    }
  ]

  const colorMap = {
    lave: { bg: 'bg-lava-100', text: 'text-lava-600', border: 'border-lava-200/70' },
    amber: { bg: 'bg-amber-100', text: 'text-amber-600', border: 'border-amber-200/70' },
    electric: { bg: 'bg-electric-100', text: 'text-electric-600', border: 'border-electric-200/70' },
    neon: { bg: 'bg-neon-100', text: 'text-neon-600', border: 'border-neon-200/70' },
  }

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      {/* 页面标题 */}
      <motion.div variants={item}>
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 bg-electric-100 rounded-lg flex items-center justify-center border border-electric-200/70">
            <TrendingUp className="w-5.5 h-5.5 text-electric-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold font-display text-graphite-900 tracking-tight">安全概览</h1>
            <p className="text-sm text-graphite-500">实时监控您的模型安全状态</p>
          </div>
        </div>
      </motion.div>

      {/* 统计卡片 */}
      <motion.div variants={item} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, idx) => {
          const Icon = stat.icon
          const colors = colorMap[stat.color]
          return (
            <motion.div
              key={idx}
              variants={item}
              className="card card-hover"
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`w-11 h-11 ${colors.bg} rounded-lg flex items-center justify-center border ${colors.border}`}>
                  <Icon className={`w-5.5 h-5.5 ${colors.text}`} />
                </div>
                <TrendingUp className={`w-4.5 h-4.5 ${colors.text} opacity-50`} />
              </div>
              <div>
                <p className="text-xs text-graphite-500 mb-0.5">{stat.label}</p>
                <p className="text-2xl font-bold font-display text-graphite-900">{stat.value.toLocaleString()}</p>
              </div>
              {stat.percentage && (
                <div className="mt-3 pt-3 border-t border-graphite-200/60">
                  <span className={`text-xs font-medium ${colors.text}`}>{stat.percentage}</span>
                </div>
              )}
            </motion.div>
          )
        })}
      </motion.div>

      {/* 图表区域 */}
      <motion.div variants={item} className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* 攻击成功率 */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-graphite-900">攻击成功率</h3>
            <div className={`w-8 h-8 ${colorMap.lave.bg} rounded-md flex items-center justify-center`}>
              <AlertTriangle className={`w-4 h-4 ${colorMap.lave.text}`} />
            </div>
          </div>
          <div className="relative h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={attackData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {attackData.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index]}
                      stroke="white"
                      strokeWidth={2}
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center">
                <p className="text-2xl font-bold text-graphite-900">
                  {((stats.successful_attacks / stats.total_attacks) * 100 || 0).toFixed(0)}%
                </p>
                <p className="text-[11px] text-graphite-500">成功率</p>
              </div>
            </div>
          </div>
          <div className="flex justify-center gap-5 mt-3">
            {attackData.map((entry, idx) => (
              <div key={idx} className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[idx] }} />
                <span className="text-xs text-graphite-600">
                  {entry.name}: <span className="font-medium text-graphite-900">{entry.value}</span>
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* 防御拦截统计 */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-graphite-900">防御拦截统计</h3>
            <div className={`w-8 h-8 ${colorMap.neon.bg} rounded-md flex items-center justify-center`}>
              <ShieldCheck className={`w-4 h-4 ${colorMap.neon.text}`} />
            </div>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={defenseData}>
                <XAxis
                  dataKey="name"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12, fontWeight: 600, fill: '#71717a' }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11, fill: '#a1a1aa' }}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(14, 165, 233, 0.05)' }} />
                <Bar
                  dataKey="value"
                  radius={[8, 8, 4, 4]}
                  barSize={48}
                >
                  {defenseData.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={index === 0 ? '#22c55e' : '#f59e0b'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 7天趋势 */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-graphite-900">7天趋势</h3>
            <div className={`w-8 h-8 ${colorMap.electric.bg} rounded-md flex items-center justify-center`}>
              <TrendingUp className={`w-4 h-4 ${colorMap.electric.text}`} />
            </div>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <XAxis
                  dataKey="day"
                  axisLine={false}
                  tickLine={false}
                  fontSize={11}
                  tick={{ fill: '#71717a', fontWeight: 500 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  fontSize={11}
                  tick={{ fill: '#a1a1aa' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Line
                  type="monotone"
                  dataKey="attacks"
                  stroke="#ef4444"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#ef4444', strokeWidth: 2, stroke: '#fff' }}
                  activeDot={{ r: 5, fill: '#ef4444' }}
                />
                <Line
                  type="monotone"
                  dataKey="defenses"
                  stroke="#22c55e"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#22c55e', strokeWidth: 2, stroke: '#fff' }}
                  activeDot={{ r: 5, fill: '#22c55e' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-5 mt-2">
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-lava-500" />
              <span className="text-xs text-graphite-600">攻击</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-neon-500" />
              <span className="text-xs text-graphite-600">防御</span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* 最近活动 */}
      <motion.div variants={item} className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-electric-100 rounded-lg flex items-center justify-center border border-electric-200/70">
              <Clock className="w-5 h-5 text-electric-600" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-graphite-900">最近活动</h3>
              <p className="text-xs text-graphite-500">最新的安全事件记录</p>
            </div>
          </div>
          <a
            href="/history"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-electric-600 hover:text-electric-700 transition-colors"
          >
            查看全部
            <ArrowRight className="w-3.5 h-3.5" />
          </a>
        </div>

        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>时间</th>
                <th>攻击类型</th>
                <th>目标模型</th>
                <th>结果</th>
              </tr>
            </thead>
            <tbody>
              {stats.recent_attacks.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center py-12">
                    <div className="flex flex-col items-center gap-2">
                      <div className="w-14 h-14 bg-graphite-100 rounded-full flex items-center justify-center">
                        <History className="w-7 h-7 text-graphite-400" />
                      </div>
                      <p className="text-sm text-graphite-500">暂无活动记录</p>
                    </div>
                  </td>
                </tr>
              ) : (
                stats.recent_attacks.map((attack) => (
                  <tr key={attack.id || attack.created_at} className="group">
                    <td className="text-graphite-500 text-xs font-medium">
                      {new Date(attack.created_at).toLocaleString('zh-CN')}
                    </td>
                    <td>
                      <span className="badge badge-info">
                        {attack.attack_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="font-medium text-graphite-800 text-xs">{attack.model_name}</td>
                    <td>
                      {attack.result === 'success' ? (
                        <span className="badge badge-danger flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3" />
                          攻击成功
                        </span>
                      ) : (
                        <span className="badge badge-success flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          攻击失败
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </motion.div>
    </motion.div>
  )
}
