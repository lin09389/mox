import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Shield,
  AlertTriangle,
  Activity,
  Lock,
  Eye,
  Zap,
  CheckCircle,
  XCircle,
  TrendingUp,
  Server,
  Clock,
  ArrowRight
} from 'lucide-react'
import { getStats, getRecentAttacks, getDefenseLogs } from '../api/security'

export default function SecurityDashboard() {
  const [stats, setStats] = useState({
    totalRequests: 0,
    blockedRequests: 0,
    attackSuccessRate: 0,
    defenseSuccessRate: 0,
  })
  const [recentAttacks, setRecentAttacks] = useState([])
  const [defenseLogs, setDefenseLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(new Date())

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      const [statsData, attacksData, logsData] = await Promise.all([
        getStats(),
        getRecentAttacks(),
        getDefenseLogs()
      ])
      setStats(statsData)
      setRecentAttacks(attacksData)
      setDefenseLogs(logsData)
      setLastUpdate(new Date())
    } catch (error) {
      console.error('加载仪表盘数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <div className="spinner-lg" />
        <span className="text-sm text-graphite-500">正在加载仪表盘数据...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold font-display text-graphite-900 tracking-tight">
            安全仪表盘
          </h1>
          <p className="text-sm text-graphite-500 mt-0.5">实时监控您的 LLM 应用安全状态</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-graphite-400">
          <Clock className="w-3.5 h-3.5" />
          <span>最后更新: {lastUpdate.toLocaleTimeString()}</span>
        </div>
      </motion.div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Activity className="w-5 h-5" />}
          label="总请求数"
          value={stats.totalRequests.toLocaleString()}
          subLabel="今日请求总量"
          color="electric"
        />
        <StatCard
          icon={<Shield className="w-5 h-5" />}
          label="拦截请求"
          value={stats.blockedRequests.toLocaleString()}
          subLabel="恶意请求已拦截"
          color="lava"
        />
        <StatCard
          icon={<Lock className="w-5 h-5" />}
          label="防御成功率"
          value={`${(stats.defenseSuccessRate * 100).toFixed(1)}%`}
          subLabel="安全防护有效"
          color="neon"
        />
        <StatCard
          icon={<AlertTriangle className="w-5 h-5" />}
          label="攻击成功率"
          value={`${(stats.attackSuccessRate * 100).toFixed(1)}%`}
          subLabel="需要关注的比例"
          color="amber"
        />
      </div>

      {/* 图表区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* 请求分布 */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card"
        >
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-base font-semibold text-graphite-900 flex items-center gap-2">
              <Server className="w-4.5 h-4.5 text-graphite-400" />
              请求分布
            </h3>
          </div>
          <div className="flex items-center justify-center gap-10 py-6">
            <div className="text-center">
              <div className="text-4xl font-bold font-display text-neon-600">
                {stats.totalRequests - stats.blockedRequests}
              </div>
              <div className="text-xs text-graphite-500 mt-1">已放行</div>
            </div>
            <div className="text-2xl text-graphite-300 font-light">/</div>
            <div className="text-center">
              <div className="text-4xl font-bold font-display text-lava-600">
                {stats.blockedRequests}
              </div>
              <div className="text-xs text-graphite-500 mt-1">已拦截</div>
            </div>
          </div>
          <div className="flex justify-center gap-6 mt-2">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-neon-500" />
              <span className="text-xs text-graphite-600">正常请求</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-lava-500" />
              <span className="text-xs text-graphite-600">恶意请求</span>
            </div>
          </div>
        </motion.div>

        {/* 防御活动趋势 */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="card"
        >
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-base font-semibold text-graphite-900 flex items-center gap-2">
              <TrendingUp className="w-4.5 h-4.5 text-graphite-400" />
              防御活动趋势
            </h3>
          </div>
          <div className="space-y-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-10 text-[11px] text-graphite-400">T-{6 - i}</div>
                <div className="flex-1 h-5 bg-graphite-100 rounded overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.random() * 60 + 20}%` }}
                    transition={{ duration: 0.8, delay: i * 0.1 }}
                    className={`h-full ${i % 3 === 0 ? 'bg-lava-500' : 'bg-neon-500'} rounded`}
                  />
                </div>
                <span className={`text-[11px] font-medium ${i % 3 === 0 ? 'text-lava-600' : 'text-neon-600'}`}>
                  {i % 3 === 0 ? '拦截' : '放行'}
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* 详细列表 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* 最近攻击记录 */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold flex items-center gap-2">
              <AlertTriangle className="w-4.5 h-4.5 text-lava-500" />
              最近攻击记录
            </h3>
            <span className="text-xs text-graphite-400">实时监控</span>
          </div>
          <div className="space-y-2.5">
            {recentAttacks.length === 0 ? (
              <div className="text-center py-10">
                <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-neon-50 flex items-center justify-center">
                  <Shield className="w-6 h-6 text-neon-500" />
                </div>
                <p className="text-sm font-medium text-graphite-700">暂无攻击记录</p>
                <p className="text-xs text-graphite-400 mt-0.5">系统运行安全</p>
              </div>
            ) : (
              recentAttacks.slice(0, 5).map((attack, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-center justify-between p-3 rounded-md bg-graphite-50/60 border border-graphite-200/50"
                >
                  <div className="flex items-center gap-3">
                    {attack.success ? (
                      <XCircle className="w-4.5 h-4.5 text-lava-500 flex-shrink-0" />
                    ) : (
                      <CheckCircle className="w-4.5 h-4.5 text-neon-500 flex-shrink-0" />
                    )}
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-graphite-900 truncate">
                        {attack.type || '未知攻击类型'}
                      </p>
                      <p className="text-xs text-graphite-400 truncate">
                        {attack.prompt?.substring(0, 30) || '无内容'}...
                      </p>
                    </div>
                  </div>
                  <span className={`badge flex-shrink-0 ${attack.success ? 'badge-danger' : 'badge-success'}`}>
                    {attack.success ? '攻击成功' : '已拦截'}
                  </span>
                </motion.div>
              ))
            )}
          </div>
        </motion.div>

        {/* 防御日志 */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="card"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold flex items-center gap-2">
              <Zap className="w-4.5 h-4.5 text-electric-500" />
              防御日志
            </h3>
            <span className="text-xs text-graphite-400">实时更新</span>
          </div>
          <div className="space-y-2.5">
            {defenseLogs.length === 0 ? (
              <div className="text-center py-10">
                <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-electric-50 flex items-center justify-center">
                  <Activity className="w-6 h-6 text-electric-500" />
                </div>
                <p className="text-sm font-medium text-graphite-700">暂无防御日志</p>
                <p className="text-xs text-graphite-400 mt-0.5">等待请求处理</p>
              </div>
            ) : (
              defenseLogs.slice(0, 5).map((log, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-center justify-between p-3 rounded-md bg-graphite-50/60 border border-graphite-200/50"
                >
                  <div className="flex items-center gap-3">
                    {log.blocked ? (
                      <XCircle className="w-4.5 h-4.5 text-lava-500 flex-shrink-0" />
                    ) : (
                      <CheckCircle className="w-4.5 h-4.5 text-neon-500 flex-shrink-0" />
                    )}
                    <div>
                      <p className="text-sm font-medium text-graphite-900">
                        {log.defense_type || '防御模块'}
                      </p>
                      <p className="text-xs text-graphite-400">
                        置信度: {(log.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                  <span className={`badge flex-shrink-0 ${log.blocked ? 'badge-danger' : 'badge-success'}`}>
                    {log.blocked ? '已拦截' : '已放行'}
                  </span>
                </motion.div>
              ))
            )}
          </div>
        </motion.div>
      </div>

      {/* 安全提示 */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="card border-electric-200/60 bg-electric-50/30"
      >
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-electric-100 flex items-center justify-center flex-shrink-0">
            <Shield className="w-5 h-5 text-electric-600" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-graphite-900">安全提示</p>
            <p className="text-xs text-graphite-600 mt-0.5">
              定期进行 OWASP 测试和红队演练可以提升系统安全性
            </p>
          </div>
          <ArrowRight className="w-4 h-4 text-graphite-400" />
        </div>
      </motion.div>
    </div>
  )
}

function StatCard({ icon, label, value, subLabel, color }) {
  const colors = {
    electric: 'bg-electric-50 text-electric-600 border-electric-200/70',
    lava: 'bg-lava-50 text-lava-600 border-lava-200/70',
    neon: 'bg-neon-50 text-neon-600 border-neon-200/70',
    amber: 'bg-amber-50 text-amber-600 border-amber-200/70',
  }

  const valueColors = {
    electric: 'stat-value-electric',
    lava: 'stat-value-lava',
    neon: 'stat-value-neon',
    amber: 'text-3xl font-bold font-display text-amber-600 tracking-tight',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="card card-hover"
    >
      <div className="flex items-center gap-4">
        <div className={`p-2.5 rounded-md border ${colors[color]}`}>
          {icon}
        </div>
        <div className="min-w-0">
          <p className="text-xs text-graphite-500">{label}</p>
          <p className={valueColors[color]}>{value}</p>
          <p className="text-[11px] text-graphite-400 mt-0.5">{subLabel}</p>
        </div>
      </div>
    </motion.div>
  )
}
