import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { Loader } from 'lucide-react'
import Layout from './components/Layout'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ProtectedRoute } from './components/ProtectedRoute'

const SecurityDashboard = lazy(() => import('./pages/SecurityDashboard'))
const TaskProgressPage = lazy(() => import('./pages/TaskProgressPage'))
const AttackHubPage = lazy(() => import('./pages/AttackHubPage'))
const AutoTestingHubPage = lazy(() => import('./pages/AutoTestingHubPage'))
const EvaluationHubPage = lazy(() => import('./pages/EvaluationHubPage'))
const GovernanceHubPage = lazy(() => import('./pages/GovernanceHubPage'))
const DefensePage = lazy(() => import('./pages/DefensePage'))

const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const PricingPage = lazy(() => import('./pages/PricingPage'))

function GovernanceTabRedirect({ tab }) {
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  params.set('tab', tab)
  return <Navigate to={`/governance?${params.toString()}`} replace />
}

function PageLoader() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4" aria-live="polite" aria-busy="true">
      <div className="rounded-[20px] border border-white/80 bg-white/82 p-5 shadow-soft">
        <Loader className="h-8 w-8 animate-spin text-electric-600" />
      </div>
      <div className="text-center">
        <p className="text-sm font-medium text-graphite-700">页面正在加载</p>
        <p className="mt-1 text-xs text-graphite-500">我们正在准备模块资源与页面数据。</p>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Suspense fallback={<PageLoader />}>
          <ErrorBoundary>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/pricing" element={<PricingPage />} />

              <Route path="/" element={<ProtectedRoute><SecurityDashboard /></ProtectedRoute>} />
              <Route path="/tasks" element={<ProtectedRoute><TaskProgressPage /></ProtectedRoute>} />

              <Route path="/attack" element={<ProtectedRoute><AttackHubPage /></ProtectedRoute>} />
              <Route path="/testing" element={<ProtectedRoute><AutoTestingHubPage /></ProtectedRoute>} />
              <Route path="/evaluation" element={<ProtectedRoute><EvaluationHubPage /></ProtectedRoute>} />
              <Route path="/defense" element={<ProtectedRoute><DefensePage /></ProtectedRoute>} />
              <Route path="/governance" element={<ProtectedRoute><GovernanceHubPage /></ProtectedRoute>} />

              {/* Legacy redirects */}
              <Route path="/auto-redteam" element={<Navigate to="/testing?tab=auto-redteam" replace />} />
              <Route path="/canvas" element={<Navigate to="/testing?tab=canvas" replace />} />
              <Route path="/benchmark" element={<Navigate to="/evaluation?tab=benchmark" replace />} />
              <Route path="/datasets" element={<GovernanceTabRedirect tab="datasets" />} />
              <Route path="/templates" element={<GovernanceTabRedirect tab="templates" />} />
              <Route path="/reports" element={<GovernanceTabRedirect tab="reports" />} />
              <Route path="/audit" element={<GovernanceTabRedirect tab="audit" />} />
              <Route path="/history" element={<GovernanceTabRedirect tab="history" />} />

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ErrorBoundary>
        </Suspense>
      </Layout>
      <Toaster
        position="top-right"
        toastOptions={{
          className:
            '!rounded-[18px] !border !border-white/80 !bg-white/94 !px-3 !py-3 !text-sm !text-graphite-900 !shadow-soft',
          success: {
            iconTheme: {
              primary: '#188850',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#c83c12',
              secondary: '#fff',
            },
          },
        }}
      />
    </BrowserRouter>
  )
}