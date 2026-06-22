import { lazy } from 'react'
import { BarChart3, Shield, Code2, Scale } from 'lucide-react'
import HubShell from '../components/HubShell'
import { HUB_COPY } from '../constants/copy'

const BenchmarkPage = lazy(() => import('./BenchmarkPage'))
const SafetyCardPage = lazy(() => import('./SafetyCardPage'))
const CodeSecurityPage = lazy(() => import('./CodeSecurityPage'))
const BiasDetectionPage = lazy(() => import('./BiasDetectionPage'))

const TABS = [
  { id: 'benchmark', label: '安全基准测试', icon: BarChart3, component: BenchmarkPage },
  { id: 'safety-card', label: '模型安全卡片', icon: Shield, component: SafetyCardPage },
  { id: 'code-security', label: '代码安全评估', icon: Code2, component: CodeSecurityPage },
  { id: 'bias', label: '偏见与公平性', icon: Scale, component: BiasDetectionPage },
]

const copy = HUB_COPY.evaluation

export default function EvaluationHubPage() {
  return (
    <HubShell
      icon={BarChart3}
      title={copy.title}
      description={copy.description}
      accentClass={copy.accentClass}
      tabIndicatorClass={copy.tabIndicatorClass}
      layoutId={copy.layoutId}
      defaultTab="benchmark"
      tabStorageKey="mox_hub_evaluation_tab"
      tabs={TABS}
    />
  )
}