import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Check, CreditCard, Crown, Shield, Sparkles, X, Zap } from 'lucide-react'
import toast from 'react-hot-toast'


const plans = [
  {
    id: 'starter',
    name: '基础探索版',
    price: '免费',
    period: '',
    description: '适用于个人开发者、学生及轻量级模型对齐验证。',
    icon: Zap,
    tone: 'graphite',
    popular: false,
    features: ['基础沙盒攻击测试', '每月 100 次 API 并发调用', '标准漏洞摘要报告', 'Discord 社区技术支持'],
  },
  {
    id: 'pro',
    name: '红队专业版',
    price: '¥2,999',
    period: '/月',
    description: '专为高频安全评测、红蓝对抗及中型 AI 团队设计。',
    icon: Shield,
    tone: 'electric',
    popular: true,
    features: ['全栈高级与多模态渗透模块', '每月 10,000 次高优并发调用', '7x24 专属安全专家响应', '团队级漏洞图谱与审计留痕'],
  },
  {
    id: 'enterprise',
    name: '政企旗舰版',
    price: '定制',
    period: '',
    description: '面向大型组织，提供完全私有化部署与深度合规治理框架。',
    icon: Crown,
    tone: 'lava',
    popular: false,
    features: ['无限制 API 调用与算力独享', '100% 物理隔离私有化部署', '定制化靶场与合规安全策略', '原厂工程师驻场级保障'],
  },
]

import { WorkspacePageShell, WorkspacePanelIntro } from '../components/workspace'
import { itemVariants } from '../utils/animations'

export default function PricingPage() {
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [showCheckout, setShowCheckout] = useState(false)

  const handleSubscribe = (plan) => {
    if (plan.id === 'pro') {
      toast('付费订阅功能规划中，当前版本可免费使用全部核心能力。', { icon: 'ℹ️' })
      return
    }
    if (plan.id === 'enterprise') {
      toast.success('企业旗舰版意向已收到，专职架构师将在 24 小时内与您联络。')
      return
    }
    setSelectedPlan(plan)
    setShowCheckout(true)
  }

  const handlePayment = () => {
    setIsProcessing(true)
    window.setTimeout(() => {
      setIsProcessing(false)
      setShowCheckout(false)
      toast.success(`您已成功订阅 ${selectedPlan.name}，算力资源正在调配。`)
    }, 1500)
  }

  return (
    <WorkspacePageShell theme="pricing">
      <motion.div variants={itemVariants} className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-700 dark:text-amber-300">
        计费与订阅功能正在规划中。当前开源版本可免费使用攻击、防御、评估等核心能力。
      </motion.div>
      <motion.div variants={itemVariants}>
        <WorkspacePanelIntro
          theme="pricing"
          badgeLabel="订阅方案 · 算力配额"
          description="从轻量级验证到企业级治理，为红蓝对抗场景提供可扩展的算力与专家支持方案。"
        />
      </motion.div>

      <motion.section variants={itemVariants} className="card p-6 sm:p-8 bg-[var(--bg-glass-strong)] border-[var(--border-glass)] shadow-[inset_0_0_40px_rgba(6,182,212,0.02)] mb-8">
        <div className="relative z-10 grid gap-8 lg:grid-cols-[1.3fr_0.7fr]">
          <div className="space-y-5">
            <span className="badge border text-[10px] uppercase font-bold tracking-widest bg-cyan-500/10 text-cyan-500 border-cyan-500/20 px-3 py-1">透明与可扩展的算力矩阵</span>
            <h2 className="font-display text-3xl font-bold tracking-tight text-[var(--text-main)] sm:text-4xl leading-tight">
              构建更强韧的模型安全防线
            </h2>
            <p className="text-sm font-medium text-[var(--text-muted)] sm:text-base leading-relaxed max-w-2xl">
              所有方案均依托底层统一的渗透测试引擎。升级方案将解锁更高的并发吞吐量、更复杂的多模态攻击载荷以及企业级合规报告导出能力。
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
            <div className="ws-stat-mini">
              <p className="ws-stat-mini-label">架构保障</p>
              <p className="text-sm font-bold text-[var(--text-main)]">金融级安全沙盒隔离</p>
            </div>
            <div className="ws-stat-mini">
              <p className="ws-stat-mini-label">算力调度</p>
              <p className="text-sm font-bold text-[var(--text-main)]">全球分布式边缘推理</p>
            </div>
            <div className="ws-stat-mini">
              <p className="ws-stat-mini-label">合规标准</p>
              <p className="text-sm font-bold text-[var(--text-main)]">满足 ISO 27001 与 SOC2</p>
            </div>
          </div>
        </div>
      </motion.section>

      <div className="grid gap-6 lg:grid-cols-3">
        {plans.map((plan, index) => {
          const Icon = plan.icon
          const toneStyles = {
            graphite: 'border-[var(--border-glass-strong)] bg-[var(--bg-glass)] hover:bg-[var(--bg-glass-strong)] hover:border-cyan-500/20',
            electric: 'border-cyan-500/50 bg-cyan-500/5 shadow-[inset_0_0_20px_rgba(6,182,212,0.1),0_10px_30px_rgba(6,182,212,0.1)] transform scale-[1.02] z-10',
            lava: 'border-amber-500/30 bg-amber-500/5 hover:border-amber-500/50',
          }

          return (
            <motion.article
              key={plan.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + index * 0.1, ease: [0.22, 1, 0.36, 1], duration: 0.5 }}
              className={`ws-pricing-tier ${plan.popular ? 'ws-pricing-tier--featured' : ''} relative border p-8 flex flex-col ${toneStyles[plan.tone]}`}
            >
              {plan.popular && (
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 badge border text-[10px] uppercase font-bold tracking-widest bg-cyan-500 text-[var(--bg-main)] border-cyan-400 px-4 py-1.5 shadow-[0_0_15px_rgba(6,182,212,0.5)]">
                  <Sparkles className="h-3.5 w-3.5 mr-1" />
                  团队优选
                </div>
              )}

              <div className="mb-6 flex items-start gap-4">
                <div className={`shrink-0 rounded-xl p-3 shadow-lg border ${plan.popular ? 'bg-cyan-500/20 border-cyan-500/30 text-cyan-500' : plan.tone === 'lava' ? 'bg-amber-500/20 border-amber-500/30 text-amber-500' : 'bg-[var(--bg-glass-strong)] border-[var(--border-glass)] text-[var(--text-muted)]'}`}>
                  <Icon className="h-6 w-6" />
                </div>
                <div>
                  <h2 className={`text-xl font-bold font-display ${plan.popular ? 'text-cyan-500' : 'text-[var(--text-main)]'}`}>{plan.name}</h2>
                  <p className="mt-2 text-xs font-medium leading-relaxed text-[var(--text-muted)]">{plan.description}</p>
                </div>
              </div>

              <div className="mb-8 flex items-end gap-1">
                <span className="font-display text-4xl font-bold tracking-tight text-[var(--text-main)]">{plan.price}</span>
                {plan.period && <span className="pb-1 text-sm font-bold text-[var(--text-muted)]">{plan.period}</span>}
              </div>

              <div className="space-y-4 flex-1">
                {plan.features.map((feature) => (
                  <div key={feature} className="flex items-start gap-3">
                    <div className={`mt-0.5 shrink-0 rounded-full p-1 ${plan.popular ? 'bg-cyan-500/20 text-cyan-500' : 'bg-[var(--bg-glass-strong)] text-[var(--text-muted)]'}`}>
                      <Check className="h-3 w-3" />
                    </div>
                    <span className="text-sm font-medium text-[var(--text-muted)]">{feature}</span>
                  </div>
                ))}
              </div>

              <button
                type="button"
                onClick={() => handleSubscribe(plan)}
                className={`mt-10 w-full justify-center py-3.5 text-sm font-bold transition-all shadow-lg ${
                  plan.popular 
                    ? 'btn-primary bg-cyan-500 hover:bg-cyan-600 border-cyan-500 text-white shadow-cyan-500/30' 
                    : plan.tone === 'lava'
                      ? 'btn-secondary bg-amber-500/10 hover:bg-amber-500/20 border-amber-500/30 text-amber-500'
                      : 'btn-secondary bg-[var(--bg-glass)] hover:bg-[var(--bg-glass-strong)] text-[var(--text-main)] border-[var(--border-glass-strong)]'
                }`}
              >
                {plan.id === 'enterprise' ? '联络企业专家' : plan.id === 'starter' ? '免费接入引擎' : '立即升级算力'}
              </button>
            </motion.article>
          )
        })}
      </div>

      <AnimatePresence>
        {showCheckout && selectedPlan && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-md"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowCheckout(false)}
          >
            <motion.div
              className="w-full max-w-[520px] rounded-2xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass-strong)] p-8 shadow-[0_20px_50px_rgba(0,0,0,0.5)] relative overflow-hidden"
              initial={{ scale: 0.96, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.96, opacity: 0, y: 20 }}
              onClick={(event) => event.stopPropagation()}
            >
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-500 to-transparent opacity-50"></div>
              
              <div className="mb-8 flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-3 text-cyan-500 shadow-[inset_0_0_15px_rgba(6,182,212,0.2)]">
                    <CreditCard className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold font-display text-[var(--text-main)]">核对配额网关信息</h3>
                    <p className="mt-1 text-xs font-medium text-[var(--text-muted)]">加密通道已建立，交易受高强度加密保护。</p>
                  </div>
                </div>
                <button type="button" onClick={() => setShowCheckout(false)} className="rounded-lg p-2 text-[var(--text-muted)] hover:bg-[var(--bg-glass)] hover:text-[var(--text-main)] transition-colors">
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-6 mb-8">
                <div className="flex items-center justify-between text-sm text-[var(--text-muted)] mb-4">
                  <span className="font-bold uppercase tracking-widest text-[10px]">许可协议类型</span>
                  <span className="font-bold font-display text-cyan-500 text-base">{selectedPlan.name}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-bold uppercase tracking-widest text-[10px] text-[var(--text-muted)]">计费结算周期</span>
                  <span className="font-display text-3xl font-bold tracking-tight text-[var(--text-main)]">
                    {selectedPlan.price}
                    <span className="text-base text-[var(--text-muted)] font-normal ml-1">{selectedPlan.period}</span>
                  </span>
                </div>
              </div>

              <div className="space-y-5">
                <div>
                  <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest block mb-2">安全结算凭证号</label>
                  <input className="input-field font-mono tracking-widest text-lg py-3 px-4" placeholder="XXXX XXXX XXXX XXXX" />
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest block mb-2">有效周期</label>
                    <input className="input-field font-mono tracking-widest py-3 px-4" placeholder="MM / YY" />
                  </div>
                  <div>
                    <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest block mb-2">授权密匙 (CVV)</label>
                    <input className="input-field font-mono tracking-widest py-3 px-4" placeholder="•••" type="password" />
                  </div>
                </div>
              </div>

              <button 
                type="button" 
                onClick={handlePayment} 
                disabled={isProcessing} 
                className="btn-primary mt-10 w-full justify-center py-4 text-base bg-cyan-500 hover:bg-cyan-600 border-cyan-500 text-white font-bold shadow-[0_0_20px_rgba(6,182,212,0.3)] disabled:opacity-70 disabled:shadow-none"
              >
                {isProcessing ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-3" />
                    验证凭证并建立通道...
                  </>
                ) : (
                  `授权支付 ${selectedPlan.price}`
                )}
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </WorkspacePageShell>
  )
}
