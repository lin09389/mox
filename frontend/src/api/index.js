import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 300000,
})

let apiStatus = 'unknown'

export const getApiStatus = () => apiStatus

api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => {
    apiStatus = 'connected'
    return response
  },
  (error) => {
    if (!error.response) {
      apiStatus = 'disconnected'
    }
    return Promise.reject(error)
  }
)

export const attackApi = {
  run: (data) => api.post('/api/attack', data),
  getHistory: (params) => api.get('/api/attack/history', { params }),
  test: () => api.get('/api/health'),
}

export const defenseApi = {
  scan: (data) => api.post('/api/defense/scan', data),
  sanitize: (data) => api.post('/api/defense/sanitize', data),
  getHistory: (params) => api.get('/api/defense/history', { params }),
}

export const benchmarkApi = {
  run: (data) => api.post('/api/benchmark/run', data),
  getDatasets: () => api.get('/api/benchmark/datasets'),
}

export const statsApi = {
  getOverview: () => api.get('/api/stats/overview'),
}
