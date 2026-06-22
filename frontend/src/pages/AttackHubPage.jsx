import { lazy } from 'react'
import { Sword, Zap, Wand2, Sparkles, Target } from 'lucide-react'
import HubShell from '../components/HubShell'
import { HUB_COPY } from '../constants/copy'

const AttackPage = lazy(() => import('./AttackPage'))
const AdvancedAttackPage = lazy(() => import('./AdvancedAttackPage'))
const NovelAttackPage = lazy(() => import('./NovelAttackPage'))
const AgentAttackPage = lazy(() => import('./AgentAttackPage'))
const MultimodalAttackPage = lazy(() => import('./MultimodalAttackPage'))

const TABS = [
  { id: 'basic', label: '基础攻击', icon: Sword, component: AttackPage },
  { id: 'advanced', label: '高级攻击', icon: Zap, component: AdvancedAttackPage },
  { id: 'novel', label: '新型攻击', icon: Wand2, component: NovelAttackPage },
  { id: 'agent', label: 'Agent 攻击', icon: Sparkles, component: AgentAttackPage },
  { id: 'multimodal', label: '多模态攻击', icon: Target, component: MultimodalAttackPage },
]

const copy = HUB_COPY.attack

export default function AttackHubPage() {
  return (
    <HubShell
      icon={Sword}
      title={copy.title}
      description={copy.description}
      accentClass={copy.accentClass}
      tabIndicatorClass={copy.tabIndicatorClass}
      layoutId={copy.layoutId}
      defaultTab="basic"
      tabStorageKey="mox_hub_attack_tab"
      tabs={TABS}
    />
  )
}