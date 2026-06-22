import { Link } from 'react-router-dom'
import { ArrowRight, FileText } from 'lucide-react'
import { buildGovernanceReportLink } from '../../api'

export default function RunCompleteBanner({ reportId, title, description, demo = false }) {
  if (!reportId && !demo) return null

  const href = demo ? '/governance?tab=reports' : buildGovernanceReportLink(reportId)
  const detail =
    description ||
    (demo
      ? '演示模式：报告未实际入库，可在治理中心查看示例报告。'
      : `报告 ID #${reportId}，可在治理中心查看与下载。`)

  return (
    <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/10 p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <FileText className="h-5 w-5 text-cyan-500 shrink-0" />
        <div>
          <p className="text-sm font-bold text-[var(--text-main)]">{title}</p>
          <p className="text-xs text-[var(--text-muted)]">{detail}</p>
        </div>
      </div>
      <Link
        to={href}
        className="btn-secondary inline-flex items-center gap-2 text-xs font-bold text-cyan-500 border-cyan-500/30 hover:bg-cyan-500/10 shrink-0"
      >
        查看报告
        <ArrowRight className="h-3.5 w-3.5" />
      </Link>
    </div>
  )
}