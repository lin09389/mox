import { lazy } from 'react'
import { FileText, History, BookOpen, Database, Activity } from 'lucide-react'
import HubShell from '../components/HubShell'
import { HUB_COPY } from '../constants/copy'

const HistoryPage = lazy(() => import('./HistoryPage'))
const ReportPage = lazy(() => import('./ReportPage'))
const TemplatePage = lazy(() => import('./TemplatePage'))
const DatasetPage = lazy(() => import('./DatasetPage'))
const AuditLogPage = lazy(() => import('./AuditLogPage'))

const TABS = [
  { id: 'history', label: '测试历史', icon: History, component: HistoryPage },
  { id: 'reports', label: '评估报告', icon: FileText, component: ReportPage },
  { id: 'templates', label: '模板中心', icon: BookOpen, component: TemplatePage },
  { id: 'datasets', label: '数据集管理', icon: Database, component: DatasetPage },
  { id: 'audit', label: '审计日志', icon: Activity, component: AuditLogPage },
]

const copy = HUB_COPY.governance

export default function GovernanceHubPage() {
  return (
    <HubShell
      icon={Database}
      title={copy.title}
      description={copy.description}
      accentClass={copy.accentClass}
      tabIndicatorClass={copy.tabIndicatorClass}
      layoutId={copy.layoutId}
      defaultTab="reports"
      tabStorageKey="mox_hub_governance_tab"
      tabs={TABS}
    />
  )
}