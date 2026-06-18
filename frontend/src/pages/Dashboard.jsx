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
  CartesianGrid,
} from 'recharts'
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
  Activity,
  ServerCrash,
  Database
} from 'lucide-react'

// Custom Premium Colors for Charts
const COLORS = {
  danger: '#ef4444',
  success: '#10b981',
  warning: '#f59e0b',
  primary: '#06b6d4',
  purple: '#8b5cf6',
  slate: '#64748b'
}

const PIE_COLORS = [COLORS.danger, COLORS.success]

import { containerVariants, itemVariants } from '../utils/animations'

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="card p-3 shadow-lifted border-[var(--border-glass-strong)] min-w-[140px]">
        <p className="text-sm font-bold text-[var(--text-main)] mb-2 pb-2 border-b border-[var(--border-glass)]">{label}</p>
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center justify-between gap-4 mt-1">
            <span className="text-xs font-medium" style={{ color: entry.color }}>
              {entry.name}
            </span>
            <span className="font-bold font-mono text-[var(--text-main)]">{entry.value}</span>
          </div>
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

  const [isLoading, setIsLoading] = useState(true)

  const loadStats = async () => {
    setIsLoading(true)
    try {
      const { data } = await statsApi.getOverview()
      setStats(data)
    } catch (error) {
      // Fallback Demo Data
      setTimeout(() => {
        setStats({
          total_attacks: 2456,
          successful_attacks: 342,
          total_defenses: 8992,
          blocked_attacks: 8650,
          recent_attacks: [
            { id: 1, attack_type: 'prompt_injection', model_name: 'gpt-4-turbo', result: 'success', created_at: new Date(Date.now() - 1000 * 60 * 5).toISOString() },
            { id: 2, attack_type: 'jailbreak', model_name: 'claude-3-opus', result: 'failure', created_at: new Date(Date.now() - 1000 * 60 * 15).toISOString() },
            { id: 3, attack_type: 'gcg', model_name: 'gpt-4-turbo', result: 'success', created_at: new Date(Date.now() - 1000 * 60 * 42).toISOString() },
            { id: 4, attack_type: 'data_extraction', model_name: 'llama-3-70b', result: 'failure', created_at: new Date(Date.now() - 1000 * 60 * 120).toISOString() },
          ]
        })
        setIsLoading(false)
      }, 800)
    }
  }

  const attackData = [
    { name: '成功突破', value: stats.successful_attacks },
    { name: '防御拦截', value: stats.total_attacks - stats.successful_attacks },
  ]

  const defenseData = [
    { name: '拦截威胁', value: stats.blocked_attacks },
    { name: '正常放行', value: stats.total_defenses - stats.blocked_attacks },
  ]

  const trendData = [
    { day: 'Mon', attacks: 120, defenses: 450 },
    { day: 'Tue', attacks: 190, defenses: 520 },
    { day: 'Wed', attacks: 150, defenses: 480 },
    { day: 'Thu', attacks: 220, defenses: 610 },
    { day: 'Fri', attacks: 180, defenses: 550 },
    { day: 'Sat', attacks: 80, defenses: 320 },
    { day: 'Sun', attacks: 100, defenses: 380 },
  ]

  const statCards = [
    {
      label: '累计攻击请求',
      value: stats.total_attacks,
      icon: Zap,
      colorClass: 'text-cyan-500',
      bgClass: 'bg-cyan-500/10 border-cyan-500/20',
      glow: 'shadow-[0_0_15px_rgba(6,182,212,0.15)]',
      trend: '+12.5%',
      trendUp: true
    },
    {
      label: '高危突破事件',
      value: stats.successful_attacks,
      icon: AlertTriangle,
      colorClass: 'text-rose-500',
      bgClass: 'bg-rose-500/10 border-rose-500/20',
      glow: 'shadow-[0_0_15px_rgba(244,63,94,0.15)]',
      trend: '+4.2%',
      trendUp: true
    },
    {
      label: '安全防御总数',
      value: stats.total_defenses,
      icon: ShieldCheck,
      colorClass: 'text-emerald-500',
      bgClass: 'bg-emerald-500/10 border-emerald-500/20',
      glow: 'shadow-[0_0_15px_rgba(16,185,129,0.15)]',
      trend: '+24.8%',
      trendUp: true
    },
    {
      label: '成功拦截次数',
      value: stats.blocked_attacks,
      icon: CheckCircle2,
      colorClass: 'text-indigo-500',
      bgClass: 'bg-indigo-500/10 border-indigo-500/20',
      glow: 'shadow-[0_0_15px_rgba(99,102,241,0.15)]',
      percentage: `${((stats.blocked_attacks / stats.total_defenses) * 100 || 0).toFixed(1)}%`
    }
  ]

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-[var(--border-glass)] border-t-[var(--accent-primary)] rounded-full animate-spin"></div>
          <p className="text-[var(--text-muted)] font-medium animate-pulse">正在同步安全数据矩阵...</p>
        </div>
      </div>
    )
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="page-shell"
    >
      {/* Premium Hero Title */}
      <motion.div variants={itemVariants} className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-2">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--bg-glass)] border border-[var(--border-glass)] text-xs font-bold text-[var(--accent-primary)] uppercase tracking-widest mb-3">
            <Activity className="w-3.5 h-3.5" /> Core Metrics
          </div>
          <h1 className="text-3xl md:text-4xl font-bold font-display text-[var(--text-main)] tracking-tight">
            安全监控<span className="text-gradient">大盘</span>
          </h1>
          <p className="text-[var(--text-muted)] mt-2 font-medium max-w-xl">
            实时分析AI模型所面临的对抗攻击请求与系统防御效能，为您提供全方位的态势感知。
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button className="btn-secondary">
            <ServerCrash className="w-4 h-4" /> 导出分析
          </button>
          <button className="btn-primary">
            <Zap className="w-4 h-4" /> 开启主动防御
          </button>
        </div>
      </motion.div>

      {/* KPI Cards Grid */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((stat, idx) => {
          const Icon = stat.icon
          return (
            <div key={idx} className={`card card-hover flex flex-col justify-between h-[160px] ${stat.glow}`}>
              <div className="flex justify-between items-start">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border ${stat.bgClass}`}>
                  <Icon className={`w-6 h-6 ${stat.colorClass}`} />
                </div>
                {stat.trend && (
                  <div className={`flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-md ${stat.trendUp ? 'bg-rose-500/10 text-rose-500' : 'bg-emerald-500/10 text-emerald-500'}`}>
                    <TrendingUp className="w-3 h-3" /> {stat.trend}
                  </div>
                )}
                {stat.percentage && (
                  <div className="flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-md bg-indigo-500/10 text-indigo-500">
                    {stat.percentage} 拦截率
                  </div>
                )}
              </div>
              <div>
                <p className="text-sm font-semibold text-[var(--text-muted)] mb-1">{stat.label}</p>
                <div className="text-3xl font-bold font-mono tracking-tight text-[var(--text-main)]">
                  {stat.value.toLocaleString()}
                </div>
              </div>
            </div>
          )
        })}
      </motion.div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        
        {/* Pie Chart: Attack Success Rate */}
        <motion.div variants={itemVariants} className="card flex flex-col h-[380px]">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-base font-bold font-display text-[var(--text-main)]">威胁穿透分析</h3>
            <div className="p-1.5 rounded-lg bg-rose-500/10">
              <AlertTriangle className="w-4 h-4 text-rose-500" />
            </div>
          </div>
          <div className="flex-1 relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={attackData}
                  cx="50%"
                  cy="50%"
                  innerRadius={70}
                  outerRadius={100}
                  paddingAngle={8}
                  dataKey="value"
                  stroke="none"
                  cornerRadius={6}
                >
                  {attackData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-4xl font-bold font-display text-[var(--text-main)]">
                {((stats.successful_attacks / stats.total_attacks) * 100 || 0).toFixed(1)}<span className="text-xl text-[var(--text-muted)]">%</span>
              </span>
              <span className="text-xs font-semibold uppercase tracking-widest text-[var(--text-muted)] mt-1">穿透率</span>
            </div>
          </div>
          <div className="flex justify-center gap-6 mt-2 pb-2">
            {attackData.map((entry, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full shadow-sm" style={{ backgroundColor: PIE_COLORS[idx] }} />
                <span className="text-sm font-medium text-[var(--text-muted)]">{entry.name}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Line Chart: 7-Day Trend */}
        <motion.div variants={itemVariants} className="card lg:col-span-2 flex flex-col h-[380px]">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-base font-bold font-display text-[var(--text-main)]">7日攻防态势趋势</h3>
            <div className="flex gap-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]" />
                <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">攻击</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">防御</span>
              </div>
            </div>
          </div>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-glass)" />
                <XAxis 
                  dataKey="day" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: 'var(--text-muted)', fontSize: 12, fontWeight: 600 }} 
                  dy={10}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: 'var(--text-muted)', fontSize: 12 }} 
                />
                <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'var(--border-glass-strong)', strokeWidth: 2, strokeDasharray: '5 5' }} />
                <Line 
                  type="monotone" 
                  dataKey="attacks" 
                  name="攻击次数"
                  stroke={COLORS.danger} 
                  strokeWidth={3}
                  dot={{ r: 4, fill: 'var(--bg-main)', stroke: COLORS.danger, strokeWidth: 2 }}
                  activeDot={{ r: 6, fill: COLORS.danger, stroke: 'var(--bg-main)' }}
                  animationDuration={1500}
                />
                <Line 
                  type="monotone" 
                  dataKey="defenses" 
                  name="防御次数"
                  stroke={COLORS.success} 
                  strokeWidth={3}
                  dot={{ r: 4, fill: 'var(--bg-main)', stroke: COLORS.success, strokeWidth: 2 }}
                  activeDot={{ r: 6, fill: COLORS.success, stroke: 'var(--bg-main)' }}
                  animationDuration={1500}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* Recent Activity Table */}
      <motion.div variants={itemVariants} className="card p-0 overflow-hidden">
        <div className="p-5 border-b border-[var(--border-glass)] flex items-center justify-between bg-[var(--bg-glass-strong)]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <History className="w-5 h-5 text-indigo-500" />
            </div>
            <div>
              <h3 className="text-base font-bold font-display text-[var(--text-main)]">实时安全事件日志</h3>
              <p className="text-xs text-[var(--text-muted)] font-medium">最近发生的攻击尝试与系统响应</p>
            </div>
          </div>
          <button className="btn-ghost text-xs">
            查看完整日志 <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="table-container">
          <table className="table w-full">
            <thead>
              <tr>
                <th>时间戳</th>
                <th>攻击向量</th>
                <th>目标模型引擎</th>
                <th>执行结果</th>
              </tr>
            </thead>
            <tbody>
              {stats.recent_attacks.length === 0 ? (
                <tr>
                  <td colSpan={4} className="text-center py-16">
                    <div className="flex flex-col items-center gap-3">
                      <div className="w-16 h-16 rounded-full bg-[var(--bg-glass)] border border-[var(--border-glass)] flex items-center justify-center">
                        <ShieldCheck className="w-8 h-8 text-[var(--text-muted)] opacity-50" />
                      </div>
                      <p className="text-sm font-semibold text-[var(--text-muted)]">暂无最新安全事件</p>
                    </div>
                  </td>
                </tr>
              ) : (
                stats.recent_attacks.map((attack, i) => (
                  <motion.tr 
                    key={attack.id || i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + i * 0.1 }}
                    className="group"
                  >
                    <td className="font-mono text-xs text-[var(--text-muted)] font-medium">
                      {new Date(attack.created_at).toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' })}
                    </td>
                    <td>
                      <span className="badge badge-neutral bg-[var(--bg-glass-strong)] border-[var(--border-glass-strong)]">
                        {attack.attack_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] flex items-center justify-center">
                          <Database className="w-3 h-3 text-[var(--text-muted)]" />
                        </div>
                        <span className="font-bold text-[var(--text-main)] text-sm">{attack.model_name}</span>
                      </div>
                    </td>
                    <td>
                      {attack.result === 'success' ? (
                        <span className="badge badge-danger">
                          <AlertTriangle className="w-3 h-3" /> 突破防护
                        </span>
                      ) : (
                        <span className="badge badge-success">
                          <ShieldCheck className="w-3 h-3" /> 成功拦截
                        </span>
                      )}
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </motion.div>

    </motion.div>
  )
}
