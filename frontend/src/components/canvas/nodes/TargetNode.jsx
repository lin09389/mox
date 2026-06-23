import { Handle, Position } from '@xyflow/react'
import { Server, Settings } from 'lucide-react'

export default function TargetNode({ data }) {
  return (
    <div className="bg-[var(--bg-glass-strong)] border border-purple-500/50 shadow-[0_0_15px_rgba(168,85,247,0.15)] rounded-xl w-64 backdrop-blur-md overflow-hidden relative group">
      {/* Input Handle */}
      <Handle type="target" position={Position.Left} className="w-3 h-3 bg-purple-500 border-2 border-[var(--bg-main)]" />
      
      <div className="px-4 py-3 border-b border-[var(--border-glass)] flex items-center justify-between bg-purple-500/10">
        <div className="flex items-center gap-2 text-purple-400 font-bold">
          <Server className="w-5 h-5" />
          {data.label || 'Target Asset'}
        </div>
        <button className="text-[var(--text-muted)] hover:text-purple-400 transition-colors">
          <Settings className="w-4 h-4" />
        </button>
      </div>

      <div className="p-4 space-y-3">
        <div className="text-xs text-[var(--text-muted)]">
          <span className="font-mono text-[var(--text-main)] block mb-1">ENDPOINT:</span>
          {data.endpoint || 'api.example.com/v1/chat'}
        </div>
        <div className="text-xs text-[var(--text-muted)]">
          <span className="font-mono text-[var(--text-main)] block mb-1">DEFENSES:</span>
          {data.defenses ? data.defenses.join(', ') : 'WAF, RateLimit'}
        </div>
      </div>

      {/* Output Handle */}
      <Handle type="source" position={Position.Right} className="w-3 h-3 bg-purple-500 border-2 border-[var(--bg-main)]" />
    </div>
  )
}
