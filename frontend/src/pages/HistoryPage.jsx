import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import toast from 'react-hot-toast'
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock3,
  Download,
  Filter,
  RefreshCw,
  Search,
  Shield,
  Trash2,
  Zap,
  History,
  Eye,
  ArrowRight,
  FileText,
} from 'lucide-react'
import { buildGovernanceReportLink } from '../api'
import { useReportDetail } from '../hooks/useReportDetail'
import { extractReportId, normalizeHistoryResponse } from '../utils/historyRecords'
import {
  MetricCard,
  MetricCardSkeleton,

  PanelHeader,
  TableMobileFallback,
  Skeleton
} from '../components/ui/AppFrame'
import { HubPanelIntro } from '../context/HubContext'
import { FOCUSABLE_ROW_CLASS, handleRowKeyDown } from '../utils/a11y'
import { useAttackHistory, useDefenseHistory } from '../hooks/queries'
import { useQueryClient } from '@tanstack/react-query'

const TABS = [
  { id: 'attack', label: '攻击记录', icon: Zap },
  { id: 'defense', label: '防御记录', icon: Shield },
]

const ATTACK_LABELS = {
  prompt_injection: '提示词注入',
  jailbreak: '越狱攻击',
  gcg: 'GCG 攻击',
  auto_dan: 'AutoDAN',
}

const DEFENSE_LABELS = {
  input_filter: '输入过滤',
  output_filter: '输出过滤',
}

const badgeForAttackResult = (result) => (result === 'success' ? 'badge-danger border-rose-500/30 bg-rose-500/10 text-rose-500' : 'badge-success border-emerald-500/30 bg-emerald-500/10 text-emerald-500')
const badgeForDefenseResult = (malicious) => (malicious ? 'badge-danger border-rose-500/30 bg-rose-500/10 text-rose-500' : 'badge-success border-emerald-500/30 bg-emerald-500/10 text-emerald-500')

function formatDate(dateStr) {
  const date = new Date(dateStr)
  const diff = Date.now() - date.getTime()
  if (diff < 60_000) return '刚刚'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} 小时前`
  return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

import { containerVariants, itemVariants } from '../utils/animations'

export default function HistoryPage() {
  const [activeTab, setActiveTab] = useState('attack')
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState('newest')
  const [selectedRecord, setSelectedRecord] = useState(null)
  
  const queryClient = useQueryClient()
  const attackQuery = useAttackHistory({ limit: 50 })
  const defenseQuery = useDefenseHistory({ limit: 50 })

  const isAttack = activeTab === 'attack'
  const loading = isAttack ? attackQuery.isLoading : defenseQuery.isLoading
  const isFetching = isAttack ? attackQuery.isFetching : defenseQuery.isFetching
  
  // Fallbacks for demo if queries fail, handled by our api layer already so `data` will be correct
  const currentRaw = useMemo(() => {
    const response = isAttack ? attackQuery.data : defenseQuery.data
    return normalizeHistoryResponse(response, isAttack ? 'attack' : 'defense')
  }, [isAttack, attackQuery.data, defenseQuery.data])

  const linkedReportId = useMemo(
    () => (selectedRecord ? extractReportId(selectedRecord) : null),
    [selectedRecord]
  )
  const linkedReport = useMemo(
    () => (linkedReportId ? { id: linkedReportId } : null),
    [linkedReportId]
  )
  const { detailLoading: reportDetailLoading, detailContent: reportDetail } = useReportDetail(linkedReport)

  const filtered = useMemo(() => {
    const search = searchTerm.trim().toLowerCase()
    const list = currentRaw.filter((item) => {
      const type = isAttack ? item.attack_type : item.defense_type
      return !search || type?.toLowerCase().includes(search) || item.model_name?.toLowerCase().includes(search)
    })

    return [...list].sort((a, b) => {
      if (sortBy === 'oldest') return new Date(a.created_at) - new Date(b.created_at)
      if (sortBy === 'score') return (b.success_score || 0) - (a.success_score || 0)
      if (sortBy === 'confidence') return (b.confidence || 0) - (a.confidence || 0)
      return new Date(b.created_at) - new Date(a.created_at)
    })
  }, [isAttack, currentRaw, searchTerm, sortBy])

  const metrics = useMemo(() => {
    const total = currentRaw.length
    const successCount =
      isAttack
        ? currentRaw.filter((item) => item.result === 'success').length
        : currentRaw.filter((item) => item.is_malicious).length
    const todayCount = currentRaw.filter(
      (item) => new Date(item.created_at).toDateString() === new Date().toDateString()
    ).length

    return {
      total,
      successCount,
      ratio: total ? Math.round((successCount / total) * 100) : 0,
      todayCount,
    }
  }, [isAttack, currentRaw])

  const clearHistory = () => {
    // Optimistically update query client cache
    if (isAttack) {
      queryClient.setQueryData(['attack', 'history', { limit: 50 }], { records: [] })
    } else {
      queryClient.setQueryData(['defense', 'history', { limit: 50 }], { records: [] })
    }
    toast.success('已清空当前页签记录。')
  }

  const exportHistory = () => {
    const data = JSON.stringify(currentRaw, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${activeTab}_history_${new Date().toISOString().slice(0, 10)}.json`
    anchor.click()
    URL.revokeObjectURL(url)
    toast.success('已导出当前记录。')
  }

  const refetch = () => {
    if (isAttack) attackQuery.refetch()
    else defenseQuery.refetch()
  }

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="page-shell">
      <HubPanelIntro description="统一查看攻击与防御记录，支持搜索、排序、导出和移动端浏览。" />

      <motion.div variants={itemVariants} className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => <MetricCardSkeleton key={i} />)
        ) : (
          <>
            <MetricCard icon={BarChart3} label="总记录数" value={metrics.total} hint="当前页签下的所有记录" tone="electric" />
            <MetricCard
              icon={isAttack ? AlertTriangle : Shield}
              label={isAttack ? '攻击成功数' : '检测到威胁'}
              value={metrics.successCount}
              hint={isAttack ? '需要重点复盘的案例' : '被识别出的风险内容'}
              tone={isAttack ? 'lava' : 'amber'}
            />
            <MetricCard
              icon={CheckCircle2}
              label={isAttack ? '成功率' : '识别率'}
              value={`${metrics.ratio}%`}
              hint="帮助快速判断近期趋势"
              tone="neon"
            />
            <MetricCard icon={Clock3} label="今日新增" value={metrics.todayCount} hint="便于快速查看今天的变化" tone="graphite" />
          </>
        )}
      </motion.div>

      <motion.section variants={itemVariants} className="card p-5">
        <PanelHeader
          title="筛选与操作"
          description="优先把常用动作聚合在一行，减少来回切页。"
        />
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex flex-wrap w-fit gap-1 p-1 rounded-xl bg-[var(--bg-glass-strong)] border border-[var(--border-glass-strong)] shadow-sm backdrop-blur-md">
            {TABS.map((tab) => {
              const Icon = tab.icon
              const active = tab.id === activeTab
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => {
                    setActiveTab(tab.id)
                    setSelectedRecord(null)
                  }}
                  className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-bold transition-all duration-300 ${active ? 'bg-cyan-500 text-white shadow-soft' : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-glass)]'}`}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              )
            })}
          </div>

          <div className="flex flex-col gap-3 md:flex-row md:items-center">
            <label className="relative min-w-[220px]">
              <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" />
              <input
                type="text"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                className="input-field pl-10"
                placeholder="搜索类型或模型"
              />
            </label>

            <label className="relative min-w-[180px]">
              <Filter className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" />
              <select value={sortBy} onChange={(event) => setSortBy(event.target.value)} className="input-field pl-10 appearance-none bg-no-repeat bg-[right_0.5rem_center] bg-[length:1.5em_1.5em]">
                <option value="newest">最新优先</option>
                <option value="oldest">最早优先</option>
                <option value={isAttack ? 'score' : 'confidence'}>
                  {isAttack ? '分数优先' : '置信度优先'}
                </option>
              </select>
            </label>

            <div className="flex gap-2">
              <button type="button" onClick={refetch} className="btn-secondary h-[42px]" disabled={isFetching}>
                <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
              </button>
              <button type="button" onClick={exportHistory} className="btn-secondary h-[42px]" disabled={currentRaw.length === 0}>
                <Download className="h-4 w-4" />
              </button>
              <button type="button" onClick={clearHistory} className="btn-ghost text-rose-500 hover:text-rose-600 hover:bg-rose-500/10 h-[42px]" disabled={currentRaw.length === 0}>
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </motion.section>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <motion.section variants={itemVariants} className="card overflow-hidden">
        <div className="border-b border-[var(--border-glass)] bg-[var(--bg-glass-strong)] px-5 py-4">
          <h2 className="text-lg font-bold font-display text-[var(--text-main)]">{isAttack ? '攻击记录列表' : '防御记录列表'}</h2>
          <p className="mt-1 text-sm font-medium text-[var(--text-muted)]">
            {loading ? '正在同步数据...' : `当前共检索到 ${filtered.length} 条记录。`}
          </p>
        </div>

        {!loading && filtered.length > 0 && (
          <TableMobileFallback
            items={filtered}
            onItemActivate={setSelectedRecord}
            getCardClassName={(item) =>
              selectedRecord?.id === item.id ? 'border-l-2 border-l-cyan-500 bg-[var(--bg-glass-strong)]' : ''
            }
            renderTitle={(item) =>
              isAttack
                ? ATTACK_LABELS[item.attack_type] || item.attack_type
                : DEFENSE_LABELS[item.defense_type] || item.defense_type
            }
            renderMeta={(item) => (
              <>
                <p>模型: <span className="font-mono">{item.model_name}</span></p>
                <p>时间: <span className="font-mono">{formatDate(item.created_at)}</span></p>
                <p>
                  {isAttack
                    ? `漏洞分值: ${Math.round((item.success_score || 0) * 100)}%`
                    : `判定置信度: ${Math.round((item.confidence || 0) * 100)}%`}
                </p>
              </>
            )}
            renderRight={(item) => (
              <span className={`badge ${
                isAttack
                  ? badgeForAttackResult(item.result)
                  : badgeForDefenseResult(item.is_malicious)
              }`}>
                {isAttack
                  ? item.result === 'success'
                    ? '突破成功'
                    : '已拦截'
                  : item.is_malicious
                    ? '发现威胁'
                    : '内容合规'}
              </span>
            )}
          />
        )}

        <div className="hidden md:block">
          {loading ? (
            <div className="p-6 space-y-4">
               {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex min-h-[300px] flex-col items-center justify-center px-6 text-center text-sm font-bold text-[var(--text-muted)] opacity-60">
              <History className="h-12 w-12 mb-4" />
              {searchTerm ? '没有找到匹配的记录。' : '当前页签还没有数据。'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-[var(--text-main)]">
                <thead className="bg-[var(--bg-glass-strong)] text-[var(--text-muted)] font-bold uppercase tracking-wider text-xs border-b border-[var(--border-glass)]">
                  <tr>
                    <th className="px-6 py-4">时间戳</th>
                    <th className="px-6 py-4">{isAttack ? '攻击向量' : '防御切面'}</th>
                    <th className="px-6 py-4">目标模型</th>
                    <th className="px-6 py-4">裁决结果</th>
                    <th className="px-6 py-4">{isAttack ? '漏洞分值' : '判定置信度'}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-glass)]">
                  {filtered.map((item) => {
                    const typeLabel =
                      isAttack
                        ? ATTACK_LABELS[item.attack_type] || item.attack_type
                        : DEFENSE_LABELS[item.defense_type] || item.defense_type
                    const score = isAttack ? item.success_score || 0 : item.confidence || 0

                    const isSelected = selectedRecord?.id === item.id
                    return (
                      <motion.tr
                        key={item.id}
                        tabIndex={0}
                        role="button"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`hover:bg-[var(--bg-glass)] transition-colors cursor-pointer ${FOCUSABLE_ROW_CLASS} ${
                          isSelected ? 'bg-[var(--bg-glass-strong)] border-l-2 border-l-cyan-500' : ''
                        }`}
                        onClick={() => setSelectedRecord(item)}
                        onKeyDown={(event) => handleRowKeyDown(event, () => setSelectedRecord(item))}
                      >
                        <td className="px-6 py-4 whitespace-nowrap font-mono text-[var(--text-muted)]">{formatDate(item.created_at)}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="badge badge-neutral bg-[var(--bg-glass-strong)] border-[var(--border-glass)]">{typeLabel}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap font-mono font-bold">{item.model_name}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`badge ${
                              isAttack
                                ? badgeForAttackResult(item.result)
                                : badgeForDefenseResult(item.is_malicious)
                            }`}
                          >
                            {isAttack
                              ? item.result === 'success'
                                ? '突破成功'
                                : '安全防御'
                              : item.is_malicious
                                ? '发现威胁'
                                : '内容合规'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-3">
                            <div className="h-2 w-24 overflow-hidden rounded-full bg-[var(--bg-glass-strong)] border border-[var(--border-glass)]">
                              <div
                                className={`h-full rounded-full transition-all duration-700 ease-out ${
                                  score >= 0.6 ? 'bg-rose-500' : 'bg-emerald-500'
                                }`}
                                style={{ width: `${Math.round(score * 100)}%` }}
                              />
                            </div>
                            <span className="font-mono font-bold text-[var(--text-main)]">
                              {Math.round(score * 100)}%
                            </span>
                          </div>
                        </td>
                      </motion.tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </motion.section>

      <motion.section variants={itemVariants} className="card bg-[var(--bg-glass-strong)] border-cyan-500/10 h-fit lg:sticky lg:top-6">
        <div className="border-b border-[var(--border-glass)] px-5 py-4">
          <h2 className="text-lg font-bold font-display text-[var(--text-main)] flex items-center gap-2">
            <Eye className="h-5 w-5 text-cyan-500" />
            记录详情
          </h2>
          <p className="mt-1 text-sm font-medium text-[var(--text-muted)]">选中列表中的记录查看完整上下文。</p>
        </div>

        <AnimatePresence mode="wait">
          {selectedRecord ? (
            <motion.div
              key={selectedRecord.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-4 p-5"
            >
              <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-4">
                <div className="flex flex-wrap items-center gap-2 mb-3">
                  <span className="badge badge-neutral bg-[var(--bg-glass-strong)] border-[var(--border-glass)]">
                    {isAttack
                      ? ATTACK_LABELS[selectedRecord.attack_type] || selectedRecord.attack_type
                      : DEFENSE_LABELS[selectedRecord.defense_type] || selectedRecord.defense_type}
                  </span>
                  <span className="badge badge-neutral font-mono">{selectedRecord.model_name}</span>
                  <span className={`badge ${
                    isAttack
                      ? badgeForAttackResult(selectedRecord.result)
                      : badgeForDefenseResult(selectedRecord.is_malicious)
                  }`}>
                    {isAttack
                      ? selectedRecord.result === 'success' ? '突破成功' : '已拦截'
                      : selectedRecord.is_malicious ? '发现威胁' : '内容合规'}
                  </span>
                </div>
                <p className="text-xs font-mono text-[var(--text-muted)]">{formatDate(selectedRecord.created_at)}</p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-4 text-center">
                  <p className="text-2xl font-mono font-bold text-[var(--text-main)]">
                    {Math.round((isAttack ? selectedRecord.success_score || 0 : selectedRecord.confidence || 0) * 100)}%
                  </p>
                  <p className="mt-1 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">
                    {isAttack ? '漏洞分值' : '判定置信度'}
                  </p>
                </div>
                <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-4 text-center">
                  <p className="text-sm font-mono font-bold text-[var(--text-main)]">#{selectedRecord.id}</p>
                  <p className="mt-1 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">记录 ID</p>
                </div>
              </div>

              {(selectedRecord.prompt || selectedRecord.text || selectedRecord.input) && (
                <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-main)]/40 p-4">
                  <p className="mb-2 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">
                    {isAttack ? '攻击提示词' : '扫描文本'}
                  </p>
                  <pre className="max-h-40 overflow-auto whitespace-pre-wrap break-words text-xs font-mono text-[var(--text-main)]">
                    {selectedRecord.prompt || selectedRecord.text || selectedRecord.input}
                  </pre>
                </div>
              )}

              {isAttack && selectedRecord.model_response && (
                <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-main)]/40 p-4">
                  <p className="mb-2 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">模型响应</p>
                  <pre className="max-h-40 overflow-auto whitespace-pre-wrap break-words text-xs font-mono text-[var(--text-main)]">
                    {selectedRecord.model_response}
                  </pre>
                </div>
              )}

              {!isAttack && selectedRecord.output_text && (
                <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-main)]/40 p-4">
                  <p className="mb-2 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">过滤输出</p>
                  <pre className="max-h-40 overflow-auto whitespace-pre-wrap break-words text-xs font-mono text-[var(--text-main)]">
                    {selectedRecord.output_text}
                  </pre>
                </div>
              )}

              {linkedReportId ? (
                <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4 space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs font-bold uppercase tracking-widest text-cyan-500 flex items-center gap-1.5">
                      <FileText className="h-3.5 w-3.5" />
                      关联报告 #{linkedReportId}
                    </p>
                    <Link
                      to={buildGovernanceReportLink(linkedReportId)}
                      className="btn-secondary inline-flex items-center gap-1 px-2 py-1 text-xs font-bold text-cyan-500"
                    >
                      查看报告
                      <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                  {reportDetailLoading ? (
                    <Skeleton className="h-[120px] w-full" />
                  ) : reportDetail ? (
                    <pre className="max-h-[160px] overflow-auto whitespace-pre-wrap break-words text-xs font-mono text-[var(--text-main)]">
                      {JSON.stringify(reportDetail, null, 2)}
                    </pre>
                  ) : null}
                </div>
              ) : null}
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex min-h-[280px] flex-col items-center justify-center p-8 text-center"
            >
              <History className="mb-4 h-10 w-10 text-[var(--text-muted)] opacity-50" />
              <p className="text-sm font-bold text-[var(--text-muted)]">从左侧列表选择一条记录查看详情。</p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.section>
      </div>
    </motion.div>
  )
}
