import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import AttackPage from './pages/AttackPage'
import NovelAttackPage from './pages/NovelAttackPage'
import DefensePage from './pages/DefensePage'
import BenchmarkPage from './pages/BenchmarkPage'
import HistoryPage from './pages/HistoryPage'
import Dashboard from './pages/Dashboard'
import CodeSecurityPage from './pages/CodeSecurityPage'
import BiasDetectionPage from './pages/BiasDetectionPage'
import SecurityDashboard from './pages/SecurityDashboard'
import OWASPPage from './pages/OWASPPage'
import RedTeamPage from './pages/RedTeamPage'
import AdvancedAttackPage from './pages/AdvancedAttackPage'
import TemplatePage from './pages/TemplatePage'
import ReportPage from './pages/ReportPage'
import TaskProgressPage from './pages/TaskProgressPage'
import AuditLogPage from './pages/AuditLogPage'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<SecurityDashboard />} />
          <Route path="/attack" element={<AttackPage />} />
          <Route path="/attack/advanced" element={<AdvancedAttackPage />} />
          <Route path="/attack/novel" element={<NovelAttackPage />} />
          <Route path="/defense" element={<DefensePage />} />
          <Route path="/benchmark" element={<BenchmarkPage />} />
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
      </Layout>
      <Toaster
        position="top-right"
        toastOptions={{
          className: '!bg-white !text-graphite-900 !text-sm !rounded-md !shadow-lifted',
          success: {
            iconTheme: {
              primary: '#16a34a',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#dc2626',
              secondary: '#fff',
            },
          },
        }}
      />
    </BrowserRouter>
  )
}

export default App
