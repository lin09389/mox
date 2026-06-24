import { Loader2, ListRestart, Pause, Play, Square, Wifi, WifiOff } from 'lucide-react'

export default function AttackLoopToolbar({
  isRunning,
  isPaused,
  connectionMode,
  canStart,
  onStart,
  onPause,
  onResume,
  onStop,
}) {
  return (
    <div className="flex items-center gap-3">
      {isRunning && (
        <span className="flex items-center gap-2 rounded-full border border-[var(--border-glass-strong)] bg-[var(--bg-glass-strong)] px-3 py-1.5 text-xs font-bold text-[var(--text-main)] shadow-sm backdrop-blur-md">
          {connectionMode === 'ws' ? (
            <><Wifi className="h-3.5 w-3.5 text-emerald-500" /> 实时链路</>
          ) : connectionMode === 'polling' ? (
            <><WifiOff className="h-3.5 w-3.5 text-amber-500" /> 轮询降级</>
          ) : (
            <><Loader2 className="h-3.5 w-3.5 animate-spin text-cyan-500" /> 握手中</>
          )}
        </span>
      )}
      {isRunning ? (
        <div className="flex gap-2">
          {isPaused ? (
            <button onClick={onResume} className="btn-primary bg-emerald-500 hover:bg-emerald-600 border-emerald-500/20 text-white shadow-[0_0_15px_rgba(16,185,129,0.2)]">
              <Play className="h-4 w-4" /> 恢复执行
            </button>
          ) : (
            <button onClick={onPause} className="btn-primary bg-amber-500 hover:bg-amber-600 border-amber-500/20 text-white shadow-[0_0_15px_rgba(245,158,11,0.2)]">
              <Pause className="h-4 w-4" /> 挂起任务
            </button>
          )}
          <button onClick={onStop} className="btn-secondary bg-rose-500 hover:bg-rose-600 text-white border-transparent">
            <Square className="h-4 w-4" /> 终止
          </button>
        </div>
      ) : (
        <button onClick={onStart} disabled={!canStart} className="btn-primary disabled:opacity-50">
          <ListRestart className="h-4 w-4" /> 启动编排任务
        </button>
      )}
    </div>
  )
}