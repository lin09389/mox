import { lazy } from 'react'
import { BarChart3, Shield, Code2, Scale } from 'lucide-react'
import HubShell from '../components/HubShell'
import { HUB_COPY } from '../constants/copy'

const BenchmarkPage = lazy(() => import('./BenchmarkPage'))
const SafetyCardPage = lazy(() => import('./SafetyCardPage'))
const CodeSecurityPage = lazy(() => import('./CodeSecurityPage'))
const BiasDetectionPage = lazy(() => import('./BiasDetectionPage'))

const TABS = [
  { id: 'benchmark', label: '安全基准测试', desc: '使用标准数据集对目标模型执行自动化对抗评测与打分。', icon: BarChart3, component: BenchmarkPage },
  { id: 'safety-card', label: '模型安全卡片', desc: '自动化扫描合规缺陷，生成多维度风险态势画像。', icon: Shield, component: SafetyCardPage },
  { id: 'code-security', label: '代码安全评估', desc: 'AI 静态代码分析，快速识别 CWE 漏洞与注入风险。', icon: Code2, component: CodeSecurityPage },
  { id: 'bias', label: '偏见与公平性', desc: '检测性别、种族、年龄等维度的公平性与偏见风险。', icon: Scale, component: BiasDetectionPage },
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
      theme="evaluation"
      defaultTab="benchmark"
      tabStorageKey="mox_hub_evaluation_tab"
      tabs={TABS}
    />
  )
}