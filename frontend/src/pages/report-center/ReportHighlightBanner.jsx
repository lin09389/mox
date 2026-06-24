import { motion } from 'framer-motion'
import { Sparkles, X } from 'lucide-react'
import { itemVariants } from '../../utils/animations'

export default function ReportHighlightBanner({ highlightId, onDismiss }) {
  if (!highlightId) return null

  return (
    <motion.div
      variants={itemVariants}
      className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
    >
      <div className="flex items-center gap-3">
        <Sparkles className="h-5 w-5 text-cyan-500" />
        <div>
          <p className="text-sm font-bold text-[var(--text-main)]">正在查看刚生成的报告</p>
          <p className="text-xs text-[var(--text-muted)]">报告 ID #{highlightId} 已高亮显示在列表中。</p>
        </div>
      </div>
      <button type="button" className="btn-secondary text-xs font-bold text-cyan-500" onClick={onDismiss}>
        <X className="h-3.5 w-3.5" />
        取消高亮
      </button>
    </motion.div>
  )
}