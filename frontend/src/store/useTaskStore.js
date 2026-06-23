import { create } from 'zustand'
import { tasksApi } from '../api'
import { isDemoModeEnabled } from '../api'
import { getTaskHref, isActiveTask, normalizeRemoteTask } from '../utils/taskTrayHelpers'

const fallbackTasks = [
  { id: 'task-001', name: 'GPT-4 批量盲测任务', status: 'running', progress: 65, source: 'queue' },
  { id: 'task-002', name: '全矩阵渗透模拟', status: 'running', progress: 35, source: 'attack_loop', href: '/testing?tab=loop' },
]

function mergeTasks(remoteTasks, localTasks) {
  const byId = new Map()
  for (const task of remoteTasks) {
    if (isActiveTask(task)) byId.set(task.id, task)
  }
  for (const task of Object.values(localTasks)) {
    if (isActiveTask(task)) {
      byId.set(task.id, { ...byId.get(task.id), ...task })
    }
  }
  return Array.from(byId.values())
}

export const useTaskStore = create((set, get) => ({
  tasks: [],
  localTasks: {},
  minimized: false,
  closed: false,
  setMinimized: (val) => set({ minimized: val }),
  setClosed: (val) => set({ closed: val }),
  registerLocalTask: (task) => {
    const entry = {
      status: 'running',
      progress: 0,
      href: getTaskHref(task),
      ...task,
    }
    set((state) => ({
      localTasks: { ...state.localTasks, [entry.id]: entry },
      closed: false,
      tasks: mergeTasks(state.tasks, { ...state.localTasks, [entry.id]: entry }),
    }))
  },
  updateLocalTask: (id, patch) => {
    set((state) => {
      const current = state.localTasks[id]
      if (!current) return state
      const next = { ...current, ...patch, href: patch.href || current.href || getTaskHref({ ...current, ...patch }) }
      const localTasks = { ...state.localTasks, [id]: next }
      return {
        localTasks,
        tasks: mergeTasks(state.tasks, localTasks),
      }
    })
  },
  finishLocalTask: (id, patch = {}) => {
    get().updateLocalTask(id, { status: 'completed', progress: 100, ...patch })
    window.setTimeout(() => {
      set((state) => {
        const { [id]: _removed, ...rest } = state.localTasks
        return {
          localTasks: rest,
          tasks: mergeTasks(state.tasks.filter((t) => t.id !== id), rest),
        }
      })
    }, 4000)
  },
  removeLocalTask: (id) => {
    set((state) => {
      const { [id]: _removed, ...rest } = state.localTasks
      return {
        localTasks: rest,
        tasks: mergeTasks(state.tasks.filter((t) => t.id !== id), rest),
      }
    })
  },
  fetchTasks: async () => {
    const { localTasks } = get()
    let remote = []
    try {
      const data = await tasksApi.list()
      remote = (data || []).map(normalizeRemoteTask)
    } catch {
      if (isDemoModeEnabled) {
        remote = fallbackTasks.map(normalizeRemoteTask)
      }
    }
    set({ tasks: mergeTasks(remote, localTasks) })
  },
}))