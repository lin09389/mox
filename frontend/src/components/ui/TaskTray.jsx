import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Activity, Loader2, X, Minimize2 } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { useTaskStore } from '../../store/useTaskStore'

export function TaskTray() {
  const location = useLocation()
  const { tasks, minimized, closed, setMinimized, setClosed, fetchTasks } = useTaskStore()

  useEffect(() => {
    fetchTasks()
    const interval = setInterval(fetchTasks, 5000)
    return () => clearInterval(interval)
  }, [fetchTasks])

  // Hide the tray if we are on the tasks hub page, or if the user dismissed it, or if no running tasks
  if (closed || tasks.length === 0 || location.pathname === '/tasks') return null

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3 pointer-events-none">
      <AnimatePresence>
        {!minimized && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="pointer-events-auto w-[320px] rounded-xl border border-cyan-500/20 bg-[var(--bg-glass-strong)] shadow-[0_10px_40px_rgba(0,0,0,0.5)] backdrop-blur-xl overflow-hidden"
          >
            <div className="bg-cyan-500/10 border-b border-cyan-500/20 px-4 py-2.5 flex items-center justify-between">
              <div className="flex items-center gap-2 text-cyan-500">
                <Activity className="h-4 w-4 animate-pulse" />
                <span className="text-xs font-bold uppercase tracking-widest">后台演练进行中 ({tasks.length})</span>
              </div>
              <div className="flex items-center gap-1">
                <button onClick={() => setMinimized(true)} className="p-1 hover:bg-cyan-500/20 rounded text-cyan-500 transition-colors"><Minimize2 className="h-3.5 w-3.5" /></button>
                <button onClick={() => setClosed(true)} className="p-1 hover:bg-cyan-500/20 rounded text-cyan-500 transition-colors"><X className="h-3.5 w-3.5" /></button>
              </div>
            </div>
            <div className="p-4 space-y-4 max-h-[240px] overflow-y-auto">
              {tasks.map((task) => (
                <Link
                  key={task.id}
                  to={task.href || '/tasks'}
                  className="block space-y-2 rounded-lg border border-transparent p-2 -mx-2 transition-colors hover:border-cyan-500/20 hover:bg-cyan-500/5"
                >
                  <div className="flex justify-between items-center text-xs gap-2">
                    <span className="font-bold text-[var(--text-main)] truncate">{task.name}</span>
                    <span className="font-mono text-cyan-500 font-bold shrink-0">{task.progress ?? 0}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-[var(--bg-glass)] rounded-full overflow-hidden border border-[var(--border-glass)]">
                    <div
                      className="h-full bg-gradient-to-r from-cyan-400 to-cyan-600 transition-all duration-1000 ease-linear shadow-[0_0_10px_rgba(6,182,212,0.5)]"
                      style={{ width: `${task.progress ?? 0}%` }}
                    />
                  </div>
                </Link>
              ))}
            </div>
            <Link to="/tasks" className="block text-center border-t border-[var(--border-glass)] py-2.5 text-[10px] text-[var(--text-muted)] hover:text-cyan-500 hover:bg-[var(--bg-glass)] transition-colors uppercase font-bold tracking-widest">
              打开完整任务控制台
            </Link>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {minimized && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={() => setMinimized(false)}
            className="pointer-events-auto h-12 w-12 rounded-full border border-cyan-500/30 bg-[var(--bg-glass-strong)] shadow-[0_0_20px_rgba(6,182,212,0.2)] backdrop-blur-xl flex items-center justify-center text-cyan-500 hover:bg-cyan-500/10 hover:border-cyan-500 transition-all group"
          >
            <div className="relative">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-cyan-500 text-[9px] font-bold text-white shadow-[0_0_10px_rgba(6,182,212,0.5)]">
                {tasks.length}
              </span>
            </div>
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  )
}
