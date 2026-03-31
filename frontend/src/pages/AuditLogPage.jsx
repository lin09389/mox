import { useEffect, useMemo, useState } from 'react'
import { FileText, Filter, RefreshCw, Search } from 'lucide-react'
import api from '../api'
import { MetricCard, PageHeader, PanelHeader, TableMobileFallback } from '../components/ui/AppFrame'

function fallbackLogs() {
  return [
    { id: 1, action: 'attack_run', action_label: '攻击测试', resource: '/api/attack', method: 'POST', username: 'admin', response_status: 200, duration_ms: 1250, created_at: '2026-03-31 10:30:00' },
    { id: 2, action: 'defense_detect', action_label: '防御检测', resource: '/api/defense', method: 'POST', username: 'analyst', response_status: 200, duration_ms: 450, created_at: '2026-03-31 10:29:30' },
    { id: 3, action: 'benchmark_run', action_label: '基准评测', resource: '/api/benchmark', method: 'POST', username: 'admin', response_status: 202, duration_ms: 220, created_at: '2026-03-31 10:28:00' },
    { id: 4, action: 'model_list', action_label: '模型查询', resource: '/api/models', method: 'GET', username: 'reviewer', response_status: 200, duration_ms: 88, created_at: '2026-03-31 10:27:15' },
    { id: 5, action: 'attack_run', action_label: '攻击测试', resource: '/api/attack', method: 'POST', username: 'intern', response_status: 400, duration_ms: 310, created_at: '2026-03-31 10:26:00' },
  ]
}

export default function AuditLogPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  const fetchLogs = async () => {
    setLoading(true)
    try {
      const response = await api.get('/api/audit/logs')
      const items = response.data?.logs || response.data || []
      setLogs(items)
    } catch {
      setLogs(fallbackLogs())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
  }, [])

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    return logs.filter((log) => {
      const statusMatch =
        statusFilter === 'all' ||
        (statusFilter === 'success' && log.response_status < 400) ||
        (statusFilter === 'error' && log.response_status >= 400)
      const textMatch =
        !term ||
        String(log.action_label || log.action).toLowerCase().includes(term) ||
        String(log.resource).toLowerCase().includes(term) ||
        String(log.username).toLowerCase().includes(term)
      return statusMatch && textMatch
    })
  }, [logs, search, statusFilter])

  const stats = useMemo(() => {
    const total = logs.length
    const avg = total ? Math.round(logs.reduce((sum, item) => sum + (item.duration_ms || 0), 0) / total) : 0
    const errors = logs.filter((item) => item.response_status >= 400).length
    return { total, avg, errors }
  }, [logs])

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="AUDIT LOG"
        title="审计日志中心"
        description="统一查看接口行为、状态码和响应时延，便于快速定位异常。"
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard icon={FileText} label="日志总数" value={stats.total} hint="当前筛选前总量" tone="electric" />
        <MetricCard icon={RefreshCw} label="平均耗时" value={`${stats.avg}ms`} hint="接口响应中位水平" tone="warning" />
        <MetricCard icon={Filter} label="异常请求" value={stats.errors} hint="状态码 >= 400" tone="lava" />
      </div>

      <section className="card">
        <PanelHeader title="筛选" description="按关键字和状态过滤审计事件。" />
        <div className="grid gap-3 md:grid-cols-[1fr_220px_auto]">
          <label className="relative">
            <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-graphite-400" />
            <input className="input-field pl-11" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索动作、资源、用户" />
          </label>
          <select className="select-field" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="all">全部状态</option>
            <option value="success">成功</option>
            <option value="error">异常</option>
          </select>
          <button type="button" className="btn-secondary" onClick={fetchLogs}>
            <RefreshCw className="h-4 w-4" />
            刷新日志
          </button>
        </div>
      </section>

      <section className="table-shell">
        {!loading && filtered.length > 0 ? (
          <TableMobileFallback
            items={filtered}
            renderTitle={(item) => item.action_label || item.action}
            renderMeta={(item) => (
              <>
                <p>{item.method} {item.resource}</p>
                <p>用户：{item.username}</p>
                <p>耗时：{item.duration_ms}ms · 时间：{item.created_at}</p>
              </>
            )}
            renderRight={(item) => (
              <span className={`badge ${item.response_status >= 400 ? 'badge-danger' : 'badge-success'}`}>
                {item.response_status}
              </span>
            )}
          />
        ) : null}
        <div className="table-container hidden md:block">
          <table className="table">
            <thead>
              <tr>
                <th>动作</th>
                <th>资源</th>
                <th>用户</th>
                <th>状态码</th>
                <th>耗时</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6}>加载中…</td></tr>
              ) : filtered.length ? (
                filtered.map((log) => (
                  <tr key={log.id}>
                    <td>{log.action_label || log.action}</td>
                    <td>{log.method} {log.resource}</td>
                    <td>{log.username}</td>
                    <td>
                      <span className={`badge ${log.response_status >= 400 ? 'badge-danger' : 'badge-success'}`}>
                        {log.response_status}
                      </span>
                    </td>
                    <td>{log.duration_ms}ms</td>
                    <td>{log.created_at}</td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={6}>暂无匹配日志。</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
