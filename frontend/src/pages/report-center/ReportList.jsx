import { motion } from 'framer-motion'
import { Download, Eye, Trash2 } from 'lucide-react'
import { TableMobileFallback } from '../../components/ui/AppFrame'
import { FOCUSABLE_ROW_CLASS, handleRowKeyDown } from '../../utils/a11y'
import { TYPE_LABEL } from './constants'

export default function ReportList({
  reports,
  loading,
  selected,
  highlightId,
  onSelect,
  onDownload,
  onDelete,
}) {
  return (
    <section className="card overflow-hidden">
      <div className="border-b border-[var(--border-glass)] bg-[var(--bg-glass-strong)] px-5 py-4">
        <h2 className="text-lg font-bold font-display text-[var(--text-main)]">报告列表</h2>
        <p className="mt-1 text-sm font-medium text-[var(--text-muted)]">
          {loading ? '正在从后端加载报告…' : '按报告类型与模型查看历史结论。'}
        </p>
      </div>

      {!loading && reports.length > 0 && (
        <div className="p-4">
          <TableMobileFallback
            items={reports}
            onItemActivate={onSelect}
            getItemId={(report) => `report-row-${report.id}`}
            getCardClassName={(report) => {
              const isHighlighted = highlightId === report.id
              const isSelected = selected?.id === report.id
              return [
                isSelected ? 'border-l-2 border-l-cyan-500 bg-[var(--bg-glass-strong)]' : '',
                isHighlighted ? 'ring-2 ring-inset ring-cyan-500/40 bg-cyan-500/5' : '',
              ].filter(Boolean).join(' ')
            }}
            renderTitle={(report) => report.report_name}
            renderMeta={(report) => (
              <>
                <p>{TYPE_LABEL[report.report_type] || report.report_type} · {report.model_name}</p>
                <p>
                  攻击 {Math.round(report.attack_success_rate * 100)}% / 防御 {Math.round(report.defense_success_rate * 100)}%
                </p>
                <p>{report.created_at}</p>
              </>
            )}
            renderRight={(report) => (
              <div className="flex shrink-0 flex-col gap-1.5" onClick={(e) => e.stopPropagation()}>
                <button type="button" className="btn-secondary px-2 py-1 text-xs" onClick={() => onSelect(report)}>
                  <Eye className="h-3.5 w-3.5 inline mr-1" />
                  查看
                </button>
                <button type="button" className="btn-secondary px-2 py-1 text-xs" onClick={() => onDownload(report)}>
                  <Download className="h-3.5 w-3.5 inline mr-1" />
                  下载
                </button>
                <button
                  type="button"
                  className="btn-ghost px-2 py-1 text-xs text-rose-500 hover:bg-rose-500/10"
                  onClick={() => onDelete(report)}
                >
                  <Trash2 className="h-3.5 w-3.5 inline mr-1" />
                  删除
                </button>
              </div>
            )}
          />
        </div>
      )}

      <div className="hidden md:block overflow-x-auto">
        <table className="w-full text-left text-sm text-[var(--text-main)]">
          <thead className="bg-[var(--bg-glass-strong)] text-[var(--text-muted)] font-bold uppercase tracking-wider text-xs border-b border-[var(--border-glass)]">
            <tr>
              <th className="px-6 py-4">报告名称</th>
              <th className="px-6 py-4">类型</th>
              <th className="px-6 py-4">模型</th>
              <th className="px-6 py-4 text-center">风险指标</th>
              <th className="px-6 py-4">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-glass)]">
            {reports.map((report) => {
              const isHighlighted = highlightId === report.id
              const isSelected = selected?.id === report.id
              return (
                <motion.tr
                  id={`report-row-${report.id}`}
                  key={report.id}
                  tabIndex={0}
                  role="button"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className={`hover:bg-[var(--bg-glass)] transition-colors cursor-pointer ${FOCUSABLE_ROW_CLASS} ${
                    isSelected ? 'bg-[var(--bg-glass-strong)] border-l-2 border-l-cyan-500' : ''
                  } ${isHighlighted ? 'ring-2 ring-inset ring-cyan-500/40 bg-cyan-500/5' : ''}`}
                  onClick={() => onSelect(report)}
                  onKeyDown={(event) => handleRowKeyDown(event, () => onSelect(report))}
                >
                  <td className="px-6 py-4 font-medium">{report.report_name}</td>
                  <td className="px-6 py-4">
                    <span className="badge badge-neutral bg-[var(--bg-glass-strong)] border-[var(--border-glass)]">
                      {TYPE_LABEL[report.report_type] || report.report_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono font-bold text-[var(--text-muted)]">{report.model_name}</td>
                  <td className="px-6 py-4 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <span className="text-rose-500 font-mono font-bold" title="攻击成功率">
                        {Math.round(report.attack_success_rate * 100)}%
                      </span>
                      <span className="text-[var(--text-muted)]">/</span>
                      <span className="text-emerald-500 font-mono font-bold" title="防御成功率">
                        {Math.round(report.defense_success_rate * 100)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4" onClick={(e) => e.stopPropagation()}>
                    <div className="flex gap-2">
                      <button type="button" className="btn-secondary px-2.5 py-1.5 hover:text-cyan-500 hover:border-cyan-500/50" onClick={() => onSelect(report)}>
                        <Eye className="h-4 w-4" />
                      </button>
                      <button type="button" className="btn-secondary px-2.5 py-1.5" onClick={() => onDownload(report)}>
                        <Download className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        className="btn-ghost px-2.5 py-1.5 text-rose-500 hover:bg-rose-500/10"
                        onClick={() => onDelete(report)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </motion.tr>
              )
            })}
            {reports.length === 0 && !loading && (
              <tr>
                <td colSpan="5" className="p-8 text-center text-[var(--text-muted)] font-bold">
                  暂无报告。运行攻击循环测试后，结果将自动归档至此。
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}