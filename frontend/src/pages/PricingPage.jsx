import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Check, CreditCard, Crown, Shield, Sparkles, X, Zap } from 'lucide-react'
import toast from 'react-hot-toast'
import { PageHeader } from '../components/ui/AppFrame'

const plans = [
  {
    id: 'starter',
    name: '基础版',
    price: '免费',
    period: '',
    description: '适合个人开发者和轻量级安全验证。',
    icon: Zap,
    tone: 'graphite',
    features: ['基础攻击测试', '每月 100 次 API 调用', '基础报告导出', '社区支持'],
  },
  {
    id: 'pro',
    name: '专业版',
    price: '¥2,999',
    period: '/月',
    description: '适合高频评测、团队协作和更完整的攻防闭环。',
    icon: Shield,
    tone: 'electric',
    popular: true,
    features: ['全部基础版能力', '高级攻击与多模态模块', '每月 10,000 次 API 调用', '7x24 技术支持', '团队级报告与留痕'],
  },
  {
    id: 'enterprise',
    name: '企业版',
    price: '定制',
    period: '',
    description: '适合大型组织、私有化部署与合规治理场景。',
    icon: Crown,
    tone: 'lava',
    features: ['全部专业版能力', '私有化部署', '无限 API 调用', '专属顾问支持', '定制化安全策略与报表'],
  },
]

export default function PricingPage() {
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [showCheckout, setShowCheckout] = useState(false)

  const handleSubscribe = (plan) => {
    if (plan.id === 'enterprise') {
      toast.success('企业版咨询请求已记录，我们会尽快联系你。')
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
      toast.success(`已成功订阅 ${selectedPlan.name}。`)
    }, 1200)
  }

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="PLANS"
        title="适合安全团队的订阅方案"
        description="这次定价页不再走营销站浮夸路线，而是保持和产品一致的专业监控台风格，让方案信息更清晰、动作更直接。"
      />

      <section className="hero-panel">
        <div className="relative z-10 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-4">
            <span className="badge badge-neutral">统一品牌体验 · 更清晰的方案层级</span>
            <h2 className="font-display text-3xl font-bold tracking-tight text-graphite-950 sm:text-4xl">
              从轻量验证到企业治理，按真实攻防需求选择。
            </h2>
            <p className="text-sm text-graphite-600 sm:text-base">
              所有方案都围绕同一条主线：更稳定的评测流程、更清晰的结果沉淀、以及更可持续的安全运营能力。
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            <div className="rounded-[20px] border border-white/80 bg-white/72 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-graphite-400">统一设计</p>
              <p className="mt-2 text-sm font-semibold text-graphite-900">与主应用视觉一致</p>
            </div>
            <div className="rounded-[20px] border border-white/80 bg-white/72 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-graphite-400">聚焦决策</p>
              <p className="mt-2 text-sm font-semibold text-graphite-900">突出能力边界与调用量</p>
            </div>
            <div className="rounded-[20px] border border-white/80 bg-white/72 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-graphite-400">专业感</p>
              <p className="mt-2 text-sm font-semibold text-graphite-900">更像产品控制台，而不是广告页</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        {plans.map((plan, index) => {
          const Icon = plan.icon
          const toneStyles = {
            graphite: 'border-graphite-200 bg-white/82',
            electric: 'border-electric-200 bg-electric-50/80',
            lava: 'border-lava-200 bg-lava-50/80',
          }

          return (
            <motion.article
              key={plan.id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.08 }}
              className={`relative rounded-[28px] border p-6 shadow-fine ${toneStyles[plan.tone]} ${
                plan.popular ? 'shadow-glow-electric' : ''
              }`}
            >
              {plan.popular && (
                <div className="absolute right-5 top-5 badge badge-success">
                  <Sparkles className="h-3.5 w-3.5" />
                  推荐
                </div>
              )}

              <div className="mb-6 flex items-center gap-3">
                <div className="rounded-[18px] bg-white/82 p-3 shadow-fine">
                  <Icon className="h-5 w-5 text-graphite-900" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-graphite-950">{plan.name}</h2>
                  <p className="text-sm text-graphite-500">{plan.description}</p>
                </div>
              </div>

              <div className="mb-6 flex items-end gap-1">
                <span className="font-display text-4xl font-bold tracking-tight text-graphite-950">{plan.price}</span>
                {plan.period ? <span className="pb-1 text-sm text-graphite-500">{plan.period}</span> : null}
              </div>

              <div className="space-y-3">
                {plan.features.map((feature) => (
                  <div key={feature} className="flex items-start gap-3 rounded-[18px] border border-white/70 bg-white/72 px-4 py-3">
                    <Check className="mt-0.5 h-4 w-4 text-neon-600" />
                    <span className="text-sm text-graphite-700">{feature}</span>
                  </div>
                ))}
              </div>

              <button
                type="button"
                onClick={() => handleSubscribe(plan)}
                className={`mt-6 w-full justify-center ${plan.popular ? 'btn-primary' : 'btn-secondary'}`}
              >
                {plan.id === 'enterprise' ? '联系销售' : '立即订阅'}
              </button>
            </motion.article>
          )
        })}
      </section>

      <AnimatePresence>
        {showCheckout && selectedPlan && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-graphite-950/35 p-4 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowCheckout(false)}
          >
            <motion.div
              className="w-full max-w-[520px] rounded-[28px] border border-white/80 bg-[#f9fbff] p-6 shadow-modal"
              initial={{ scale: 0.96, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.96, opacity: 0 }}
              onClick={(event) => event.stopPropagation()}
            >
              <div className="mb-5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="rounded-[18px] bg-electric-50 p-3 text-electric-700">
                    <CreditCard className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-graphite-950">确认订阅信息</h3>
                    <p className="text-sm text-graphite-500">支付弹层也已统一为控制台风格。</p>
                  </div>
                </div>
                <button type="button" onClick={() => setShowCheckout(false)} className="btn-ghost px-2 py-2">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="rounded-[22px] border border-graphite-200/70 bg-white/80 p-4">
                <div className="flex items-center justify-between text-sm text-graphite-500">
                  <span>订阅方案</span>
                  <span className="font-medium text-graphite-900">{selectedPlan.name}</span>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-sm text-graphite-500">应付金额</span>
                  <span className="font-display text-3xl font-bold tracking-tight text-graphite-950">
                    {selectedPlan.price}
                    {selectedPlan.period}
                  </span>
                </div>
              </div>

              <div className="mt-5 space-y-4">
                <div>
                  <label className="label">银行卡号</label>
                  <input className="input-field font-mono" placeholder="0000 0000 0000 0000" />
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="label">有效期</label>
                    <input className="input-field" placeholder="MM / YY" />
                  </div>
                  <div>
                    <label className="label">安全码</label>
                    <input className="input-field" placeholder="123" />
                  </div>
                </div>
              </div>

              <button type="button" onClick={handlePayment} disabled={isProcessing} className="btn-primary mt-6 w-full justify-center py-3">
                {isProcessing ? (
                  <>
                    <div className="spinner" />
                    正在处理支付
                  </>
                ) : (
                  `确认支付 ${selectedPlan.price}${selectedPlan.period}`
                )}
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
