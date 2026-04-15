import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { Loader } from 'lucide-react'
import Layout from './components/Layout'

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
const ReportPage = lazy(() => import('./pages/ReportPage'))
const TaskProgressPage = lazy(() => import('./pages/TaskProgressPage'))
const AuditLogPage = lazy(() => import('./pages/AuditLogPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const PricingPage = lazy(() => import('./pages/PricingPage'))

function PageLoader() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4" aria-live="polite" aria-busy="true">
      <div className="rounded-[20px] border border-white/80 bg-white/82 p-5 shadow-soft">
        <Loader className="h-8 w-8 animate-spin text-electric-700" />
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
          <Routes>
            <Route path="/" element={<SecurityDashboard />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/attack" element={<AttackPage />} />
            <Route path="/attack/advanced" element={<AdvancedAttackPage />} />
            <Route path="/attack/novel" element={<NovelAttackPage />} />
            <Route path="/attack/agent" element={<AgentAttackPage />} />
            <Route path="/attack/multimodal" element={<MultimodalAttackPage />} />
            <Route path="/defense" element={<DefensePage />} />
            <Route path="/benchmark" element={<BenchmarkPage />} />
            <Route path="/safety-card" element={<SafetyCardPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/code-security" element={<CodeSecurityPage />} />
            <Route path="/bias" element={<BiasDetectionPage />} />
            <Route path="/owasp" element={<OWASPPage />} />
            <Route path="/redteam" element={<RedTeamPage />} />
            <Route path="/templates" element={<TemplatePage />} />
            <Route path="/reports" element={<ReportPage />} />
            <Route path="/tasks" element={<TaskProgressPage />} />
            <Route path="/audit" element={<AuditLogPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
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
