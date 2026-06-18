import { create } from 'zustand'
import api from '../api'

const fallbackTasks = [
  { id: 'task-001', name: 'GPT-4 批量盲测任务', status: 'running', progress: 65 },
  { id: 'task-002', name: '全矩阵渗透模拟', status: 'running', progress: 35 },
]

export const useTaskStore = create((set) => ({
  tasks: [],
  minimized: false,
  closed: false,
  setMinimized: (val) => set({ minimized: val }),
  setClosed: (val) => set({ closed: val }),
  fetchTasks: async () => {
    try {
      const response = await api.get('/api/tasks')
      const runningTasks = (response.data || []).filter(t => t.status === 'running')
      set({ tasks: runningTasks })
    } catch {
      set({ tasks: fallbackTasks.filter(t => t.status === 'running') })
    }
  }
}))
