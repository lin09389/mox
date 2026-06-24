import { AnimatePresence, motion } from 'framer-motion'
import { Clock3, Download, Eye, FileText, Shield, TrendingUp } from 'lucide-react'
import { Skeleton } from '../../components/ui/AppFrame'
import ReportDetailPanel from '../../components/report/ReportDetailPanel'
import { TYPE_LABEL } from './constants'

export default function ReportPreviewPanel({
  selected,
  detailLoading,
  detailContent,
  onDownload,
}) {
  return (
    <section className="card bg-[var(--bg-glass-strong)] border-cyan-500/10 shadow-[inset_0_0_40px_rgba(6,182,212,0.03)] h-fit lg:sticky lg:top-6">
      <div className="border-b border-[var(--border-glass)] px-5 py-4">
        <h2 className="text-lg font-bold font-display text-[var(--text-main)] flex items-center gap-2">
          <Eye className="h-5 w-5 text-cyan-500" />
          报告预览
        </h2>
        <p className="mt-1 text-sm font-medium text-[var(--text-muted)]">选中左侧任一报告查看关键摘要。</p>
      </div>

      <AnimatePresence mode="wait">
        {selected ? (
          <motion.div
            key={selected.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="p-5 space-y-5"
          >
            <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-5 shadow-sm">
              <h3 className="text-base font-bold text-[var(--text-main)] mb-1">{selected.report_name}</h3>
              <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-muted)] mb-4">
                <Clock3 className="h-3.5 w-3.5" /> {selected.created_at}
              </div>
              <div className="flex flex-wrap gap-2">
                <span className="badge badge-info bg-cyan-500/10 text-cyan-500 border-cyan-500/20">
                  {TYPE_LABEL[selected.report_type] || selected.report_type}
                </span>
                <span className="badge badge-neutral bg-[var(--bg-glass-strong)] border-[var(--border-glass)] font-mono">
                  {selected.model_name}
                </span>
                <span className="badge badge-neutral bg-amber-500/10 text-amber-500 border-amber-500/20 uppercase tracking-widest text-[10px]">
                  {selected.format}
                </span>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 text-center">
                <TrendingUp className="h-6 w-6 text-rose-500 mx-auto mb-2" />
                <div className="text-2xl font-mono font-bold text-rose-500">
                  {Math.round(selected.attack_success_rate * 100)}%
                </div>
                <div className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)] mt-1">攻击成功率</div>
              </div>
              <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-center">
                <Shield className="h-6 w-6 text-emerald-500 mx-auto mb-2" />
                <div className="text-2xl font-mono font-bold text-emerald-500">
                  {Math.round(selected.defense_success_rate * 100)}%
                </div>
                <div className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)] mt-1">防御成功率</div>
              </div>
            </div>

            {detailLoading ? (
              <div className="space-y-2 rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-main)]/40 p-4">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-[200px] w-full" />
              </div>
            ) : detailContent ? (
              <ReportDetailPanel
                report={selected}
                content={detailContent}
                isDemo={Boolean(selected._demo_mode)}
              />
            ) : null}

            <button
              onClick={() => onDownload(selected)}
              className="btn-primary w-full bg-cyan-500 hover:bg-cyan-600 border-cyan-500 text-white shadow-[0_0_15px_rgba(6,182,212,0.3)]"
            >
              <Download className="h-4 w-4" />
              {selected._demo_mode ? '导出演示 JSON' : '完整导出报告'}
            </button>
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col min-h-[300px] items-center justify-center p-8 text-center"
          >
            <div className="w-16 h-16 rounded-2xl bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] flex items-center justify-center mb-4">
              <FileText className="h-8 w-8 text-[var(--text-muted)] opacity-50" />
            </div>
            <p className="text-sm font-bold text-[var(--text-muted)] opacity-80">
              从左侧报告列表选择一项查看详情。
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  )
}