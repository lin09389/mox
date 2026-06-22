import { useCallback, useEffect, useState } from 'react'
import { getApiStatus } from '../api'
import { useAutoRefresh } from './useAutoRefresh'

export function useApiStatus(pollIntervalMs = 30000, enabled = true) {
  const [status, setStatus] = useState(() => getApiStatus())

  const sync = useCallback(() => {
    setStatus(getApiStatus())
  }, [])

  useEffect(() => {
    sync()
  }, [sync])

  useAutoRefresh(sync, pollIntervalMs, enabled)

  return {
    status,
    isConnected: status === 'connected',
    isDegraded: status === 'degraded',
    isDisconnected: status === 'disconnected',
    sync,
  }
}