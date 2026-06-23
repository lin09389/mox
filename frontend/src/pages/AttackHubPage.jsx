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
  {
    id: 'basic',
    label: '基础攻击',
    desc: '提示词注入、越狱与梯度对抗——单轮渗透测试的核心入口。',
    icon: Sword,
    component: AttackPage,
  },
  {
    id: 'advanced',
    label: '高级攻击',
    desc: 'Token 走私、知识提取与 GCG++ 梯度搜索的组合矩阵渗透。',
    icon: Zap,
    component: AdvancedAttackPage,
  },
  {
    id: 'novel',
    label: '新型攻击',
    desc: 'Tokenizer 旁路、控制字符隐写与 RAG 投毒等零日攻击向量。',
    icon: Wand2,
    component: NovelAttackPage,
  },
  {
    id: 'agent',
    label: 'Agent 攻击',
    desc: '工具链滥用、权限提升与多 Agent 协同链路的沙箱突破测试。',
    icon: Sparkles,
    component: AgentAttackPage,
  },
  {
    id: 'multimodal',
    label: '多模态攻击',
    desc: '图像隐写、音频混淆与跨模态协同注入的对抗样本生成。',
    icon: Target,
    component: MultimodalAttackPage,
  },
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
      theme="attack"
      defaultTab="basic"
      tabStorageKey="mox_hub_attack_tab"
      tabs={TABS}
    />
  )
}