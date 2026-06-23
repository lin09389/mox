import { useEffect, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Clock3, Eye, ListTodo, Loader2, Play, RefreshCw, XCircle, Terminal } from 'lucide-react'
import { tasksApi, isDemoModeEnabled } from '../api'
import { MetricCard, PanelHeader, ProgressMeter } from '../components/ui/AppFrame'
import { getTaskHref, normalizeRemoteTask } from '../utils/taskTrayHelpers'

const statusConfig = {
  running: { label: '执行中', tone: 'warning', badge: 'bg-amber-500/10 text-amber-500 border-amber-500/20' },
  completed: { label: '已完成', tone: 'success', badge: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' },
  failed: { label: '中止/失败', tone: 'danger', badge: 'bg-rose-500/10 text-rose-500 border-rose-500/20' },
  pending: { label: '等待队列', tone: 'electric', badge: 'bg-[var(--bg-glass-strong)] text-[var(--text-muted)] border-[var(--border-glass)]' },
}

function fallbackTasks() {
  return [
    { id: 'task-001', name: 'GPT-4 批量攻击盲测', status: 'running', progress: 65, total: 100, completed: 65, failed: 3, start_time: '2026-03-31 10:00:00' },
    { id: 'task-002', name: '防御策略回归引擎评估', status: 'running', progress: 35, total: 80, completed: 28, failed: 2, start_time: '2026-03-31 10:15:00' },
    { id: 'task-003', name: 'AdvBench 基准靶机联调', status: 'pending', progress: 0, total: 200, completed: 0, failed: 0, start_time: '-' },
    { id: 'task-004', name: '夜间静默安全巡检', status: 'completed', progress: 100, total: 120, completed: 120, failed: 4, start_time: '2026-03-30 23:00:00' },
    { id: 'task-005', name: '多模态攻击全量批处理', status: 'failed', progress: 48, total: 90, completed: 43, failed: 9, start_time: '2026-03-30 19:00:00' },
  ]
}

import { containerVariants, itemVariants } from '../utils/animations'

export default function TaskProgressPage() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedTask, setSelectedTask] = useState(null)

  const fetchTasks = async () => {
    setLoading(true)
    try {
      const data = await tasksApi.list()
      setTasks((data || []).map(normalizeRemoteTask))
    } catch {
      if (isDemoModeEnabled) {
        setTasks(fallbackTasks().map(normalizeRemoteTask))
      } else {
        setTasks([])
      }
    }
    setLoading(false)
  }

  useEffect(() => {
    let mounted = true
    const init = async () => {
      if (mounted) fetchTasks()
    }
    init()
    const interval = window.setInterval(fetchTasks, 6000)
    return () => {
      mounted = false
      window.clearInterval(interval)
    }
  }, [])

  const metrics = useMemo(() => {
    const total = tasks.length
    const running = tasks.filter((item) => item.status === 'running').length
    const completed = tasks.filter((item) => item.status === 'completed').length
    const failed = tasks.filter((item) => item.status === 'failed').length
    return { total, running, completed, failed }
  }, [tasks])

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="page-shell">
      <motion.div variants={itemVariants} className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-2 max-w-2xl">
          <p className="text-sm font-medium text-[var(--text-muted)]">
            查看攻击循环、自动红队与基准评测等后台任务进度，支持定时同步与进程切面分析。
          </p>
        </div>
        <button type="button" onClick={fetchTasks} className="btn-secondary h-[42px] px-6 text-cyan-500 border-[var(--border-glass)] hover:border-cyan-500/30 shrink-0">
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          刷新任务
        </button>
      </motion.div>

      <motion.div variants={itemVariants} className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard icon={ListTodo} label="节点任务总量" value={metrics.total} hint="调度栈全量作业" tone="electric" />
        <MetricCard icon={Play} label="活跃执行引擎" value={metrics.running} hint="占用算力进程" tone="amber" />
        <MetricCard icon={Clock3} label="合规完结项" value={metrics.completed} hint="顺利终止闭环" tone="neon" />
        <MetricCard icon={XCircle} label="熔断/故障进程" value={metrics.failed} hint="触发系统级异常" tone="lava" />
      </motion.div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <motion.section variants={itemVariants} className="card p-6 h-fit lg:sticky lg:top-6 border-[var(--border-glass)]">
          <PanelHeader title="调度器日志流" description="点击指定节点查看详尽的执行内存栈。" />
          {loading && tasks.length === 0 ? (
            <div className="flex min-h-[360px] items-center justify-center">
              <div className="w-10 h-10 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin"></div>
            </div>
          ) : (
            <div className="space-y-3">
              <AnimatePresence>
                {tasks.map((task) => {
                  const isSelected = selectedTask?.id === task.id
                  return (
                    <motion.button
                      layout
                      initial={{ opacity: 0, scale: 0.98 }}
                      animate={{ opacity: 1, scale: 1 }}
                      type="button"
                      key={task.id}
                      onClick={() => setSelectedTask(task)}
                      className={`w-full rounded-xl border p-4 text-left transition-all duration-300 ${
                        isSelected
                          ? 'border-cyan-500/50 bg-cyan-500/10 shadow-[inset_0_0_15px_rgba(6,182,212,0.1)] transform scale-[1.02]'
                          : 'border-[var(--border-glass)] bg-[var(--bg-glass)] hover:bg-[var(--bg-glass-strong)] hover:border-cyan-500/30'
                      }`}
                    >
                      <div className="mb-3 flex items-center justify-between">
                        <p className={`text-sm font-bold font-display transition-colors ${isSelected ? 'text-cyan-500' : 'text-[var(--text-main)]'}`}>{task.name}</p>
                        <span className={`badge border text-[10px] uppercase font-bold tracking-widest ${statusConfig[task.status]?.badge || 'bg-[var(--bg-glass-strong)] text-[var(--text-muted)] border-[var(--border-glass)]'}`}>
                          {statusConfig[task.status]?.label || task.status}
                        </span>
                      </div>
                      <ProgressMeter value={task.progress || 0} tone={statusConfig[task.status]?.tone || 'electric'} label="进程切片进度" />
                      {task.source && task.status === 'running' ? (
                        <Link
                          to={getTaskHref(task)}
                          onClick={(event) => event.stopPropagation()}
                          className="mt-3 inline-flex text-xs font-bold text-cyan-500 hover:underline"
                        >
                          打开来源页面 →
                        </Link>
                      ) : null}
                    </motion.button>
                  )
                })}
              </AnimatePresence>
            </div>
          )}
        </motion.section>

        <motion.section variants={itemVariants} className="card p-6 bg-[var(--bg-glass-strong)] border-[var(--border-glass)] shadow-[inset_0_0_40px_rgba(6,182,212,0.02)]">
          <PanelHeader title="进程切面分析" description="监控独立任务周期的失败样本流与时延特征。" />
          
          <AnimatePresence mode="wait">
            {selectedTask ? (
              <motion.div 
                key={selectedTask.id}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="space-y-5"
              >
                <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-5 relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-4 opacity-10">
                    <Terminal className="h-24 w-24" />
                  </div>
                  <div className="relative z-10">
                    <p className="text-lg font-bold font-display text-[var(--text-main)]">{selectedTask.name}</p>
                    <p className="mt-1 text-xs font-mono font-medium text-[var(--text-muted)]">UUID: {selectedTask.id}</p>
                  </div>
                </div>
                
                <div className="grid gap-4 sm:grid-cols-2">
                  <MetricCard icon={Play} label="已完成载荷" value={selectedTask.completed || 0} hint={`靶机池总容量 ${selectedTask.total || 0}`} tone="neon" />
                  <MetricCard icon={XCircle} label="被拦截样本" value={selectedTask.failed || 0} hint="触发防御阈值" tone="lava" />
                </div>
                
                <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-5">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">初始唤醒时戳</p>
                    <p className="text-sm font-mono font-bold text-[var(--text-main)]">{selectedTask.start_time || 'UNAVAILABLE'}</p>
                  </div>
                  <div className="mt-6">
                    <ProgressMeter value={selectedTask.progress || 0} tone={statusConfig[selectedTask.status]?.tone || 'electric'} label="当前子循环推演进度" />
                  </div>
                </div>
              </motion.div>
            ) : (
              <motion.div 
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex min-h-[400px] flex-col items-center justify-center gap-4 text-center p-8"
              >
                <div className="w-20 h-20 rounded-full bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] flex items-center justify-center">
                  <Eye className="h-10 w-10 text-[var(--text-muted)] opacity-60" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[var(--text-main)]">暂无活动焦点</h3>
                  <p className="mt-2 text-sm font-medium text-[var(--text-muted)] max-w-sm">
                    点击左侧总线列表中的任意任务，即时挂载分析该进程的系统上下文。
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.section>
      </div>
    </motion.div>
  )
}
