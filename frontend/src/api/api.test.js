import { beforeEach, describe, expect, it, vi } from 'vitest'

const axiosMock = vi.hoisted(() => {
  const instance = {
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  }
  return {
    create: vi.fn(() => instance),
    instance,
  }
})

vi.mock('axios', () => ({
  default: {
    create: axiosMock.create,
  },
}))

vi.mock('../auth', () => ({
  clearSession: vi.fn(),
  DEMO_MODE_ENABLED: false,
  getAccessToken: vi.fn(() => 'test-token'),
}))

describe('API utilities', () => {
  beforeEach(() => {
    vi.resetModules()
    axiosMock.instance.get.mockReset()
    axiosMock.instance.post.mockReset()
    axiosMock.instance.delete.mockReset()
    axiosMock.create.mockClear()
  })

  it('API_PREFIX is /api/v1', async () => {
    const { API_PREFIX } = await import('./index.js')
    expect(API_PREFIX).toBe('/api/v1')
  })

  it('buildGovernanceReportLink includes tab and highlight', async () => {
    const { buildGovernanceReportLink } = await import('./index.js')
    expect(buildGovernanceReportLink()).toBe('/governance?tab=reports')
    expect(buildGovernanceReportLink(42)).toBe('/governance?tab=reports&highlight=42')
  })

  it('buildApiUrl returns path when no base URL', async () => {
    const { buildApiUrl } = await import('./index.js')
    expect(buildApiUrl('/api/v1/health')).toBe('/api/v1/health')
  })

  it('buildApiUrl prefixes configured API base', async () => {
    vi.stubEnv('VITE_API_URL', 'http://localhost:8000')
    const { buildApiUrl, getApiBaseUrl } = await import('./index.js')
    expect(getApiBaseUrl()).toBe('http://localhost:8000')
    expect(buildApiUrl('/api/v1/health')).toBe('http://localhost:8000/api/v1/health')
    vi.unstubAllEnvs()
  })

  it('attackApi.run posts to /api/v1/attack', async () => {
    axiosMock.instance.post.mockResolvedValue({ data: { ok: true } })
    const { attackApi } = await import('./index.js')
    const payload = { attack_type: 'jailbreak', prompt: 'test' }
    const result = await attackApi.run(payload)
    expect(result).toEqual({ ok: true })
    expect(axiosMock.instance.post).toHaveBeenCalledWith('/api/v1/attack', payload)
  })

  it('tasksApi.list fetches /api/v1/tasks', async () => {
    axiosMock.instance.get.mockResolvedValue({ data: [{ id: 't1' }] })
    const { tasksApi } = await import('./index.js')
    const result = await tasksApi.list()
    expect(result).toEqual([{ id: 't1' }])
    expect(axiosMock.instance.get).toHaveBeenCalledWith('/api/v1/tasks')
  })

  it('auditApi.getLogs passes query params', async () => {
    axiosMock.instance.get.mockResolvedValue({ data: { logs: [] } })
    const { auditApi } = await import('./index.js')
    const result = await auditApi.getLogs({ limit: 10, action: 'GET' })
    expect(result).toEqual({ logs: [] })
    expect(axiosMock.instance.get).toHaveBeenCalledWith('/api/v1/audit/logs', {
      params: { limit: 10, action: 'GET' },
    })
  })

  it('autoRedteamApi.streamUrl builds SSE endpoint', async () => {
    const { autoRedteamApi } = await import('./index.js')
    expect(autoRedteamApi.streamUrl('task-1')).toBe('/api/v1/auto-redteam/task-1/stream')
  })

  it('canvasApi.deploy posts DAG payload', async () => {
    axiosMock.instance.post.mockResolvedValue({ data: { run_id: 'run-1' } })
    const { canvasApi } = await import('./index.js')
    const dag = { nodes: [], edges: [] }
    const result = await canvasApi.deploy(dag)
    expect(result).toEqual({ run_id: 'run-1' })
    expect(axiosMock.instance.post).toHaveBeenCalledWith('/api/v1/canvas/deploy', dag)
  })

  it('getMonitoringVisualization fetches visualization endpoint', async () => {
    axiosMock.instance.get.mockResolvedValue({
      data: { trends: { series: [] }, radar: { items: [] }, topology: { nodes: [], links: [] } },
    })
    const { getMonitoringVisualization } = await import('./index.js')
    const result = await getMonitoringVisualization()
    expect(result.trends).toBeDefined()
    expect(axiosMock.instance.get).toHaveBeenCalledWith('/api/v1/monitoring/visualization')
  })

  it('v2Api.agentAttack posts to /api/v2/attacks/agent', async () => {
    axiosMock.instance.post.mockResolvedValue({ data: { success: true } })
    const { v2Api } = await import('./index.js')
    const payload = { strategy: 'tool_abuse' }
    const result = await v2Api.agentAttack(payload)
    expect(result).toEqual({ success: true })
    expect(axiosMock.instance.post).toHaveBeenCalledWith('/api/v2/attacks/agent', payload)
  })
})