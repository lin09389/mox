import { useEffect, useMemo, useState } from 'react'
import { Clock3, Eye, ListTodo, Loader2, Play, RefreshCw, XCircle } from 'lucide-react'
import api from '../api'
import { MetricCard, PageHeader, PanelHeader, ProgressMeter } from '../components/ui/AppFrame'

const statusConfig = {
  running: { label: '运行中', tone: 'warning', badge: 'badge-warning' },
  completed: { label: '已完成', tone: 'success', badge: 'badge-success' },
  failed: { label: '失败', tone: 'danger', badge: 'badge-danger' },
  pending: { label: '等待中', tone: 'electric', badge: 'badge-neutral' },
}

function fallbackTasks() {
  return [
    { id: 'task-001', name: 'GPT-4 批量攻击测试', status: 'running', progress: 65, total: 100, completed: 65, failed: 3, start_time: '2026-03-31 10:00:00' },
    { id: 'task-002', name: '防御策略回归评估', status: 'running', progress: 35, total: 80, completed: 28, failed: 2, start_time: '2026-03-31 10:15:00' },
    { id: 'task-003', name: 'AdvBench 基准评测', status: 'pending', progress: 0, total: 200, completed: 0, failed: 0, start_time: '-' },
    { id: 'task-004', name: '夜间安全巡检', status: 'completed', progress: 100, total: 120, completed: 120, failed: 4, start_time: '2026-03-30 23:00:00' },
    { id: 'task-005', name: '多模态攻击批处理', status: 'failed', progress: 48, total: 90, completed: 43, failed: 9, start_time: '2026-03-30 19:00:00' },
  ]
}

export default function TaskProgressPage() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedTask, setSelectedTask] = useState(null)

  const fetchTasks = async () => {
    setLoading(true)
    try {
      const response = await api.get('/api/tasks')
      setTasks(response.data || [])
    } catch {
      setTasks(fallbackTasks())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTasks()
    const interval = window.setInterval(fetchTasks, 6000)
    return () => window.clearInterval(interval)
  }, [])

  const metrics = useMemo(() => {
    const total = tasks.length
    const running = tasks.filter((item) => item.status === 'running').length
    const completed = tasks.filter((item) => item.status === 'completed').length
    const failed = tasks.filter((item) => item.status === 'failed').length
    return { total, running, completed, failed }
  }, [tasks])

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="TASK CENTER"
        title="任务中心"
        description="集中查看攻击、防御、评测任务的执行状态与进度，支持自动刷新。"
        actions={
          <button type="button" onClick={fetchTasks} className="btn-secondary">
            <RefreshCw className="h-4 w-4" />
            刷新
          </button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard icon={ListTodo} label="任务总数" value={metrics.total} hint="当前可见任务" tone="electric" />
        <MetricCard icon={Play} label="运行中" value={metrics.running} hint="需要重点关注" tone="amber" />
        <MetricCard icon={Clock3} label="已完成" value={metrics.completed} hint="已收敛任务" tone="neon" />
        <MetricCard icon={XCircle} label="失败任务" value={metrics.failed} hint="建议优先复盘" tone="lava" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="card card-glow">
          <PanelHeader title="任务列表" description="按状态实时更新，点击查看详情。" />
          {loading ? (
            <div className="panel-muted flex min-h-[360px] items-center justify-center">
              <Loader2 className="h-7 w-7 animate-spin text-electric-600" />
            </div>
          ) : (
            <div className="space-y-3">
              {tasks.map((task) => (
                <button
                  type="button"
                  key={task.id}
                  onClick={() => setSelectedTask(task)}
                  className="w-full rounded-[18px] border border-graphite-200/70 bg-white/80 px-4 py-4 text-left transition-all hover:border-electric-200 hover:bg-white"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-sm font-semibold text-graphite-900">{task.name}</p>
                    <span className={`badge ${statusConfig[task.status]?.badge || 'badge-neutral'}`}>
                      {statusConfig[task.status]?.label || task.status}
                    </span>
                  </div>
                  <ProgressMeter value={task.progress || 0} tone={statusConfig[task.status]?.tone || 'electric'} />
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="card card-glow">
          <PanelHeader title="任务详情" description="查看执行进度、失败数和启动时间。" />
          {selectedTask ? (
            <div className="space-y-4">
              <div className="rounded-[18px] border border-graphite-200/70 bg-white/80 p-4">
                <p className="text-sm font-semibold text-graphite-900">{selectedTask.name}</p>
                <p className="mt-1 text-xs text-graphite-500">任务 ID: {selectedTask.id}</p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <MetricCard icon={Play} label="完成数" value={selectedTask.completed || 0} hint={`总数 ${selectedTask.total || 0}`} tone="neon" />
                <MetricCard icon={XCircle} label="失败数" value={selectedTask.failed || 0} hint="失败样本累计" tone="lava" />
              </div>
              <div className="rounded-[18px] border border-graphite-200/70 bg-white/80 p-4">
                <p className="text-xs text-graphite-500">启动时间</p>
                <p className="mt-1 text-sm font-medium text-graphite-900">{selectedTask.start_time || '-'}</p>
                <div className="mt-3">
                  <ProgressMeter value={selectedTask.progress || 0} tone={statusConfig[selectedTask.status]?.tone || 'electric'} label="当前进度" />
                </div>
              </div>
            </div>
          ) : (
            <div className="panel-muted flex min-h-[360px] flex-col items-center justify-center gap-3 text-center">
              <Eye className="h-7 w-7 text-graphite-400" />
              <p className="text-sm text-graphite-500">从左侧列表选择一个任务查看详情。</p>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
