import { useCallback, useState } from 'react'
import { getApiStatus } from '../api'
import { useAutoRefresh } from './useAutoRefresh'

export function useApiStatus(pollIntervalMs = 30000, enabled = true) {
  const [status, setStatus] = useState(() => getApiStatus())

  const sync = useCallback(() => {
    setStatus(getApiStatus())
  }, [])

  useAutoRefresh(sync, pollIntervalMs, enabled)

  return {
    status,
    isConnected: status === 'connected',
    isDegraded: status === 'degraded',
    isDisconnected: status === 'disconnected',
    sync,
  }
}