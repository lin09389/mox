import { motion } from 'framer-motion'
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  XCircle,
  Zap,
} from 'lucide-react'

export default function AttackLoopProgressPanel({ progress }) {
  return (
    <motion.div
      key="progress"
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      className="space-y-6"
    >
      {progress ? (
        <>
          <div className="card p-6">
            <h3 className="mb-6 flex items-center gap-3 text-lg font-bold font-display text-[var(--text-main)]">
              <div className="p-1.5 bg-cyan-500/10 rounded-lg"><Activity className="h-5 w-5 text-cyan-500" /></div>
              编排执行轨道
            </h3>
            <div className="space-y-6">
              <div>
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="font-bold text-[var(--text-muted)] uppercase tracking-wider text-xs">
                    {progress.completed} / {progress.total} 测试完成
                  </span>
                  <span className="font-mono font-bold text-cyan-500 text-lg">
                    {progress.progress_percent?.toFixed(1)}%
                  </span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-[var(--bg-glass-strong)] border border-[var(--border-glass)]">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-cyan-600"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress.progress_percent || 0}%` }}
                    transition={{ duration: 0.5, ease: 'easeOut' }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div className="rounded-2xl border border-[var(--border-glass)] bg-emerald-500/5 p-4 text-center">
                  <CheckCircle2 className="h-6 w-6 text-emerald-500 mx-auto mb-2" />
                  <span className="text-3xl font-mono font-bold text-emerald-500">{progress.successful || 0}</span>
                  <div className="mt-1 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">成功突破</div>
                </div>
                <div className="rounded-2xl border border-[var(--border-glass)] bg-rose-500/5 p-4 text-center">
                  <XCircle className="h-6 w-6 text-rose-500 mx-auto mb-2" />
                  <span className="text-3xl font-mono font-bold text-rose-500">{progress.failed || 0}</span>
                  <div className="mt-1 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">被防御拦截</div>
                </div>
                <div className="rounded-2xl border border-[var(--border-glass)] bg-amber-500/5 p-4 text-center">
                  <AlertTriangle className="h-6 w-6 text-amber-500 mx-auto mb-2" />
                  <span className="text-3xl font-mono font-bold text-amber-500">{progress.errors || 0}</span>
                  <div className="mt-1 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">引擎错误</div>
                </div>
                <div className="rounded-2xl border border-[var(--border-glass)] bg-[var(--bg-glass-strong)] p-4 text-center">
                  <Clock className="h-6 w-6 text-cyan-500 mx-auto mb-2" />
                  <span className="text-3xl font-mono font-bold text-[var(--text-main)]">{progress.eta_seconds?.toFixed(0) || 0}s</span>
                  <div className="mt-1 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">预计剩余时间</div>
                </div>
              </div>

              <div className="flex items-center gap-6 text-sm font-medium text-[var(--text-muted)] bg-[var(--bg-glass-strong)] p-3 rounded-lg border border-[var(--border-glass)] w-fit">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-cyan-500" />
                  <span className="font-mono">{progress.rate_per_second?.toFixed(2)}</span> Ops/sec
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-cyan-500" />
                  已历时 <span className="font-mono">{progress.elapsed_seconds?.toFixed(0)}</span>s
                </div>
              </div>
            </div>
          </div>

          <div className="card p-6 flex justify-between items-center">
            <h4 className="text-sm font-bold text-[var(--text-main)]">任务守护状态</h4>
            <div className="flex items-center gap-3">
              {progress.status === 'running' && (
                <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 px-4 py-2 rounded-lg">
                  <div className="h-2 w-2 animate-ping rounded-full bg-emerald-500" />
                  <span className="font-bold text-emerald-500 text-sm tracking-wide">执行中</span>
                </div>
              )}
              {progress.status === 'paused' && (
                <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/20 px-4 py-2 rounded-lg">
                  <div className="h-2 w-2 rounded-full bg-amber-500" />
                  <span className="font-bold text-amber-500 text-sm tracking-wide">已挂起</span>
                </div>
              )}
              {progress.status === 'completed' && (
                <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 px-4 py-2 rounded-lg">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  <span className="font-bold text-emerald-500 text-sm tracking-wide">编排完成</span>
                </div>
              )}
            </div>
          </div>
        </>
      ) : (
        <div className="card p-16 flex flex-col items-center text-center opacity-60 border-dashed">
          <Activity className="h-12 w-12 text-[var(--text-muted)] mb-4" />
          <h3 className="text-lg font-bold text-[var(--text-main)]">编排引擎待命</h3>
          <p className="mt-2 text-sm font-medium text-[var(--text-muted)]">请在配置面板确认参数后启动编排任务。</p>
        </div>
      )}
    </motion.div>
  )
}