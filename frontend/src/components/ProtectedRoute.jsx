import { Navigate, useLocation } from 'react-router-dom'
import { DEMO_MODE_ENABLED, useAuthSession } from '../auth'

export function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthSession()
  const location = useLocation()

  if (DEMO_MODE_ENABLED) {
    return children
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children
}
