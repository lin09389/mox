import {
  BarChart3,
  Clock3,
  Cpu,
  CreditCard,
  Database,
  LayoutDashboard,
  LogIn,
  Shield,
  ShieldAlert,
  Sparkles,
} from 'lucide-react'

export const WORKSPACE_THEME_META = {
  default: {
    badgeSuffix: '工作台',
    badgeIcon: Sparkles,
    showPulse: false,
    showGrid: false,
  },
  testing: {
    badgeSuffix: '引擎模块',
    badgeIcon: Cpu,
    showPulse: true,
    showGrid: true,
  },
  evaluation: {
    badgeSuffix: '评测维度',
    badgeIcon: BarChart3,
    showPulse: true,
    showGrid: true,
  },
  governance: {
    badgeSuffix: '治理资产',
    badgeIcon: Database,
    showPulse: false,
    showGrid: true,
  },
  defense: {
    badgeSuffix: '防御链路',
    badgeIcon: Shield,
    showPulse: true,
    showGrid: true,
  },
  dashboard: {
    badgeSuffix: '态势感知',
    badgeIcon: LayoutDashboard,
    showPulse: true,
    showGrid: true,
  },
  tasks: {
    badgeSuffix: '任务队列',
    badgeIcon: Clock3,
    showPulse: true,
    showGrid: true,
  },
  auth: {
    badgeSuffix: '身份认证',
    badgeIcon: LogIn,
    showPulse: false,
    showGrid: true,
  },
  pricing: {
    badgeSuffix: '订阅方案',
    badgeIcon: CreditCard,
    showPulse: false,
    showGrid: true,
  },
  attack: {
    badgeSuffix: '渗透向量',
    badgeIcon: ShieldAlert,
    showPulse: true,
    showGrid: true,
  },
}