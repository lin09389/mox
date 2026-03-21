import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, CheckCircle, XCircle, Clock, Loader, ListTodo, Eye } from 'lucide-react'
import { api } from '../api'

const statusConfig = {
  running: { icon: Loader, color: 'text-electric-600', bgColor: 'bg-electric-100', borderColor: 'border-electric-200/70', label: '运行中' },
  completed: { icon: CheckCircle, color: 'text-neon-600', bgColor: 'bg-neon-100', borderColor: 'border-neon-200/70', label: '已完成' },
  failed: { icon: XCircle, color: 'text-lava-600', bgColor: 'bg-lava-100', borderColor: 'border-lava-200/70', label: '失败' },
  pending: { icon: Clock, color: 'text-amber-600', bgColor: 'bg-amber-100', borderColor: 'border-amber-200/70', label: '等待中' },
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
}

const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } },
}

export default function TaskProgressPage() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedTask, setSelectedTask] = useState(null)

  useEffect(() => {
    fetchTasks()
    const interval = setInterval(fetchTasks, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchTasks = async () => {
    setLoading(true)
    try {
      const res = await api.get('/api/tasks')
      setTasks(res.data)
    } catch (error) {
      setTasks(getDefaultTasks())
    } finally {
      setLoading(false)
    }
  }

  const getDefaultTasks = () => [
    { id: 'task_001', name: 'GPT-4批量攻击测试', type: 'attack', status: 'running', progress: 65, total: 100, completed: 65, failed: 3, start_time: '2024-03-01 10:00:00' },
    { id: 'task_002', name: 'Claude防御评估', type: 'defense', status: 'running', progress: 30, total: 50, completed: 15, failed: 1, start_time: '2024-03-01 10:15:00' },
    { id: 'task_003', name: 'AdvBench基准测试', type: 'benchmark', status: 'pending', progress: 0, total: 200, completed: 0, failed: 0, start_time: '-' },
    { id: 'task_004', name: '模型安全扫描', type: 'scan', status: 'completed', progress: 100, total: 100, completed: 100, failed: 5, start_time: '2024-02-28 14:00:00' },
    { id: 'task_005', name: '定时安全巡检', type: 'scheduled', status: 'failed', progress: 45, total: 100, completed: 45, failed: 12, start_time: '2024-02-28 09:00:00' },
  ]

  const viewTaskDetail = (task) => {
    setSelectedTask(task)
  }

  const runningTasks = tasks.filter((t) => t.status === 'running')
  const stats = {
    running: tasks.filter((t) => t.status === 'running').length,
    pending: tasks.filter((t) => t.status === 'pending').length,
    completed: tasks.filter((t) => t.status === 'completed').length,
    failed: tasks.filter((t) => t.status === 'failed').length,
  }

  const getStatusIcon = (status) => {
    const config = statusConfig[status] || statusConfig.pending
    const Icon = config.icon
    return <Icon className={`w-4 h-4 ${config.color} ${status === 'running' ? 'animate-spin' : ''}`} />
  }

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      {/* 页面标题 */}
      <motion.div variants={item} className="flex items-center gap-3">
        <div className="w-11 h-11 bg-electric-100 rounded-lg flex items-center justify-center border border-electric-200/70">
          <ListTodo className="w-5.5 h-5.5 text-electric-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold font-display text-graphite-900 tracking-tight">
            任务中心
          </h1>
          <p className="text-sm text-graphite-500">管理和监控所有安全测试任务</p>
        </div>
      </motion.div>

      {/* 统计卡片 */}
      <motion.div variants={item} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Object.entries(stats).map(([key, value]) => {
          const config = statusConfig[key] || statusConfig.pending
          const Icon = config.icon
          return (
            <motion.div key={key} variants={item} className="card flex items-center gap-3">
              <div className={`w-10 h-10 ${config.bgColor} rounded-lg flex items-center justify-center border ${config.borderColor}`}>
                <Icon className={`w-5 h-5 ${config.color} ${key === 'running' ? 'animate-spin' : ''}`} />
              </div>
              <div>
                <p className="text-xs text-graphite-500">{config.label}</p>
                <p className="text-2xl font-bold font-display text-graphite-900">{value}</p>
              </div>
            </motion.div>
          )
        })}
      </motion.div>

      {/* 正在执行的任务 */}
      {runningTasks.length > 0 && (
        <motion.div variants={item} className="card">
          <h3 className="text-sm font-semibold text-graphite-900 mb-4 flex items-center gap-2">
            <Play className="w-4 h-4 text-electric-500" />
            正在执行
          </h3>
          <div className="space-y-3">
            {runningTasks.map((task) => (
              <div
                key={task.id}
                className="flex items-center gap-4 p-3 bg-graphite-50/50 rounded-lg border border-graphite-200/60"
              >
                <Loader className="w-5 h-5 text-electric-500 animate-spin" />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-medium text-sm text-graphite-900">{task.name}</span>
                    <span className="text-xs text-graphite-500">
                      {task.completed}/{task.total}
                    </span>
                  </div>
                  <div className="h-2 bg-graphite-200 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-electric-500 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${task.progress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* 任务列表 */}
      <motion.div variants={item} className="card p-0 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-graphite-500">
            <div className="spinner mx-auto mb-2" />
            加载中...
          </div>
        ) : tasks.length === 0 ? (
          <div className="p-8 text-center text-graphite-500">暂无任务</div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>任务ID</th>
                  <th>任务名称</th>
                  <th>类型</th>
                  <th>状态</th>
                  <th>进度</th>
                  <th>完成/总计</th>
                  <th>失败</th>
                  <th>开始时间</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => {
                  const status = statusConfig[task.status] || statusConfig.pending
                  return (
                    <tr
                      key={task.id}
                      className="cursor-pointer group"
                      onClick={() => viewTaskDetail(task)}
                    >
                      <td className="font-mono text-xs text-graphite-600">{task.id}</td>
                      <td className="font-medium text-graphite-900 text-sm">{task.name}</td>
                      <td>
                        <span className="badge bg-graphite-100 text-graphite-700 border border-graphite-200/60">
                          {task.type}
                        </span>
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(task.status)}
                          <span className={`text-xs font-medium ${status.color}`}>
                            {status.label}
                          </span>
                        </div>
                      </td>
                      <td className="w-32">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-1.5 bg-graphite-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                task.status === 'failed'
                                  ? 'bg-lava-500'
                                  : task.status === 'completed'
                                  ? 'bg-neon-500'
                                  : 'bg-electric-500'
                              }`}
                              style={{ width: `${task.progress}%` }}
                            />
                          </div>
                          <span className="text-xs text-graphite-500">{task.progress}%</span>
                        </div>
                      </td>
                      <td className="text-graphite-600 text-sm">
                        {task.completed}/{task.total}
                      </td>
                      <td>
                        <span className={task.failed > 0 ? 'text-lava-600 font-medium' : 'text-neon-600'}>
                          {task.failed}
                        </span>
                      </td>
                      <td className="text-graphite-500 text-xs">{task.start_time}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      {/* 任务详情模态框 */}
      <AnimatePresence>
        {selectedTask && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-graphite-900/30 backdrop-blur-sm flex items-center justify-center z-50"
            onClick={() => setSelectedTask(null)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="bg-white rounded-lg p-6 w-full max-w-md shadow-modal"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-lg font-semibold text-graphite-900 mb-4 flex items-center gap-2">
                <Eye className="w-5 h-5 text-electric-500" />
                任务详情
              </h2>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-graphite-500">任务ID:</span>
                  <span className="font-mono text-sm">{selectedTask.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-graphite-500">任务名称:</span>
                  <span className="font-medium">{selectedTask.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-graphite-500">类型:</span>
                  <span className="badge badge-info">{selectedTask.type}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-graphite-500">状态:</span>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(selectedTask.status)}
                    <span className={`font-medium ${statusConfig[selectedTask.status]?.color}`}>
                      {statusConfig[selectedTask.status]?.label}
                    </span>
                  </div>
                </div>
                <div className="mt-4">
                  <div className="flex justify-between text-sm mb-1.5">
                    <span className="text-graphite-500">进度:</span>
                    <span className="font-medium">{selectedTask.progress}%</span>
                  </div>
                  <div className="w-full h-3 bg-graphite-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        selectedTask.status === 'failed'
                          ? 'bg-lava-500'
                          : selectedTask.status === 'completed'
                          ? 'bg-neon-500'
                          : 'bg-electric-500'
                      }`}
                      style={{ width: `${selectedTask.progress}%` }}
                    />
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="text-graphite-500">完成:</span>
                  <span>
                    {selectedTask.completed} / {selectedTask.total}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-graphite-500">失败:</span>
                  <span className={selectedTask.failed > 0 ? 'text-lava-600' : 'text-neon-600'}>
                    {selectedTask.failed}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-graphite-500">开始时间:</span>
                  <span className="text-sm">{selectedTask.start_time}</span>
                </div>
              </div>
              <button
                onClick={() => setSelectedTask(null)}
                className="btn-secondary w-full mt-5"
              >
                关闭
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
