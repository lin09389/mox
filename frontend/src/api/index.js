import axios from 'axios'
import { clearSession, DEMO_MODE_ENABLED, getAccessToken } from '../auth'

export { getAccessToken }

const API_BASE = import.meta.env.VITE_API_URL || ''
export const API_PREFIX = '/api/v1'

/** 获取 API 根地址（用于 SSE / fetch 等不走 axios baseURL 的场景） */
export function getApiBaseUrl() {
  if (API_BASE) return API_BASE.replace(/\/$/, '')
  if (typeof window !== 'undefined') return window.location.origin
  return ''
}

/** 构建完整 API URL */
export function buildGovernanceReportLink(reportId) {
  const params = new URLSearchParams({ tab: 'reports' })
  if (reportId != null && reportId !== '') {
    params.set('highlight', String(reportId))
  }
  return `/governance?${params.toString()}`
}

export function buildApiUrl(path) {
  const normalized = path.startsWith('/') ? path : `/${path}`
  const base = getApiBaseUrl()
  return base ? `${base}${normalized}` : normalized
}

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
  register: async (data) => unwrap(await api.post(`${API_PREFIX}/auth/register`, data)),
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

export const templateApi = {
  list: async (params) => unwrap(await api.get(`${API_PREFIX}/user-templates`, { params })),
  create: async (data) => unwrap(await api.post(`${API_PREFIX}/user-templates`, data)),
  update: async (id, data) => unwrap(await api.put(`${API_PREFIX}/user-templates/${id}`, data)),
  delete: async (id) => unwrap(await api.delete(`${API_PREFIX}/user-templates/${id}`)),
  toggleFavorite: async (id) => unwrap(await api.post(`${API_PREFIX}/user-templates/${id}/favorite`)),
}

export const reportApi = {
  list: async (params) => unwrap(await api.get(`${API_PREFIX}/reports`, { params })),
  get: async (id) => unwrap(await api.get(`${API_PREFIX}/reports/${id}`)),
  delete: async (id) => unwrap(await api.delete(`${API_PREFIX}/reports/${id}`)),
  downloadUrl: (id) => buildApiUrl(`${API_PREFIX}/reports/${id}/download`),
  download: async (id, filename = 'report') => {
    const token = getAccessToken()
    const url = buildApiUrl(`${API_PREFIX}/reports/${id}/download`)
    const response = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!response.ok) {
      const error = new Error('Report download failed')
      error.response = { status: response.status }
      throw error
    }
    const blob = await response.blob()
    const objectUrl = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = objectUrl
    anchor.download = filename
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    URL.revokeObjectURL(objectUrl)
  },
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

function extractResultList(data) {
  if (Array.isArray(data?.results)) return data.results
  if (Array.isArray(data?.report?.results)) return data.report.results
  if (Array.isArray(data)) return data
  return []
}

export async function runOWASPTests(model) {
  const data = await withDemoFallback(
    async () => unwrap(await api.post(`${API_PREFIX}/owasp/run`, { model })),
    () => ({ results: generateMockOWASPResults() })
  )

  return {
    results: extractResultList(data),
    reportId: data?.report_id ?? null,
  }
}

export async function runRedTeam(targetModel, techniques) {
  const data = await withDemoFallback(
    async () => unwrap(await api.post(`${API_PREFIX}/redteam/run`, { model: targetModel, techniques })),
    () => ({ results: generateMockRedTeamResults() })
  )

  return {
    results: extractResultList(data),
    reportId: data?.report_id ?? null,
    summary: data?.summary ?? null,
  }
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

export async function getMonitoringVisualization() {
  return withDemoFallback(
    async () => unwrap(await api.get(`${API_PREFIX}/monitoring/visualization`)),
    () => ({
      stats: {
        totalRequests: 0,
        blockedRequests: 0,
        attackSuccessRate: 0,
        defenseSuccessRate: 0,
      },
      trends: { series: [] },
      radar: { items: [] },
      topology: { nodes: [], links: [] },
      _demo_mode: true,
    })
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

export const autoRedteamApi = {
  start: async (data) => unwrap(await api.post(`${API_PREFIX}/auto-redteam/start`, data)),
  stop: async (taskId) => unwrap(await api.delete(`${API_PREFIX}/auto-redteam/${taskId}`)),
  getStatus: async (taskId) => unwrap(await api.get(`${API_PREFIX}/auto-redteam/${taskId}`)),
  streamUrl: (taskId) => buildApiUrl(`${API_PREFIX}/auto-redteam/${taskId}/stream`),
}

export const canvasApi = {
  deploy: async (dag) => unwrap(await api.post(`${API_PREFIX}/canvas/deploy`, dag)),
  getRun: async (runId) => unwrap(await api.get(`${API_PREFIX}/canvas/runs/${runId}`)),
  listRuns: async (limit = 20) => unwrap(await api.get(`${API_PREFIX}/canvas/runs`, { params: { limit } })),
}

export const tasksApi = {
  list: async () => unwrap(await api.get(`${API_PREFIX}/tasks`)),
}

export const auditApi = {
  getLogs: async (params) => unwrap(await api.get(`${API_PREFIX}/audit/logs`, { params })),
}

const API_V2_PREFIX = '/api/v2'

export const v2Api = {
  agentAttack: async (payload) => unwrap(await api.post(`${API_V2_PREFIX}/attacks/agent`, payload)),
  multimodalAttack: async (payload) => unwrap(await api.post(`${API_V2_PREFIX}/attacks/multimodal`, payload)),
  safetyCardsRecent: async () => unwrap(await api.get(`${API_V2_PREFIX}/safety-cards/recent`)),
  safetyCardsGenerate: async (data) => unwrap(await api.post(`${API_V2_PREFIX}/safety-cards/generate`, data)),
}

export const evaluationApi = {
  biasDetect: async (data) => unwrap(await api.post(`${API_PREFIX}/bias/detect`, data)),
  codeSecurity: async (data) => unwrap(await api.post(`${API_PREFIX}/code/security`, data)),
}

export const attackLoopApi = {
  start: async (config) => unwrap(await api.post(`${API_PREFIX}/attack-loop/start`, config)),
  getProgress: async (taskId) => unwrap(await api.get(`${API_PREFIX}/attack-loop/progress/${taskId}`)),
  pause: async (taskId) => unwrap(await api.post(`${API_PREFIX}/attack-loop/pause/${taskId}`)),
  resume: async (taskId) => unwrap(await api.post(`${API_PREFIX}/attack-loop/resume/${taskId}`)),
  stop: async (taskId) => unwrap(await api.post(`${API_PREFIX}/attack-loop/stop/${taskId}`)),
  download: async (taskId, format) => unwrap(await api.get(`${API_PREFIX}/attack-loop/download/${taskId}?format=${format}`, { responseType: 'blob' })),
  getHistory: async (params) => unwrap(await api.get(`${API_PREFIX}/attack-loop/history`, { params })),
  getTypes: async () => withDemoFallback(
    async () => unwrap(await api.get(`${API_PREFIX}/attack-loop/types`)),
    () => null
  ),
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
