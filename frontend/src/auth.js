import { useEffect, useState } from 'react'

const STORAGE_KEY = 'mox.auth.session'
const AUTH_EVENT = 'mox:auth-changed'

export const DEMO_MODE_ENABLED = import.meta.env.VITE_DEMO_MODE === 'true'

function emitAuthChange() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(AUTH_EVENT))
  }
}

function isValidSession(obj) {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    typeof obj.accessToken === 'string' &&
    obj.accessToken.length > 0 &&
    typeof obj.expiresAt === 'number' &&
    obj.expiresAt > 0
  )
}

export function getStoredSession() {
  if (typeof window === 'undefined') {
    return null
  }

  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) {
    return null
  }

  try {
    const session = JSON.parse(raw)
    if (!isValidSession(session)) {
      window.localStorage.removeItem(STORAGE_KEY)
      return null
    }
    if (Date.now() > session.expiresAt) {
      window.localStorage.removeItem(STORAGE_KEY)
      return null
    }
    return session
  } catch {
    window.localStorage.removeItem(STORAGE_KEY)
    return null
  }
}

export function getAccessToken() {
  return getStoredSession()?.accessToken ?? null
}

export function isAuthenticated() {
  return Boolean(getAccessToken())
}

export function persistSession(payload) {
  if (typeof window === 'undefined') {
    return null
  }

  const expiresInMs = Number(payload.expires_in || 1800) * 1000
  const session = {
    accessToken: payload.access_token,
    tokenType: payload.token_type || 'bearer',
    user: payload.user || null,
    issuedAt: Date.now(),
    expiresAt: Date.now() + expiresInMs,
  }

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
  emitAuthChange()
  return session
}

export function clearSession() {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.removeItem(STORAGE_KEY)
  emitAuthChange()
}

export function useAuthSession() {
  const [session, setSession] = useState(() => getStoredSession())

  useEffect(() => {
    const sync = () => setSession(getStoredSession())
    window.addEventListener('storage', sync)
    window.addEventListener(AUTH_EVENT, sync)
    return () => {
      window.removeEventListener('storage', sync)
      window.removeEventListener(AUTH_EVENT, sync)
    }
  }, [])

  return {
    session,
    isAuthenticated: Boolean(session?.accessToken),
  }
}
