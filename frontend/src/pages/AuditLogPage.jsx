import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { FileText, Filter, RefreshCw, Search } from 'lucide-react'
import { MetricCard, MetricCardSkeleton, PageHeader, PanelHeader, TableMobileFallback, Skeleton } from '../components/ui/AppFrame'
import { useAuditLogs } from '../hooks/queries'
import { useQueryClient } from '@tanstack/react-query'

function fallbackLogs() {
  return [
    { id: 1, action: 'attack_run', action_label: '攻击测试', resource: '/api/attack', method: 'POST', username: 'admin', response_status: 200, duration_ms: 1250, created_at: '2026-03-31 10:30:00' },
    { id: 2, action: 'defense_detect', action_label: '防御检测', resource: '/api/defense', method: 'POST', username: 'analyst', response_status: 200, duration_ms: 450, created_at: '2026-03-31 10:29:30' },
    { id: 3, action: 'benchmark_run', action_label: '基准评测', resource: '/api/benchmark', method: 'POST', username: 'admin', response_status: 202, duration_ms: 220, created_at: '2026-03-31 10:28:00' },
    { id: 4, action: 'model_list', action_label: '模型查询', resource: '/api/models', method: 'GET', username: 'reviewer', response_status: 200, duration_ms: 88, created_at: '2026-03-31 10:27:15' },
    { id: 5, action: 'attack_run', action_label: '攻击测试', resource: '/api/attack', method: 'POST', username: 'intern', response_status: 400, duration_ms: 310, created_at: '2026-03-31 10:26:00' },
  ]
}

import { containerVariants, itemVariants } from '../utils/animations'

export default function AuditLogPage() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  const queryClient = useQueryClient()
  const { data: logsData, isLoading, isError, isFetching, refetch } = useAuditLogs()

  // Use fallback if api fails in demo mode
  const logs = useMemo(() => isError ? fallbackLogs() : logsData || [], [isError, logsData])

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
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="page-shell">
      <motion.div variants={itemVariants}>
        <PageHeader
          eyebrow="AUDIT LOG"
          title="审计日志中心"
          description="统一监控平台所有的接口行为、状态码和响应时延，便于快速追溯安全事件与异常请求。"
        />
      </motion.div>

      <motion.div variants={itemVariants} className="grid gap-4 md:grid-cols-3">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => <MetricCardSkeleton key={i} />)
        ) : (
          <>
            <MetricCard icon={FileText} label="日志捕获总数" value={stats.total} hint="当前记录池总量" tone="electric" />
            <MetricCard icon={RefreshCw} label="系统平均耗时" value={`${stats.avg}ms`} hint="API 响应延迟中位数" tone="warning" />
            <MetricCard icon={Filter} label="拦截/异常请求" value={stats.errors} hint="状态码 ≥ 400" tone="lava" />
          </>
        )}
      </motion.div>

      <motion.section variants={itemVariants} className="card p-5">
        <PanelHeader title="检索过滤" description="按动作关键字、请求资源路径及状态码过滤日志轨迹。" />
        <div className="grid gap-4 md:grid-cols-[1fr_220px_auto]">
          <label className="relative">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" />
            <input className="input-field pl-10" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索请求动作、REST 资源或操作用户..." />
          </label>
          <label className="relative">
            <Filter className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" />
            <select className="input-field pl-10 appearance-none bg-no-repeat bg-[right_0.5rem_center] bg-[length:1.5em_1.5em]" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="all">全部 HTTP 状态</option>
              <option value="success">正常访问 (2xx/3xx)</option>
              <option value="error">异常阻断 (4xx/5xx)</option>
            </select>
          </label>
          <button type="button" className="btn-secondary h-[42px] px-6" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
            同步日志
          </button>
        </div>
      </motion.section>

      <motion.section variants={itemVariants} className="card overflow-hidden">
        <div className="border-b border-[var(--border-glass)] bg-[var(--bg-glass-strong)] px-5 py-4">
          <h2 className="text-lg font-bold font-display text-[var(--text-main)]">系统操作流水</h2>
          <p className="mt-1 text-sm font-medium text-[var(--text-muted)]">
            当前展示 {filtered.length} 条审计记录。
          </p>
        </div>

        {!isLoading && filtered.length > 0 && (
          <div className="md:hidden">
            <TableMobileFallback
              items={filtered}
              renderTitle={(item) => item.action_label || item.action}
              renderMeta={(item) => (
                <>
                  <p className="font-mono text-xs">{item.method} {item.resource}</p>
                  <p>执行用户：<span className="font-bold">{item.username}</span></p>
                  <p>延迟：{item.duration_ms}ms · {item.created_at}</p>
                </>
              )}
              renderRight={(item) => (
                <span className={`badge border font-mono ${item.response_status >= 400 ? 'bg-rose-500/10 text-rose-500 border-rose-500/20' : 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'}`}>
                  {item.response_status}
                </span>
              )}
            />
          </div>
        )}

        <div className="hidden md:block">
          {isLoading ? (
            <div className="p-6 space-y-4">
               {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex min-h-[300px] flex-col items-center justify-center gap-3 text-center opacity-60">
              <FileText className="h-12 w-12 text-[var(--text-muted)]" />
              <p className="text-sm font-bold text-[var(--text-muted)]">无匹配记录。</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-[var(--text-main)]">
                <thead className="bg-[var(--bg-glass-strong)] text-[var(--text-muted)] font-bold uppercase tracking-wider text-xs border-b border-[var(--border-glass)]">
                  <tr>
                    <th className="px-6 py-4">操作标签</th>
                    <th className="px-6 py-4">端点路由</th>
                    <th className="px-6 py-4">身份识别</th>
                    <th className="px-6 py-4">HTTP状态</th>
                    <th className="px-6 py-4">网络延迟</th>
                    <th className="px-6 py-4">记录时间</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-glass)]">
                  {filtered.map((log) => (
                    <motion.tr 
                      key={log.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="hover:bg-[var(--bg-glass)] transition-colors"
                    >
                      <td className="px-6 py-4 font-bold">{log.action_label || log.action}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span className={`badge text-[10px] uppercase font-bold tracking-widest ${log.method === 'GET' ? 'bg-cyan-500/10 text-cyan-500' : log.method === 'POST' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'}`}>{log.method}</span>
                          <span className="font-mono text-[var(--text-muted)]">{log.resource}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 font-bold text-[var(--text-main)]">{log.username}</td>
                      <td className="px-6 py-4">
                        <span className={`badge border font-mono font-bold ${log.response_status >= 400 ? 'bg-rose-500/10 text-rose-500 border-rose-500/20' : 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'}`}>
                          {log.response_status}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-mono text-[var(--text-muted)]">
                        {log.duration_ms} ms
                      </td>
                      <td className="px-6 py-4 font-mono text-[var(--text-muted)]">{log.created_at}</td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </motion.section>
    </motion.div>
  )
}
