import { Handle, Position } from '@xyflow/react'
import { Cpu, Settings } from 'lucide-react'

export default function AgentNode({ data }) {
  return (
    <div className="bg-[var(--bg-glass-strong)] border border-rose-500/50 shadow-[0_0_15px_rgba(244,63,94,0.15)] rounded-xl w-64 backdrop-blur-md overflow-hidden relative group">
      {/* Input Handle */}
      <Handle type="target" position={Position.Left} className="w-3 h-3 bg-rose-500 border-2 border-[var(--bg-main)]" />
      
      <div className="px-4 py-3 border-b border-[var(--border-glass)] flex items-center justify-between bg-rose-500/10">
        <div className="flex items-center gap-2 text-rose-500 font-bold">
          <Cpu className="w-5 h-5" />
          {data.label || 'Attacker Agent'}
        </div>
        <button className="text-[var(--text-muted)] hover:text-rose-400 transition-colors">
          <Settings className="w-4 h-4" />
        </button>
      </div>

      <div className="p-4 space-y-3">
        <div className="text-xs text-[var(--text-muted)]">
          <span className="font-mono text-[var(--text-main)] block mb-1">STRATEGY:</span>
          {data.strategy || 'DAN Jailbreak (Dynamic)'}
        </div>
        <div className="text-xs text-[var(--text-muted)]">
          <span className="font-mono text-[var(--text-main)] block mb-1">MODEL:</span>
          {data.model || 'gpt-4o'}
        </div>
      </div>

      {/* Output Handle */}
      <Handle type="source" position={Position.Right} className="w-3 h-3 bg-rose-500 border-2 border-[var(--bg-main)]" />
    </div>
  )
}
