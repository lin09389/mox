import axios from 'axios'
import { clearSession, DEMO_MODE_ENABLED, getAccessToken } from '../auth'

const API_BASE = import.meta.env.VITE_API_URL || ''
const API_PREFIX = '/api/v1'

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 300000,
})

let apiStatus = 'unknown'

export const getApiStatus = () => apiStatus
export const isDemoModeEnabled = DEMO_MODE_ENABLED

function unwrap(response) {
  return response.data
}

function handleApiError(error) {
  if (!error.response) {
    apiStatus = 'disconnected'
  } else {
    apiStatus = 'degraded'
  }
  throw error
}

async function withDemoFallback(request, fallbackFactory) {
  try {
    return await request()
  } catch (error) {
    if (!DEMO_MODE_ENABLED) {
      handleApiError(error)
    }
    return fallbackFactory(error)
  }
}

api.interceptors.request.use(
  (config) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => {
    apiStatus = 'connected'
    return response
  },
  (error) => {
    if (error.response?.status === 401 && !String(error.config?.url || '').includes('/auth/login')) {
      clearSession()
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.assign('/login?reason=expired')
      }
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  login: async (credentials) => unwrap(await api.post(`${API_PREFIX}/auth/login`, credentials)),
  me: async () => unwrap(await api.get(`${API_PREFIX}/auth/me`)),
}

export const attackApi = {
  run: async (data) => unwrap(await api.post(`${API_PREFIX}/attack`, data)),
  getHistory: async (params) => unwrap(await api.get(`${API_PREFIX}/attack/history`, { params })),
  test: async () => unwrap(await api.get(`${API_PREFIX}/health`)),
  getRegistry: async () => unwrap(await api.get(`${API_PREFIX}/attacks/registry`)),
}

export const datasetApi = {
  list: async (params) => unwrap(await api.get(`${API_PREFIX}/datasets`, { params })),
  upload: async (formData) => unwrap(await api.post(`${API_PREFIX}/datasets/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })),
  delete: async (id) => unwrap(await api.delete(`${API_PREFIX}/datasets/${id}`)),
}

export const defenseApi = {
  scan: async (data) => unwrap(await api.post(`${API_PREFIX}/defense/scan`, data)),
  sanitize: async (data) => unwrap(await api.post(`${API_PREFIX}/defense/sanitize`, data)),
  getHistory: async (params) => unwrap(await api.get(`${API_PREFIX}/defense/history`, { params })),
}

export const benchmarkApi = {
  run: async (data) => unwrap(await api.post(`${API_PREFIX}/benchmark/run`, data)),
  getDatasets: async () => unwrap(await api.get(`${API_PREFIX}/benchmark/datasets`)),
}

export const statsApi = {
  getOverview: async () => unwrap(await api.get(`${API_PREFIX}/stats/overview`)),
}

export async function getStats() {
  return withDemoFallback(
    async () => unwrap(await api.get(`${API_PREFIX}/monitoring/stats`)),
    () => ({
      totalRequests: 1247,
      blockedRequests: 89,
      attackSuccessRate: 0.12,
      defenseSuccessRate: 0.94,
      _demo_mode: true,
    })
  )
}

export async function getRecentAttacks() {
  return withDemoFallback(
    async () => unwrap(await api.get(`${API_PREFIX}/monitoring/attacks/recent`)),
    () => []
  )
}

export async function getDefenseLogs() {
  return withDemoFallback(
    async () => unwrap(await api.get(`${API_PREFIX}/defense/logs`)),
    () => []
  )
}

export async function runOWASPTests(model) {
  const data = await withDemoFallback(
    async () => unwrap(await api.post(`${API_PREFIX}/owasp/run`, { model })),
    () => ({ results: generateMockOWASPResults() })
  )

  if (Array.isArray(data?.results)) {
    return data.results
  }
  if (Array.isArray(data?.report?.results)) {
    return data.report.results
  }
  if (Array.isArray(data)) {
    return data
  }
  return []
}

export async function runRedTeam(targetModel, techniques) {
  const data = await withDemoFallback(
    async () => unwrap(await api.post(`${API_PREFIX}/redteam/run`, { model: targetModel, techniques })),
    () => ({ results: generateMockRedTeamResults() })
  )

  if (Array.isArray(data?.report?.results)) {
    return data.report.results
  }
  if (Array.isArray(data?.results)) {
    return data.results
  }
  if (Array.isArray(data)) {
    return data
  }
  return []
}

export async function testGateway(input) {
  return withDemoFallback(
    async () => unwrap(await api.post(`${API_PREFIX}/gateway/validate`, { input })),
    () => ({ decision: 'allow', confidence: 0, reason: 'demo mode' })
  )
}

export async function testInjectionDetector(input) {
  return withDemoFallback(
    async () => unwrap(await api.post(`${API_PREFIX}/defense/injection/detect`, { text: input, scan_type: 'input' })),
    () => ({ is_malicious: false, confidence: 0 })
  )
}

export async function getMonitoringData() {
  return withDemoFallback(
    async () => unwrap(await api.get(`${API_PREFIX}/monitoring/dashboard`)),
    () => ({})
  )
}

export async function getAnomalies() {
  return withDemoFallback(
    async () => unwrap(await api.get(`${API_PREFIX}/monitoring/anomalies`)),
    () => []
  )
}

export async function getModels() {
  const data = await withDemoFallback(
    async () => unwrap(await api.get(`${API_PREFIX}/models`)),
    () => ({ models: [] })
  )
  return data?.models || []
}

export async function getAttackTemplates() {
  return unwrap(await api.get(`${API_PREFIX}/templates`))
}

function generateMockOWASPResults() {
  const categories = ['LLM01', 'LLM02', 'LLM03', 'LLM04', 'LLM05', 'LLM06', 'LLM07', 'LLM08', 'LLM09', 'LLM10']
  const names = [
    'Prompt Injection',
    'Sensitive Information Disclosure',
    'Supply Chain',
    'Data Poisoning',
    'Improper Output Handling',
    'Prompt Leakage',
    'Insecure Plugins',
    'Excessive Agency',
    'Overreliance',
    'Vector Weakness',
  ]
  return categories.map((category, index) => ({
    category,
    passed: Math.random() > 0.3,
    test: `${names[index]} Test`,
    _demo_mode: true,
  }))
}

function generateMockRedTeamResults() {
  const techniques = ['prompt_injection', 'jailbreak', 'role_play', 'encoding']
  const scenarios = ['Direct injection', 'DAN mode', 'Role-play drift', 'Base64 bypass']
  return techniques.map((technique, index) => ({
    scenario: scenarios[index],
    technique,
    success: Math.random() > 0.5,
    attempts: Math.floor(Math.random() * 3) + 1,
    _demo_mode: true,
  }))
}

export default api
