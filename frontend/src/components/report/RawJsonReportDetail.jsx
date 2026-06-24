import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

export default function RawJsonReportDetail({ content, isDemo, defaultExpanded = false }) {
  const [expanded, setExpanded] = useState(defaultExpanded)

  return (
    <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-main)]/40 p-4">
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="flex w-full items-center justify-between text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]"
      >
        <span>{isDemo ? '演示报告原始数据' : '原始 JSON 数据'}</span>
        {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>
      {expanded && (
        <pre className="mt-3 max-h-[280px] overflow-auto text-xs font-mono leading-relaxed text-[var(--text-main)] whitespace-pre-wrap break-words">
          {JSON.stringify(content, null, 2)}
        </pre>
      )}
    </div>
  )
}