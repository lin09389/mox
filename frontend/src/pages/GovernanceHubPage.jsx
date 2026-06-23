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
  { id: 'history', label: '测试历史', desc: '统一查看攻击与防御记录，支持搜索、排序、导出与移动端浏览。', icon: History, component: HistoryPage },
  { id: 'reports', label: '评估报告', desc: '汇总红队与基准测试结果，生成可分享的安全评估报告。', icon: FileText, component: ReportPage },
  { id: 'templates', label: '模板中心', desc: '管理攻击/防御提示词模板，加速日常测试配置。', icon: BookOpen, component: TemplatePage },
  { id: 'datasets', label: '数据集管理', desc: '维护对抗样本与基准数据集，支撑批量评测任务。', icon: Database, component: DatasetPage },
  { id: 'audit', label: '审计日志', desc: '监控平台接口行为、状态码和响应时延，追溯安全事件。', icon: Activity, component: AuditLogPage },
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
      theme="governance"
      defaultTab="reports"
      tabStorageKey="mox_hub_governance_tab"
      tabs={TABS}
    />
  )
}