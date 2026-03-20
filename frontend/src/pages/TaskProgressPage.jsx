import { useState, useEffect } from 'react'
import { Play, Pause, RotateCcw, CheckCircle, XCircle, Clock, Loader } from 'lucide-react'
import { api } from '../api'

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

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running': return <Loader className="animate-spin text-blue-500" size={18} />
      case 'completed': return <CheckCircle className="text-green-500" size={18} />
      case 'failed': return <XCircle className="text-red-500" size={18} />
      case 'pending': return <Clock className="text-yellow-500" size={18} />
      default: return <Clock className="text-gray-500" size={18} />
    }
  }

  const getStatusText = (status) => {
    const config = { running: '运行中', completed: '已完成', failed: '失败', pending: '等待中' }
    return config[status] || status
  }

  const getStatusColor = (status) => {
    const config = { running: 'bg-blue-100 text-blue-800', completed: 'bg-green-100 text-green-800', failed: 'bg-red-100 text-red-800', pending: 'bg-yellow-100 text-yellow-800' }
    return config[status] || 'bg-gray-100'
  }

  const runningTasks = tasks.filter(t => t.status === 'running')
  const stats = {
    running: tasks.filter(t => t.status === 'running').length,
    pending: tasks.filter(t => t.status === 'pending').length,
    completed: tasks.filter(t => t.status === 'completed').length,
    failed: tasks.filter(t => t.status === 'failed').length,
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">任务中心</h1>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <div className="flex items-center gap-2">
            <Loader className="animate-spin text-blue-500" size={20} />
            <div>
              <div className="text-sm text-gray-500">运行中</div>
              <div className="text-2xl font-bold">{stats.running}</div>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <div className="flex items-center gap-2">
            <Clock className="text-yellow-500" size={20} />
            <div>
              <div className="text-sm text-gray-500">等待中</div>
              <div className="text-2xl font-bold">{stats.pending}</div>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <div className="flex items-center gap-2">
            <CheckCircle className="text-green-500" size={20} />
            <div>
              <div className="text-sm text-gray-500">已完成</div>
              <div className="text-2xl font-bold">{stats.completed}</div>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <div className="flex items-center gap-2">
            <XCircle className="text-red-500" size={20} />
            <div>
              <div className="text-sm text-gray-500">失败</div>
              <div className="text-2xl font-bold">{stats.failed}</div>
            </div>
          </div>
        </div>
      </div>

      {runningTasks.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
          <h2 className="font-semibold mb-4">正在执行</h2>
          <div className="space-y-3">
            {runningTasks.map(task => (
              <div key={task.id} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                <Loader className="animate-spin text-blue-500" size={20} />
                <div className="flex-1">
                  <div className="font-medium">{task.name}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div className="bg-blue-500 h-2 rounded-full transition-all" style={{ width: `${task.progress}%` }} />
                    </div>
                    <span className="text-sm text-gray-600">{task.completed}/{task.total}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        {loading ? (
          <div className="p-8 text-center text-gray-500">加载中...</div>
        ) : tasks.length === 0 ? (
          <div className="p-8 text-center text-gray-500">暂无任务</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">任务ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">任务名称</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">类型</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">进度</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">完成/总计</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">失败</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">开始时间</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {tasks.map(task => (
                  <tr key={task.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => viewTaskDetail(task)}>
                    <td className="px-6 py-4 text-gray-600 font-mono text-sm">{task.id}</td>
                    <td className="px-6 py-4 font-medium text-gray-900">{task.name}</td>
                    <td className="px-6 py-4"><span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">{task.type}</span></td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(task.status)}
                        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(task.status)}`}>{getStatusText(task.status)}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 w-40">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-2">
                          <div className={`h-2 rounded-full ${task.status === 'failed' ? 'bg-red-500' : task.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'}`} style={{ width: `${task.progress}%` }} />
                        </div>
                        <span className="text-sm">{task.progress}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-600">{task.completed}/{task.total}</td>
                    <td className="px-6 py-4"><span className={task.failed > 0 ? 'text-red-600 font-medium' : 'text-green-600'}>{task.failed}</span></td>
                    <td className="px-6 py-4 text-gray-600 text-sm">{task.start_time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedTask && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedTask(null)}>
          <div className="bg-white rounded-xl p-6 w-full max-w-lg" onClick={e => e.stopPropagation()}>
            <h2 className="text-xl font-bold mb-4">任务详情</h2>
            <div className="space-y-3">
              <div className="flex justify-between"><span className="text-gray-500">任务ID:</span><span className="font-mono">{selectedTask.id}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">任务名称:</span><span>{selectedTask.name}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">类型:</span><span>{selectedTask.type}</span></div>
              <div className="flex justify-between items-center"><span className="text-gray-500">状态:</span>{getStatusIcon(selectedTask.status)} <span>{getStatusText(selectedTask.status)}</span></div>
              <div className="mt-4">
                <div className="text-sm text-gray-500 mb-1">进度: {selectedTask.progress}%</div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div className={`h-3 rounded-full ${selectedTask.status === 'failed' ? 'bg-red-500' : 'bg-blue-500'}`} style={{ width: `${selectedTask.progress}%` }} />
                </div>
              </div>
              <div className="flex justify-between mt-4"><span className="text-gray-500">完成:</span><span>{selectedTask.completed} / {selectedTask.total}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">失败:</span><span className={selectedTask.failed > 0 ? 'text-red-600' : 'text-green-600'}>{selectedTask.failed}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">开始时间:</span><span>{selectedTask.start_time}</span></div>
            </div>
            <button onClick={() => setSelectedTask(null)} className="mt-4 w-full px-4 py-2 border rounded-lg">关闭</button>
          </div>
        </div>
      )}
    </div>
  )
}
