import {
  BarChart3,
  Clock3,
  Cpu,
  Database,
  LayoutDashboard,
  Shield,
  Sword,
} from 'lucide-react'

export const NAV_GROUPS = [
  {
    title: '监控',
    items: [
      { path: '/', label: '安全总览', short: '总览', icon: LayoutDashboard },
      { path: '/tasks', label: '任务调度', short: '任务', icon: Clock3 },
    ],
  },
  {
    title: '测试',
    items: [
      { path: '/attack', label: '单点渗透测试', short: '渗透', icon: Sword },
      { path: '/testing', label: '自动化引擎', short: '自动', icon: Cpu },
    ],
  },
  {
    title: '分析',
    items: [
      { path: '/evaluation', label: '能力基准评估', short: '评测', icon: BarChart3 },
      { path: '/defense', label: '防御验证', short: '防御', icon: Shield },
    ],
  },
  {
    title: '资产与审计',
    items: [
      { path: '/governance', label: '资产与治理', short: '治理', icon: Database },
    ],
  },
]

export const HUB_COPY = {
  attack: {
    title: '渗透测试中心',
    description: '统一的攻击与渗透工作台，包含从基础文本到多模态的全维度测试手段。',
    accentClass: 'text-cyan-400',
    tabIndicatorClass: 'bg-cyan-400',
    layoutId: 'attack-hub-tab',
  },
  testing: {
    title: '自动化引擎',
    description: '高并发的自动化评测引擎，支持完全自主的智能 Agent 红队和固定跑批任务。',
    accentClass: 'text-purple-400',
    tabIndicatorClass: 'bg-purple-400',
    layoutId: 'auto-testing-hub-tab',
  },
  evaluation: {
    title: '能力基准与评估',
    description: '标准化的大语言模型能力评估体系与专项安全测评（如代码安全、偏见歧视）。',
    accentClass: 'text-green-400',
    tabIndicatorClass: 'bg-green-400',
    layoutId: 'evaluation-hub-tab',
  },
  governance: {
    title: '资产与治理',
    description: '统一管理测试记录、漏洞报告、安全模板、对抗数据集及系统审计日志。',
    accentClass: 'text-yellow-400',
    tabIndicatorClass: 'bg-yellow-400',
    layoutId: 'governance-hub-tab',
  },
}