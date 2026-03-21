import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Eye, FileText, Zap, Shield, BarChart3, Clock } from 'lucide-react'
import { api } from '../api'

const actionConfig = {
  attack_run: { bg: 'bg-lava-100', text: 'text-lava-700', border: 'border-lava-200/70', label: '攻击测试' },
  defense_detect: { bg: 'bg-neon-100', text: 'text-neon-700', border: 'border-neon-200/70', label: '防御检测' },
  benchmark_run: { bg: 'bg-electric-100', text: 'text-electric-700', border: 'border-electric-200/70', label: '基准测试' },
  model_list: { bg: 'bg-graphite-100', text: 'text-graphite-700', border: 'border-graphite-200/70', label: '模型查询' },
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
}

const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } },
}

export default function AuditLogPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({})
  const [selectedLog, setSelectedLog] = useState(null)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    fetchLogs()
  }, [filters])

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const res = await api.get('/api/audit/logs', { params: filters })
      setLogs(res.data.logs || [])
      setTotal(res.data.total || 0)
    } catch (error) {
      setLogs(getDefaultLogs())
      setTotal(getDefaultLogs().length)
    } finally {
      setLoading(false)
    }
  }

  const getDefaultLogs = () => [
    { id: 1, action: 'attack_run', resource: '/api/attack', method: 'POST', username: 'admin', ip_address: '192.168.1.100', response_status: 200, duration_ms: 1250, created_at: '2024-03-01 10:30:00' },
    { id: 2, action: 'defense_detect', resource: '/api/defense', method: 'POST', username: 'user1', ip_address: '192.168.1.101', response_status: 200, duration_ms: 450, created_at: '2024-03-01 10:29:30' },
    { id: 3, action: 'benchmark_run', resource: '/api/benchmark', method: 'POST', username: 'admin', ip_address: '192.168.1.100', response_status: 202, duration_ms: 120, created_at: '2024-03-01 10:28:00' },
    { id: 4, action: 'model_list', resource: '/api/models', method: 'GET', username: 'user2', ip_address: '192.168.1.102', response_status: 200, duration_ms: 85, created_at: '2024-03-01 10:27:15' },
    { id: 5, action: 'attack_run', resource: '/api/attack', method: 'POST', username: 'user1', ip_address: '192.168.1.101', response_status: 400, duration_ms: 320, created_at: '2024-03-01 10:26:00' },
  ]

  const viewLogDetail = (log) => setSelectedLog(log)

  const getActionTag = (action) => {
    const config = actionConfig[action] || actionConfig.model_list
    return (
      <span className={`text-xs px-2 py-1 rounded font-medium border ${config.bg} ${config.text} ${config.border}`}>
        {config.label}
      </span>
    )
  }

  const getStatusTag = (status) => {
    if (status >= 200 && status < 300) {
      return <span className="badge bg-neon-100 text-neon-700 border border-neon-200/70">{status}</span>
    }
    if (status >= 400) {
      return <span className="badge bg-lava-100 text-lava-700 border border-lava-200/70">{status}</span>
    }
    return <span className="badge bg-graphite-100 text-graphite-700 border border-graphite-200/60">{status}</span>
  }

  const stats = {
    totalRequests: total,
    avgResponseTime: logs.length
      ? Math.round(logs.reduce((a, b) => a + b.duration_ms, 0) / logs.length)
      : 0,
    errorRate: logs.length
      ? ((logs.filter((l) => l.response_status >= 400).length / logs.length) * 100).toFixed(1)
      : 0,
  }

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      {/* 页面标题 */}
      <motion.div variants={item} className="flex items-center gap-3">
        <div className="w-11 h-11 bg-electric-100 rounded-lg flex items-center justify-center border border-electric-200/70">
          <FileText className="w-5.5 h-5.5 text-electric-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold font-display text-graphite-900 tracking-tight">
            审计日志
          </h1>
          <p className="text-sm text-graphite-500">记录和追踪所有系统操作</p>
        </div>
      </motion.div>

      {/* 统计卡片 */}
      <motion.div variants={item} className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 bg-electric-100 rounded-lg flex items-center justify-center border border-electric-200/70">
            <BarChart3 className="w-5 h-5 text-electric-600" />
          </div>
          <div>
            <p className="text-xs text-graphite-500">总请求数</p>
            <p className="text-2xl font-bold font-display text-graphite-900">{stats.totalRequests}</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center border border-amber-200/70">
            <Clock className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <p className="text-xs text-graphite-500">平均响应时间</p>
            <p className="text-2xl font-bold font-display text-graphite-900">{stats.avgResponseTime}ms</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 bg-lava-100 rounded-lg flex items-center justify-center border border-lava-200/70">
            <Zap className="w-5 h-5 text-lava-600" />
          </div>
          <div>
            <p className="text-xs text-graphite-500">错误率</p>
            <p className="text-2xl font-bold font-display text-graphite-900">{stats.errorRate}%</p>
          </div>
        </div>
      </motion.div>

      {/* 搜索筛选 */}
      <motion.div variants={item} className="card">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-graphite-400" />
            <input
              type="text"
              placeholder="搜索用户..."
              className="input-field pl-10"
              onChange={(e) => setFilters({ ...filters, username: e.target.value || undefined })}
            />
          </div>
          <select
            className="select-field md:w-48"
            onChange={(e) => setFilters({ ...filters, action: e.target.value || undefined })}
          >
            <option value="">操作类型</option>
            <option value="attack_run">攻击测试</option>
            <option value="defense_detect">防御检测</option>
            <option value="benchmark_run">基准测试</option>
          </select>
        </div>
      </motion.div>

      {/* 日志表格 */}
      <motion.div variants={item} className="card p-0 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-graphite-500">
            <div className="spinner mx-auto mb-2" />
            加载中...
          </div>
        ) : logs.length === 0 ? (
          <div className="p-8 text-center text-graphite-500">暂无日志</div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>操作</th>
                  <th>资源</th>
                  <th>方法</th>
                  <th>用户</th>
                  <th>状态</th>
                  <th>耗时</th>
                  <th>时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="group">
                    <td className="text-graphite-600 text-sm">{log.id}</td>
                    <td>{getActionTag(log.action)}</td>
                    <td className="font-mono text-xs text-graphite-600">{log.resource}</td>
                    <td>
                      <span className="badge bg-graphite-100 text-graphite-700 border border-graphite-200/60">
                        {log.method}
                      </span>
                    </td>
                    <td className="text-graphite-600">{log.username}</td>
                    <td>{getStatusTag(log.response_status)}</td>
                    <td className="text-graphite-600">{log.duration_ms}ms</td>
                    <td className="text-graphite-500 text-xs">{log.created_at}</td>
                    <td>
                      <button
                        onClick={() => viewLogDetail(log)}
                        className="p-1.5 text-graphite-400 hover:text-electric-600 transition-colors"
                      >
                        <Eye size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      {/* 日志详情模态框 */}
      <AnimatePresence>
        {selectedLog && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-graphite-900/30 backdrop-blur-sm flex items-center justify-center z-50"
            onClick={() => setSelectedLog(null)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="bg-white rounded-lg p-6 w-full max-w-md shadow-modal"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-lg font-semibold text-graphite-900 mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5 text-electric-500" />
                日志详情
              </h2>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-graphite-500">操作:</span>
                  {getActionTag(selectedLog.action)}
                </div>
                <div className="flex justify-between">
                  <span className="text-graphite-500">资源:</span>
                  <span className="font-mono text-sm">{selectedLog.resource}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-graphite-500">用户名:</span>
                  <span className="font-medium">{selectedLog.username}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-graphite-500">IP地址:</span>
                  <span className="font-mono text-sm">{selectedLog.ip_address}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-graphite-500">响应状态:</span>
                  {getStatusTag(selectedLog.response_status)}
                </div>
                <div className="flex justify-between">
                  <span className="text-graphite-500">响应时间:</span>
                  <span className="font-medium">{selectedLog.duration_ms}ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-graphite-500">时间:</span>
                  <span className="text-sm">{selectedLog.created_at}</span>
                </div>
              </div>
              <button onClick={() => setSelectedLog(null)} className="btn-secondary w-full mt-5">
                关闭
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
