import { useEffect, useRef } from 'react'

export function useAutoRefresh(callback, delay, enabled = true) {
  const callbackRef = useRef(callback)

  useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  useEffect(() => {
    if (!enabled || !delay) {
      return undefined
    }

    const id = window.setInterval(() => {
      callbackRef.current?.()
    }, delay)

    return () => window.clearInterval(id)
  }, [delay, enabled])
}

export default useAutoRefresh
