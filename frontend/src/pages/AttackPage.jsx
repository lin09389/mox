import { useCallback, useEffect, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { BarChart3, ShieldAlert, Sparkles, TerminalSquare } from 'lucide-react'
import { AttackForm, AttackResult, DEFAULT_MODELS } from '../components/attack'
import { attackApi, getModels, isDemoModeEnabled } from '../api'
import { useLocalStorage } from '../hooks/useCommon'
import { useAttackTemplates } from '../hooks/useAttackTemplates'
import { HeroStat, InfoCallout, PageHeader, QuickLink, StatusPill } from '../components/ui/AppFrame'

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.1 }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] } }
}

function buildDemoResult(formData) {
  const normalized = Math.min(0.94, 0.18 + formData.max_iterations / 140 + formData.prompt.length / 900)
  const succeeded = normalized >= 0.58

  return {
    _demo_mode: true,
    result: succeeded ? 'success' : 'failure',
    success_score: Number(normalized.toFixed(2)),
    iterations: Math.max(1, Math.min(formData.max_iterations, 24)),
    adversarial_prompt: `${formData.prompt}\n\n[DEMO] Prompt variations were generated locally for interface preview.`,
    model_response: succeeded
      ? 'Demo mode: the target model showed signs of policy drift and partial unsafe completion.'
      : 'Demo mode: the target model rejected the unsafe request and kept the safety boundary intact.',
    recommendations: succeeded
      ? [
          { priority: 'P1', content: 'Strengthen the system prompt and add stricter instruction-boundary checks.' },
          { priority: 'P1', content: 'Add input filtering and high-risk response review before final output.' },
          { priority: 'P2', content: 'Turn this prompt into a regression test so the fix stays verified.' },
        ]
      : [
          { priority: 'P2', content: 'Increase prompt coverage with more paraphrases and multi-turn variants.' },
          { priority: 'P3', content: 'Cross-check the same scenario in red-team and multimodal flows.' },
        ],
    _warning: 'The backend is unavailable, so this result is generated in demo mode.',
  }
}

export default function AttackPage() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [apiConnected, setApiConnected] = useState(true)
  const [modelList, setModelList] = useState(DEFAULT_MODELS)

  const { getTemplatesByCategory } = useAttackTemplates()
  const basicTemplates = getTemplatesByCategory('basic')

  const [form, setForm] = useLocalStorage('attack_form', {
    attack_type: 'prompt_injection',
    model: 'gpt-4',
    prompt: '',
    target_behavior: '',
    max_iterations: 10,
  })

  useEffect(() => {
    void checkApiStatus()
    void loadModels()
  }, [checkApiStatus, loadModels])

  const quickFacts = useMemo(
    () => [
      { label: 'Model', value: form.model, hint: 'Target model for evaluation', tone: 'electric' },
      { label: 'Iterations', value: form.max_iterations, hint: 'Search depth', tone: 'warning' },
      {
        label: 'Run mode',
        value: apiConnected ? 'Live API' : isDemoModeEnabled ? 'Demo mode' : 'Offline',
        hint: apiConnected ? 'Connected to backend' : 'Local simulation',
        tone: apiConnected ? 'success' : 'danger',
      },
    ],
    [apiConnected, form.max_iterations, form.model]
  )

  const loadModels = useCallback(async () => {
    try {
      const models = await getModels()
      if (models.length > 0) {
        setModelList(models.map((model) => ({ value: model, label: model, provider: 'Auto detected' })))
      }
    } catch {
      setModelList(DEFAULT_MODELS)
    }
  }, [])

  const checkApiStatus = useCallback(async () => {
    try {
      await attackApi.test()
      setApiConnected(true)
    } catch {
      setApiConnected(false)
    }
  }, [])

  const handleSubmit = useCallback(async (formData) => {
    setLoading(true)
    setResult(null)

    try {
      if (!apiConnected) {
        if (!isDemoModeEnabled) {
          toast.error('The backend is offline. Live attack execution is unavailable.')
          return
        }

        await new Promise((resolve) => window.setTimeout(resolve, 900))
        setResult(buildDemoResult(formData))
        toast.success('Simulation completed in demo mode.')
        return
      }

      const data = await attackApi.run(formData)
      setResult(data)
      toast.success('Attack execution completed successfully.')
    } catch (error) {
      if (error.name === 'CanceledError' || error.name === 'AbortError') {
        return
      }
      const detail = error.response?.data?.detail || error.response?.data?.message || 'Request failed.'
      toast.error(detail)
      if (isDemoModeEnabled) {
        setResult(buildDemoResult(formData))
      }
    } finally {
      setLoading(false)
    }
  }, [apiConnected])

  function handleLoadTemplate(template) {
    setForm((current) => ({
      ...current,
      prompt: template.content || template.prompt || '',
      target_behavior: template.target || current.target_behavior,
    }))
    toast.success(`Template applied: ${template.name}`)
  }

  return (
    <motion.div 
      className="page-shell"
      variants={containerVariants}
      initial="hidden"
      animate="show"
    >
      <motion.div variants={itemVariants}>
        <PageHeader
          eyebrow="ATTACK LAB"
          title="模型攻击测试"
          description="执行自动化对抗测试，评估大模型在极端情况下的安全边界与响应策略。"
          badge={<StatusPill online={apiConnected} onlineLabel="引擎在线" offlineLabel="离线模式" />}
        />
      </motion.div>

      <motion.section variants={itemVariants} className="hero-panel mb-4">
        <div className="relative z-10 grid gap-8 xl:grid-cols-[1fr_auto]">
          <div className="space-y-6 max-w-2xl">
            <div className="space-y-2">
              <h2 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-graphite-950">
                构建高质量的对抗测试用例
              </h2>
              <p className="text-sm sm:text-base text-graphite-600 leading-relaxed">
                在左侧配置攻击参数并执行测试。所有的表单状态都会自动在本地持久化，您可以随时中断或恢复测试流程。
              </p>
            </div>
            <div className="inline-flex items-center gap-2 rounded-xl bg-electric-900/60 px-4 py-2 border border-electric-100/50 backdrop-blur-md shadow-sm">
              <Sparkles className="h-4 w-4 text-electric-700" />
              <span className="text-xs font-bold text-electric-800">提示：建议先从基础的 Prompt Injection 开始验证。</span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 xl:w-[480px]">
            {quickFacts.map((item) => (
              <HeroStat key={item.label} label={item.label} value={item.value} hint={item.hint} tone={item.tone} />
            ))}
          </div>
        </div>
      </motion.section>

      <div className="page-grid mt-2">
        <motion.div variants={itemVariants}>
          <AttackForm
            form={form}
            setForm={setForm}
            onSubmit={handleSubmit}
            loading={loading}
            apiConnected={apiConnected}
            templates={basicTemplates}
            onLoadTemplate={handleLoadTemplate}
            modelOptions={modelList}
          />
        </motion.div>

        <motion.div variants={itemVariants} className="space-y-6">
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
              >
                <AttackResult result={result} />
              </motion.div>
            ) : (
              <motion.div
                key="placeholder"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex h-[320px] flex-col items-center justify-center rounded-2xl border border-dashed border-white/60 bg-white/40 px-6 text-center backdrop-blur-sm transition-all duration-500 hover:bg-white/60"
              >
                <div className="mb-4 rounded-2xl bg-gradient-to-br from-white to-graphite-50 p-4 shadow-soft border border-white">
                  <TerminalSquare className="h-6 w-6 text-graphite-500" />
                </div>
                <h3 className="text-sm font-bold text-graphite-900">等待执行</h3>
                <p className="mt-2 max-w-[260px] text-xs font-medium text-graphite-500 leading-relaxed">
                  配置攻击参数并点击执行，测试结果和详细的修复建议将在此区域显示。
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          <InfoCallout
            title="测试建议"
            description="明确定义您的测试目标（Target Behavior），这有助于自动化评估引擎更准确地计算风险分数。"
            cta={
              <div className="space-y-3">
                <QuickLink label="使用预设模板" description="从右侧表单顶部的模板库中快速加载典型攻击案例。" />
                <QuickLink label="分析风险分数" description="超过 0.5 的分数表明模型可能存在策略漂移倾向。" />
              </div>
            }
            icon={Sparkles}
          />
        </motion.div>
      </div>
    </motion.div>
  )
}
