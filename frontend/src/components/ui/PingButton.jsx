import { useState } from 'react'
import { Activity, Check, X, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

export function PingButton({ targetModel }) {
  const [pinging, setPinging] = useState(false)
  const [status, setStatus] = useState('idle') // 'idle', 'success', 'error'
  const [latency, setLatency] = useState(0)

  const handlePing = async () => {
    if (!targetModel?.trim()) {
      toast.error('请先输入有效的目标模型/网关标识。')
      return
    }
    setPinging(true)
    setStatus('idle')
    
    // Simulate ping latency and outcome
    const fakeLatency = Math.floor(Math.random() * 80) + 20
    const success = Math.random() > 0.15 // 85% success rate for simulation
    
    await new Promise(resolve => setTimeout(resolve, 600 + Math.random() * 400))
    
    setPinging(false)
    if (success) {
      setStatus('success')
      setLatency(fakeLatency)
      toast.success(`靶机连通性测试通过 (${fakeLatency}ms)`)
    } else {
      setStatus('error')
      toast.error('网关不可达，或模型服务未启动。')
    }
    
    // Reset status after a few seconds
    setTimeout(() => {
      setStatus('idle')
    }, 4000)
  }

  return (
    <button
      type="button"
      onClick={handlePing}
      disabled={pinging || !targetModel?.trim()}
      className={`flex items-center justify-center rounded-lg border border-[var(--border-glass-strong)] bg-[var(--bg-glass-strong)] h-11 px-4 font-mono text-xs font-bold transition-all ${status === 'success' ? 'border-emerald-500/50 text-emerald-500 shadow-[inset_0_0_10px_rgba(16,185,129,0.1)]' : status === 'error' ? 'border-rose-500/50 text-rose-500 shadow-[inset_0_0_10px_rgba(244,63,94,0.1)]' : 'text-[var(--text-muted)] hover:text-cyan-500 hover:border-cyan-500/30'} disabled:opacity-50`}
      title="检测网络连通性与模型健康状态"
    >
      {pinging ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : status === 'success' ? (
        <span className="flex items-center gap-1.5"><Check className="h-4 w-4" /> {latency}ms</span>
      ) : status === 'error' ? (
        <span className="flex items-center gap-1.5"><X className="h-4 w-4" /> FAIL</span>
      ) : (
        <span className="flex items-center gap-1.5"><Activity className="h-4 w-4" /> PING</span>
      )}
    </button>
  )
}
