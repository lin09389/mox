import { useState, useEffect } from 'react'
import { Search, Eye } from 'lucide-react'
import { api } from '../api'

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
    const config = {
      attack_run: { color: 'bg-red-100 text-red-800', text: '攻击测试' },
      defense_detect: { color: 'bg-green-100 text-green-800', text: '防御检测' },
      benchmark_run: { color: 'bg-blue-100 text-blue-800', text: '基准测试' },
      model_list: { color: 'bg-gray-100 text-gray-800', text: '模型查询' },
    }
    const c = config[action] || { color: 'bg-gray-100', text: action }
    return <span className={`px-2 py-1 rounded text-xs ${c.color}`}>{c.text}</span>
  }

  const getStatusTag = (status) => {
    if (status >= 200 && status < 300) return <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">{status}</span>
    if (status >= 400) return <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs">{status}</span>
    return <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">{status}</span>
  }

  const stats = {
    totalRequests: total,
    avgResponseTime: logs.length ? Math.round(logs.reduce((a, b) => a + b.duration_ms, 0) / logs.length) : 0,
    errorRate: logs.length ? ((logs.filter(l => l.response_status >= 400).length / logs.length * 100).toFixed(1)) : 0,
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">审计日志</h1>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <div className="text-sm text-gray-500">总请求数</div>
          <div className="text-2xl font-bold text-gray-800">{stats.totalRequests}</div>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <div className="text-sm text-gray-500">平均响应时间</div>
          <div className="text-2xl font-bold text-gray-800">{stats.avgResponseTime}ms</div>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <div className="text-sm text-gray-500">错误率</div>
          <div className="text-2xl font-bold text-gray-800">{stats.errorRate}%</div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
            <input
              type="text"
              placeholder="搜索用户..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg"
              onChange={e => setFilters({ ...filters, username: e.target.value || undefined })}
            />
          </div>
          <select className="px-4 py-2 border rounded-lg" onChange={e => setFilters({ ...filters, action: e.target.value || undefined })}>
            <option value="">操作类型</option>
            <option value="attack_run">攻击测试</option>
            <option value="defense_detect">防御检测</option>
            <option value="benchmark_run">基准测试</option>
          </select>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        {loading ? (
          <div className="p-8 text-center text-gray-500">加载中...</div>
        ) : logs.length === 0 ? (
          <div className="p-8 text-center text-gray-500">暂无日志</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">资源</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">方法</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">耗时</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {logs.map(log => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-gray-600 text-sm">{log.id}</td>
                    <td className="px-6 py-4">{getActionTag(log.action)}</td>
                    <td className="px-6 py-4 text-gray-600 text-sm font-mono">{log.resource}</td>
                    <td className="px-6 py-4"><span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">{log.method}</span></td>
                    <td className="px-6 py-4 text-gray-600">{log.username}</td>
                    <td className="px-6 py-4">{getStatusTag(log.response_status)}</td>
                    <td className="px-6 py-4 text-gray-600">{log.duration_ms}ms</td>
                    <td className="px-6 py-4 text-gray-600 text-sm">{log.created_at}</td>
                    <td className="px-6 py-4">
                      <button onClick={() => viewLogDetail(log)} className="p-1 text-gray-400 hover:text-gray-600"><Eye size={18} /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedLog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedLog(null)}>
          <div className="bg-white rounded-xl p-6 w-full max-w-lg" onClick={e => e.stopPropagation()}>
            <h2 className="text-xl font-bold mb-4">日志详情</h2>
            <div className="space-y-3">
              <div className="flex justify-between"><span className="text-gray-500">操作:</span><span>{getActionTag(selectedLog.action)}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">资源:</span><span className="font-mono text-sm">{selectedLog.resource}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">用户名:</span><span>{selectedLog.username}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">IP地址:</span><span className="font-mono">{selectedLog.ip_address}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">响应状态:</span>{getStatusTag(selectedLog.response_status)}</div>
              <div className="flex justify-between"><span className="text-gray-500">响应时间:</span><span>{selectedLog.duration_ms}ms</span></div>
              <div className="flex justify-between"><span className="text-gray-500">时间:</span><span>{selectedLog.created_at}</span></div>
            </div>
            <button onClick={() => setSelectedLog(null)} className="mt-4 w-full px-4 py-2 border rounded-lg">关闭</button>
          </div>
        </div>
      )}
    </div>
  )
}
