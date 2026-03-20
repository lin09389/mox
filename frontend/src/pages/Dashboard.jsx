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
  Legend
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
  TrendingDown
} from 'lucide-react'

const COLORS = ['#ef4444', '#22c55e', '#f59e0b', '#a855f7']

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.12 }
  }
}

const item = {
  hidden: { opacity: 0, y: 25 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5 } }
}

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="card-premium !p-3 !shadow-hard">
        <p className="text-sm font-semibold text-dark-900 mb-1">{label}</p>
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
      color: 'danger',
      gradient: 'from-danger-500 to-orange-500',
      bg: 'bg-danger-100',
      textColor: 'text-danger-600',
      statType: 'danger'
    },
    {
      label: '成功攻击',
      value: stats.successful_attacks,
      icon: AlertTriangle,
      color: 'warning',
      gradient: 'from-warning-500 to-danger-500',
      bg: 'bg-warning-100',
      textColor: 'text-warning-600',
      statType: 'danger',
      percentage: `${((stats.successful_attacks / stats.total_attacks) * 100 || 0).toFixed(1)}% 成功率`
    },
    {
      label: '总防御次数',
      value: stats.total_defenses,
      icon: ShieldCheck,
      color: 'primary',
      gradient: 'from-primary-500 to-secondary-500',
      bg: 'bg-primary-100',
      textColor: 'text-primary-600',
      statType: 'primary'
    },
    {
      label: '成功拦截',
      value: stats.blocked_attacks,
      icon: CheckCircle2,
      color: 'success',
      gradient: 'from-success-500 to-primary-500',
      bg: 'bg-success-100',
      textColor: 'text-success-600',
      statType: 'success',
      percentage: `${((stats.blocked_attacks / stats.total_defenses) * 100 || 0).toFixed(1)}% 拦截率`
    }
  ]

  return (
    <motion.div 
      variants={container}
      initial="hidden"
      animate="show"
      className="space-y-8"
    >
      <motion.div variants={item}>
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-600 rounded-xl flex items-center justify-center shadow-glow-primary">
            <TrendingUp className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold text-dark-900 tracking-tight">安全概览</h1>
            <p className="text-dark-500">实时监控您的模型安全状态</p>
          </div>
        </div>
      </motion.div>

      <motion.div variants={item} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((stat, idx) => {
          const Icon = stat.icon
          return (
            <motion.div
              key={idx}
              whileHover={{ scale: 1.02, y: -4 }}
              transition={{ type: 'spring', stiffness: 300 }}
              className="card-premium card-hover glow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`w-14 h-14 ${stat.bg} rounded-2xl flex items-center justify-center shadow-soft`}>
                  <Icon className={`w-7 h-7 ${stat.textColor}`} />
                </div>
                <motion.div
                  animate={{ rotate: [0, 10, -10, 0] }}
                  transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
                >
                  <TrendingUp className={`w-5 h-5 ${stat.textColor} opacity-60`} />
                </motion.div>
              </div>
              
              <div>
                <p className="text-sm font-medium text-dark-500 mb-1">{stat.label}</p>
                <p className={`text-4xl font-extrabold bg-gradient-to-r ${stat.gradient} bg-clip-text text-transparent`}>
                  {stat.value.toLocaleString()}
                </p>
              </div>

              {stat.percentage && (
                <div className="mt-4 pt-3 border-t border-dark-100/60">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${stat.statType === 'danger' ? 'bg-danger-500' : 'bg-success-500'}`} />
                    <span className={`text-sm font-semibold ${stat.textColor}`}>
                      {stat.percentage}
                    </span>
                  </div>
                </div>
              )}

              <div className="mt-4">
                <div className="progress-bar">
                  <div 
                    className={`h-full bg-gradient-to-r ${stat.gradient} rounded-full transition-all duration-1000`}
                    style={{ 
                      width: stat.percentage 
                        ? `${parseFloat(stat.percentage)}%` 
                        : '100%' 
                    }}
                  />
                </div>
              </div>
            </motion.div>
          )
        })}
      </motion.div>

      <motion.div variants={item} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card-premium lg:col-span-1">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-lg font-bold text-dark-900">攻击成功率</h3>
            <div className="w-8 h-8 bg-danger-100 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-4 h-4 text-danger-600" />
            </div>
          </div>
          <div className="relative h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={attackData}
                  cx="50%"
                  cy="50%"
                  innerRadius={65}
                  outerRadius={95}
                  paddingAngle={6}
                  dataKey="value"
                >
                  {attackData.map((_, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={COLORS[index]} 
                      stroke="white"
                      strokeWidth={3}
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center">
                <p className="text-3xl font-extrabold text-danger-600">
                  {((stats.successful_attacks / stats.total_attacks) * 100 || 0).toFixed(0)}%
                </p>
                <p className="text-xs text-dark-500 font-medium">成功率</p>
              </div>
            </div>
          </div>
          <div className="flex justify-center gap-6 mt-4">
            {attackData.map((entry, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full" style={{ backgroundColor: COLORS[idx] }} />
                <span className="text-sm font-semibold text-dark-700">
                  {entry.name}: <span className="text-dark-900">{entry.value}</span>
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="card-premium lg:col-span-1">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-lg font-bold text-dark-900">防御拦截统计</h3>
            <div className="w-8 h-8 bg-success-100 rounded-lg flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 text-success-600" />
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={defenseData}>
                <XAxis 
                  dataKey="name" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 13, fontWeight: 600, fill: '#64748b' }}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 12, fill: '#94a3b8' }}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(14, 165, 233, 0.05)' }} />
                <Bar 
                  dataKey="value" 
                  radius={[12, 12, 4, 4]}
                  barSize={50}
                >
                  {defenseData.map((_, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={index === 0 ? 'url(#colorBlocked)' : 'url(#colorAllowed)'} 
                    />
                  ))}
                </Bar>
                <defs>
                  <linearGradient id="colorBlocked" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22c55e" />
                    <stop offset="100%" stopColor="#16a34a" />
                  </linearGradient>
                  <linearGradient id="colorAllowed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f59e0b" />
                    <stop offset="100%" stopColor="#d97706" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card-premium lg:col-span-1">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-lg font-bold text-dark-900">7天趋势</h3>
            <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-4 h-4 text-primary-600" />
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <XAxis 
                  dataKey="day" 
                  axisLine={false} 
                  tickLine={false} 
                  fontSize={12} 
                  tick={{ fill: '#64748b', fontWeight: 500 }}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  fontSize={12}
                  tick={{ fill: '#94a3b8' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Line 
                  type="monotone" 
                  dataKey="attacks" 
                  stroke="#ef4444" 
                  strokeWidth={3} 
                  dot={{ r: 4, fill: '#ef4444', strokeWidth: 2, stroke: '#fff' }}
                  activeDot={{ r: 6, fill: '#ef4444' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="defenses" 
                  stroke="#22c55e" 
                  strokeWidth={3} 
                  dot={{ r: 4, fill: '#22c55e', strokeWidth: 2, stroke: '#fff' }}
                  activeDot={{ r: 6, fill: '#22c55e' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-6 mt-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-danger-500" />
              <span className="text-sm font-semibold text-dark-600">攻击</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-success-500" />
              <span className="text-sm font-semibold text-dark-600">防御</span>
            </div>
          </div>
        </div>
      </motion.div>

      <motion.div variants={item} className="card-premium">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-600 rounded-xl flex items-center justify-center">
              <Clock className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-dark-900">最近活动</h3>
              <p className="text-sm text-dark-500">最新的安全事件记录</p>
            </div>
          </div>
          <a 
            href="/history" 
            className="inline-flex items-center gap-2 text-sm font-semibold text-primary-600 hover:text-primary-700 transition-colors group"
          >
            查看全部 
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
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
                      <div className="w-16 h-16 bg-dark-100 rounded-full flex items-center justify-center">
                        <History className="w-8 h-8 text-dark-400" />
                      </div>
                      <p className="text-dark-500 font-medium">暂无活动记录</p>
                    </div>
                  </td>
                </tr>
              ) : (
                stats.recent_attacks.map((attack) => (
                  <tr key={attack.id || attack.created_at} className="group">
                    <td className="text-dark-500 font-medium">
                      {new Date(attack.created_at).toLocaleString('zh-CN')}
                    </td>
                    <td>
                      <span className="badge-info">
                        {attack.attack_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="font-semibold text-dark-800">{attack.model_name}</td>
                    <td>
                      {attack.result === 'success' ? (
                        <span className="badge-danger flex items-center gap-1.5">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          攻击成功
                        </span>
                      ) : (
                        <span className="badge-success flex items-center gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5" />
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
