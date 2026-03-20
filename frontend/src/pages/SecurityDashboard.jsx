import { useState, useEffect } from 'react'
import { Shield, AlertTriangle, Activity, Lock, Eye, Zap, CheckCircle, XCircle, TrendingUp, TrendingDown, Server, Clock } from 'lucide-react'
import { getStats, getRecentAttacks, getDefenseLogs } from '../api/security'

const COLORS = ['#10b981', '#ef4444', '#f59e0b', '#6366f1']

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

  const pieData = [
    { name: '已放行', value: stats.totalRequests - stats.blockedRequests },
    { name: '已拦截', value: stats.blockedRequests },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        <span className="ml-3 text-gray-500">正在加载...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">安全仪表盘</h1>
          <p className="text-gray-500">实时监控您的LLM应用安全状态</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Clock className="w-4 h-4" />
          <span>最后更新: {lastUpdate.toLocaleTimeString()}</span>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Activity className="w-6 h-6" />}
          label="总请求数"
          value={stats.totalRequests.toLocaleString()}
          subLabel="今日请求总量"
          color="blue"
        />
        <StatCard
          icon={<Shield className="w-6 h-6" />}
          label="拦截请求"
          value={stats.blockedRequests.toLocaleString()}
          subLabel="恶意请求已拦截"
          color="red"
        />
        <StatCard
          icon={<Lock className="w-6 h-6" />}
          label="防御成功率"
          value={`${(stats.defenseSuccessRate * 100).toFixed(1)}%`}
          subLabel="安全防护有效"
          color="green"
        />
        <StatCard
          icon={<AlertTriangle className="w-6 h-6" />}
          label="攻击成功率"
          value={`${(stats.attackSuccessRate * 100).toFixed(1)}%`}
          subLabel="需要关注的比例"
          color="orange"
        />
      </div>

      {/* 图表区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Server className="w-5 h-5 text-gray-400" />
            请求分布
          </h3>
          <div className="flex items-center justify-center gap-8 py-8">
            <div className="text-center">
              <div className="text-4xl font-bold text-green-600">{pieData[0].value}</div>
              <div className="text-gray-500">已放行</div>
            </div>
            <div className="text-2xl text-gray-300">/</div>
            <div className="text-center">
              <div className="text-4xl font-bold text-red-600">{pieData[1].value}</div>
              <div className="text-gray-500">已拦截</div>
            </div>
          </div>
          <div className="flex justify-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-sm">正常请求</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-sm">恶意请求</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-gray-400" />
            防御活动趋势
          </h3>
          <div className="space-y-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-16 text-xs text-gray-400">T-{6-i}</div>
                <div className="flex-1 h-6 bg-gray-100 rounded overflow-hidden">
                  <div 
                    className={`h-full ${i % 3 === 0 ? 'bg-gradient-to-r from-red-400 to-red-500' : 'bg-gradient-to-r from-green-400 to-green-500'}`}
                    style={{ width: `${Math.random() * 60 + 20}%` }}
                  ></div>
                </div>
                <span className={`text-xs ${i % 3 === 0 ? 'text-red-500' : 'text-green-500'}`}>
                  {i % 3 === 0 ? '拦截' : '放行'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 详细列表 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              最近攻击记录
            </h3>
            <span className="text-sm text-gray-500">实时监控</span>
          </div>
          <div className="space-y-3">
            {recentAttacks.length === 0 ? (
              <div className="text-center py-8">
                <Shield className="w-12 h-12 text-green-500 mx-auto mb-2" />
                <p className="text-gray-500">暂无攻击记录</p>
                <p className="text-sm text-gray-400">系统运行安全</p>
              </div>
            ) : (
              recentAttacks.slice(0, 5).map((attack, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-100">
                  <div className="flex items-center gap-3">
                    {attack.success ? (
                      <XCircle className="w-5 h-5 text-red-500" />
                    ) : (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    )}
                    <div>
                      <p className="font-medium">{attack.type || '未知攻击类型'}</p>
                      <p className="text-sm text-gray-500">{attack.prompt?.substring(0, 30) || '无内容'}...</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs ${attack.success ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                    {attack.success ? '攻击成功' : '已拦截'}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Zap className="w-5 h-5 text-blue-500" />
              防御日志
            </h3>
            <span className="text-sm text-gray-500">实时更新</span>
          </div>
          <div className="space-y-3">
            {defenseLogs.length === 0 ? (
              <div className="text-center py-8">
                <Activity className="w-12 h-12 text-blue-500 mx-auto mb-2" />
                <p className="text-gray-500">暂无防御日志</p>
                <p className="text-sm text-gray-400">等待请求处理</p>
              </div>
            ) : (
              defenseLogs.slice(0, 5).map((log, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    {log.blocked ? (
                      <XCircle className="w-5 h-5 text-red-500" />
                    ) : (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    )}
                    <div>
                      <p className="font-medium">{log.defense_type || '防御模块'}</p>
                      <p className="text-sm text-gray-500">置信度: {(log.confidence * 100).toFixed(1)}%</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs ${log.blocked ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                    {log.blocked ? '已拦截' : '已放行'}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* 底部提示 */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-4 border border-indigo-100">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-100 rounded-lg">
            <Shield className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <p className="font-medium text-indigo-900">安全提示</p>
            <p className="text-sm text-indigo-700">定期进行 OWASP 测试和红队演练可以提升系统安全性</p>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, subLabel, color }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    red: 'bg-red-50 text-red-600 border-red-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    orange: 'bg-orange-50 text-orange-600 border-orange-200',
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg border ${colors[color]}`}>
          {icon}
        </div>
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-xs text-gray-400">{subLabel}</p>
        </div>
      </div>
    </div>
  )
}
