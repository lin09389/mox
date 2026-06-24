import { Shield, Zap } from 'lucide-react'

export const TABS = [
  { id: 'attack', label: '攻击记录', icon: Zap },
  { id: 'defense', label: '防御记录', icon: Shield },
]

export const ATTACK_LABELS = {
  prompt_injection: '提示词注入',
  jailbreak: '越狱攻击',
  gcg: 'GCG 攻击',
  auto_dan: 'AutoDAN',
}

export const DEFENSE_LABELS = {
  input_filter: '输入过滤',
  output_filter: '输出过滤',
}

export const badgeForAttackResult = (result) =>
  result === 'success'
    ? 'badge-danger border-rose-500/30 bg-rose-500/10 text-rose-500'
    : 'badge-success border-emerald-500/30 bg-emerald-500/10 text-emerald-500'

export const badgeForDefenseResult = (malicious) =>
  malicious
    ? 'badge-danger border-rose-500/30 bg-rose-500/10 text-rose-500'
    : 'badge-success border-emerald-500/30 bg-emerald-500/10 text-emerald-500'

export function formatDate(dateStr) {
  const date = new Date(dateStr)
  const diff = Date.now() - date.getTime()
  if (diff < 60_000) return '刚刚'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} 小时前`
  return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}