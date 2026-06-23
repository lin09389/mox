import { lazy } from 'react'
import { Cpu, RefreshCw, ShieldAlert, Target, Network } from 'lucide-react'
import HubShell from '../components/HubShell'
import { HUB_COPY } from '../constants/copy'

const AgentCanvasPage = lazy(() => import('./AgentCanvasPage'))
const AutoRedTeamPage = lazy(() => import('./AutoRedTeamPage'))
const AttackLoopPage = lazy(() => import('./AttackLoopPage'))
const OWASPPage = lazy(() => import('./OWASPPage'))
const RedTeamPage = lazy(() => import('./RedTeamPage'))

const TABS = [
  { id: 'canvas', label: '智能编排画布', desc: '可视化编排多 Agent 攻击链路，拖拽式构建复杂渗透剧本。', icon: Network, component: AgentCanvasPage },
  { id: 'auto-redteam', label: '自动红队', desc: '自主 Agent 持续探测目标模型，实时输出 ReAct 推理与发现项。', icon: Cpu, component: AutoRedTeamPage },
  { id: 'loop', label: '攻击循环', desc: '高并发矩阵跑批，组合模型×攻击类型×提示词批量压测。', icon: RefreshCw, component: AttackLoopPage },
  { id: 'owasp', label: 'OWASP 评测', desc: '按 OWASP LLM Top 10 标准类目评估模型关键风险域通过率。', icon: ShieldAlert, component: OWASPPage },
  { id: 'redteam', label: '传统红队剧本', desc: '按攻击技术组合进行红队压力测试，快速定位能力缺口。', icon: Target, component: RedTeamPage },
]

const copy = HUB_COPY.testing

export default function AutoTestingHubPage() {
  return (
    <HubShell
      icon={Cpu}
      title={copy.title}
      description={copy.description}
      accentClass={copy.accentClass}
      tabIndicatorClass={copy.tabIndicatorClass}
      layoutId={copy.layoutId}
      theme="testing"
      defaultTab="auto-redteam"
      tabStorageKey="mox_hub_testing_tab"
      tabs={TABS}
    />
  )
}