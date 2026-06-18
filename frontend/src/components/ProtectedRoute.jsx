import { Navigate, useLocation } from 'react-router-dom'
import { useAuthSession } from '../auth'

export function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthSession()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children
}
