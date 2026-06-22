import { Handle, Position } from '@xyflow/react'
import { Database, Settings } from 'lucide-react'

export default function DatasetNode({ data }) {
  return (
    <div className="bg-[var(--bg-glass-strong)] border border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.15)] rounded-xl w-56 backdrop-blur-md overflow-hidden relative group">
      
      <div className="px-4 py-3 border-b border-[var(--border-glass)] flex items-center justify-between bg-blue-500/10">
        <div className="flex items-center gap-2 text-blue-400 font-bold">
          <Database className="w-5 h-5" />
          {data.label || 'Dataset'}
        </div>
        <button className="text-[var(--text-muted)] hover:text-blue-400 transition-colors">
          <Settings className="w-4 h-4" />
        </button>
      </div>

      <div className="p-4 space-y-3">
        <div className="text-xs text-[var(--text-muted)]">
          <span className="font-mono text-[var(--text-main)] block mb-1">SOURCE:</span>
          {data.source || 'OWASP Top 10 (2024)'}
        </div>
        <div className="text-xs text-[var(--text-muted)]">
          <span className="font-mono text-[var(--text-main)] block mb-1">SIZE:</span>
          {data.size || '1,024 records'}
        </div>
      </div>

      {/* Output Handle only */}
      <Handle type="source" position={Position.Right} className="w-3 h-3 bg-blue-500 border-2 border-[var(--bg-main)]" />
    </div>
  )
}
