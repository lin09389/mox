import { Link } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowRight, Eye, FileText, History } from 'lucide-react'
import { buildGovernanceReportLink } from '../../api'
import { useReportDetail } from '../../hooks/useReportDetail'
import { Skeleton } from '../../components/ui/AppFrame'
import ReportDetailPanel from '../../components/report/ReportDetailPanel'
import {
  ATTACK_LABELS,
  DEFENSE_LABELS,
  badgeForAttackResult,
  badgeForDefenseResult,
  formatDate,
} from './constants'

export default function HistoryRecordDetail({ isAttack, selectedRecord, linkedReportId }) {
  const linkedReport = linkedReportId ? { id: linkedReportId } : null
  const { detailLoading: reportDetailLoading, detailContent: reportDetail } = useReportDetail(linkedReport)

  return (
    <section className="card bg-[var(--bg-glass-strong)] border-cyan-500/10 h-fit lg:sticky lg:top-6">
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
                <span
                  className={`badge ${
                    isAttack
                      ? badgeForAttackResult(selectedRecord.result)
                      : badgeForDefenseResult(selectedRecord.is_malicious)
                  }`}
                >
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
                  <ReportDetailPanel
                    report={linkedReport}
                    content={reportDetail}
                  />
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
    </section>
  )
}