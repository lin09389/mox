import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { Loader } from 'lucide-react'
import Layout from './components/Layout'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ProtectedRoute } from './components/ProtectedRoute'

const SecurityDashboard = lazy(() => import('./pages/SecurityDashboard'))
const AttackPage = lazy(() => import('./pages/AttackPage'))
const AdvancedAttackPage = lazy(() => import('./pages/AdvancedAttackPage'))
const NovelAttackPage = lazy(() => import('./pages/NovelAttackPage'))
const AgentAttackPage = lazy(() => import('./pages/AgentAttackPage'))
const MultimodalAttackPage = lazy(() => import('./pages/MultimodalAttackPage'))
const DefensePage = lazy(() => import('./pages/DefensePage'))
const BenchmarkPage = lazy(() => import('./pages/BenchmarkPage'))
const SafetyCardPage = lazy(() => import('./pages/SafetyCardPage'))
const HistoryPage = lazy(() => import('./pages/HistoryPage'))
const CodeSecurityPage = lazy(() => import('./pages/CodeSecurityPage'))
const BiasDetectionPage = lazy(() => import('./pages/BiasDetectionPage'))
const OWASPPage = lazy(() => import('./pages/OWASPPage'))
const RedTeamPage = lazy(() => import('./pages/RedTeamPage'))
const TemplatePage = lazy(() => import('./pages/TemplatePage'))
const DatasetPage = lazy(() => import('./pages/DatasetPage'))
const ReportPage = lazy(() => import('./pages/ReportPage'))
const TaskProgressPage = lazy(() => import('./pages/TaskProgressPage'))
const AuditLogPage = lazy(() => import('./pages/AuditLogPage'))
const AttackLoopPage = lazy(() => import('./pages/AttackLoopPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const PricingPage = lazy(() => import('./pages/PricingPage'))

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
              
              {/* Protected Routes */}
              <Route path="/" element={<ProtectedRoute><SecurityDashboard /></ProtectedRoute>} />
              <Route path="/attack" element={<ProtectedRoute><AttackPage /></ProtectedRoute>} />
              <Route path="/attack/advanced" element={<ProtectedRoute><AdvancedAttackPage /></ProtectedRoute>} />
              <Route path="/attack/novel" element={<ProtectedRoute><NovelAttackPage /></ProtectedRoute>} />
              <Route path="/attack/agent" element={<ProtectedRoute><AgentAttackPage /></ProtectedRoute>} />
              <Route path="/attack/multimodal" element={<ProtectedRoute><MultimodalAttackPage /></ProtectedRoute>} />
              <Route path="/attack/loop" element={<ProtectedRoute><AttackLoopPage /></ProtectedRoute>} />
              <Route path="/defense" element={<ProtectedRoute><DefensePage /></ProtectedRoute>} />
              <Route path="/benchmark" element={<ProtectedRoute><BenchmarkPage /></ProtectedRoute>} />
              <Route path="/safety-card" element={<ProtectedRoute><SafetyCardPage /></ProtectedRoute>} />
              <Route path="/history" element={<ProtectedRoute><HistoryPage /></ProtectedRoute>} />
              <Route path="/code-security" element={<ProtectedRoute><CodeSecurityPage /></ProtectedRoute>} />
              <Route path="/bias" element={<ProtectedRoute><BiasDetectionPage /></ProtectedRoute>} />
              <Route path="/owasp" element={<ProtectedRoute><OWASPPage /></ProtectedRoute>} />
              <Route path="/redteam" element={<ProtectedRoute><RedTeamPage /></ProtectedRoute>} />
              <Route path="/templates" element={<ProtectedRoute><TemplatePage /></ProtectedRoute>} />
              <Route path="/datasets" element={<ProtectedRoute><DatasetPage /></ProtectedRoute>} />
              <Route path="/reports" element={<ProtectedRoute><ReportPage /></ProtectedRoute>} />
              <Route path="/tasks" element={<ProtectedRoute><TaskProgressPage /></ProtectedRoute>} />
              <Route path="/audit" element={<ProtectedRoute><AuditLogPage /></ProtectedRoute>} />
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
