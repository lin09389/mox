/**
 * useAttackLoopStream - WebSocket-based real-time progress hook for attack loop tasks.
 *
 * Connects to the backend `/ws/attack/{taskId}` endpoint and listens for
 * `task_update` messages.  Falls back to HTTP polling (2 s interval) when
 * the WebSocket connection fails or is unavailable.
 *
 * @param {string|null} taskId  - current running task id
 * @param {object}      opts
 * @param {boolean}     opts.enabled       - whether streaming should be active
 * @param {function}    opts.onProgress    - called with progress data on every update
 * @param {function}    opts.onCompleted   - called with final results when task completes
 * @param {function}    opts.onFailed      - called with error string on task failure
 */
import { useEffect, useRef, useCallback, useState } from 'react'
import { attackLoopApi } from '../api'

const WS_RECONNECT_DELAY = 3000
const POLL_INTERVAL = 2000

/**
 * Build the WebSocket URL for an attack task, deriving the host from the
 * current page location and the optional VITE_API_URL env variable.
 */
function buildWsUrl(taskId) {
  const apiBase = import.meta.env.VITE_API_URL || ''
  if (apiBase) {
    // VITE_API_URL might be "http://localhost:8000" – convert to ws(s)
    const url = new URL(apiBase)
    const proto = url.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${url.host}/ws/attack/${taskId}`
  }
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws/attack/${taskId}`
}

export function useAttackLoopStream(taskId, { enabled = false, onProgress, onCompleted, onFailed } = {}) {
  const wsRef = useRef(null)
  const pollRef = useRef(null)
  const reconnectRef = useRef(null)
  const [connectionMode, setConnectionMode] = useState('idle') // 'ws' | 'polling' | 'idle'

  // Keep callback refs fresh without re-triggering effects
  const cbRef = useRef({ onProgress, onCompleted, onFailed })
  useEffect(() => {
    cbRef.current = { onProgress, onCompleted, onFailed }
  })

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  /** Poll progress via HTTP as fallback */
  const startPolling = useCallback(() => {
    if (pollRef.current) return // already polling
    setConnectionMode('polling')
    pollRef.current = setInterval(async () => {
      if (!taskId) return
      try {
        const data = await attackLoopApi.getProgress(taskId)
        cbRef.current.onProgress?.(data)
        if (data.status === 'completed') {
          cbRef.current.onCompleted?.(data)
          stopPolling()
        } else if (data.status === 'failed') {
          cbRef.current.onFailed?.(data.error)
          stopPolling()
        }
      } catch {
        // silently retry next interval
      }
    }, POLL_INTERVAL)
  }, [taskId, stopPolling])

  /** Close WebSocket and stop polling */
  const cleanup = useCallback(() => {
    if (reconnectRef.current) {
      clearTimeout(reconnectRef.current)
      reconnectRef.current = null
    }
    stopPolling()
    if (wsRef.current) {
      wsRef.current.onclose = null // prevent reconnect on intentional close
      wsRef.current.close()
      wsRef.current = null
    }
    setTimeout(() => setConnectionMode('idle'), 0)
  }, [stopPolling])

  useEffect(() => {
    if (!enabled || !taskId) {
      setTimeout(() => cleanup(), 0)
      return
    }

    let cancelled = false

    function connectWs() {
      if (cancelled) return
      try {
        const url = buildWsUrl(taskId)
        const ws = new WebSocket(url)
        wsRef.current = ws

        ws.onopen = () => {
          if (cancelled) { ws.close(); return }
          setConnectionMode('ws')
          // Keep HTTP polling as a fallback in case WS misses updates
          startPolling()
        }

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data)
            if (msg.type === 'task_update' || msg.type === 'progress') {
              cbRef.current.onProgress?.(msg)
              if (msg.status === 'completed') {
                cbRef.current.onCompleted?.(msg)
              } else if (msg.status === 'failed') {
                cbRef.current.onFailed?.(msg.error)
              }
            }
            // The dedicated endpoint sends a 'connected' confirmation – ignore it
          } catch {
            // malformed message – ignore
          }
        }

        ws.onerror = () => {
          // Will trigger onclose next
        }

        ws.onclose = () => {
          wsRef.current = null
          if (cancelled) return
          // Fallback to polling immediately
          startPolling()
          // Attempt to reconnect after a delay
          reconnectRef.current = setTimeout(() => {
            if (!cancelled) connectWs()
          }, WS_RECONNECT_DELAY)
        }
      } catch {
        // WebSocket constructor failed – degrade to polling
        startPolling()
      }
    }

    connectWs()

    return () => {
      cancelled = true
      cleanup()
    }
  }, [taskId, enabled, cleanup, startPolling, stopPolling])

  return { connectionMode, cleanup }
}
