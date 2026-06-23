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
  { id: 'canvas', label: '智能编排画布', icon: Network, component: AgentCanvasPage },
  { id: 'auto-redteam', label: '自动红队', icon: Cpu, component: AutoRedTeamPage },
  { id: 'loop', label: '攻击循环', icon: RefreshCw, component: AttackLoopPage },
  { id: 'owasp', label: 'OWASP 评测', icon: ShieldAlert, component: OWASPPage },
  { id: 'redteam', label: '传统红队剧本', icon: Target, component: RedTeamPage },
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
      defaultTab="auto-redteam"
      tabStorageKey="mox_hub_testing_tab"
      tabs={TABS}
    />
  )
}