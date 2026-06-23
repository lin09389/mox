import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  getStats, 
  getRecentAttacks, 
  getDefenseLogs, 
  attackApi, 
  defenseApi,
  getModels, 
  authApi, 
  getAttackTemplates,
  getMonitoringVisualization,
  auditApi,
} from '../api'

// Query Keys Centralization
export const queryKeys = {
  stats: ['stats'],
  recentAttacks: ['recentAttacks'],
  defenseLogs: ['defenseLogs'],
  models: ['models'],
  templates: ['templates'],
  monitoring: {
    visualization: ['monitoring', 'visualization'],
  },
  auth: {
    me: ['auth', 'me'],
  },
  attack: {
    history: (params) => ['attack', 'history', params],
  },
  defense: {
    history: (params) => ['defense', 'history', params],
  }
}

// Global Dashboard Hooks
export function useDashboardStats() {
  return useQuery({
    queryKey: queryKeys.stats,
    queryFn: getStats,
    refetchInterval: 30000, // Replace useAutoRefresh
  })
}

export function useRecentAttacks() {
  return useQuery({
    queryKey: queryKeys.recentAttacks,
    queryFn: getRecentAttacks,
    refetchInterval: 30000,
  })
}

export function useDefenseLogs() {
  return useQuery({
    queryKey: queryKeys.defenseLogs,
    queryFn: getDefenseLogs,
    refetchInterval: 30000,
  })
}

export function useMonitoringVisualization() {
  return useQuery({
    queryKey: queryKeys.monitoring.visualization,
    queryFn: getMonitoringVisualization,
    refetchInterval: 30000,
  })
}

// History Hooks
export function useAttackHistory(params) {
  return useQuery({
    queryKey: queryKeys.attack.history(params),
    queryFn: () => attackApi.getHistory(params),
  })
}

export function useDefenseHistory(params) {
  return useQuery({
    queryKey: queryKeys.defense.history(params),
    queryFn: () => defenseApi.getHistory(params),
  })
}

// Audit Hooks
export function useAuditLogs(params = {}) {
  const queryParams = params.action && params.action !== 'all' ? { action: params.action } : {}
  return useQuery({
    queryKey: ['audit', 'logs', queryParams],
    queryFn: async () => {
      const data = await auditApi.getLogs(queryParams)
      return data?.logs || data || []
    },
  })
}

// Attack / Model related Hooks
export function useModels() {
  return useQuery({
    queryKey: queryKeys.models,
    queryFn: getModels,
    staleTime: 60 * 60 * 1000, // 1 hour
  })
}

export function useAttackTemplatesQuery() {
  return useQuery({
    queryKey: queryKeys.templates,
    queryFn: getAttackTemplates,
    staleTime: 60 * 60 * 1000,
  })
}

// Auth Hooks
export function useLogin() {
  return useMutation({
    mutationFn: (credentials) => authApi.login(credentials),
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: (data) => authApi.register(data),
  })
}

export function useRunAttack() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data) => attackApi.run(data),
    onSuccess: () => {
      // Invalidate recent attacks and stats when a new attack is run
      queryClient.invalidateQueries({ queryKey: queryKeys.recentAttacks })
      queryClient.invalidateQueries({ queryKey: queryKeys.stats })
      queryClient.invalidateQueries({ queryKey: queryKeys.monitoring.visualization })
      queryClient.invalidateQueries({ queryKey: queryKeys.attack.history() })
    },
  })
}

// Auth Hooks
export function useLoginMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (credentials) => authApi.login(credentials),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.auth.me })
    },
  })
}

export function useUser() {
  return useQuery({
    queryKey: queryKeys.auth.me,
    queryFn: authApi.me,
    staleTime: 10 * 60 * 1000,
  })
}
