import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { BarChart3, ShieldAlert, Sparkles, TerminalSquare } from 'lucide-react'
import { AttackForm, AttackResult, DEFAULT_MODELS } from '../components/attack'
import { attackApi, getModels, isDemoModeEnabled } from '../api'
import { useLocalStorage } from '../hooks/useCommon'
import { useAttackTemplates } from '../hooks/useAttackTemplates'
import { HeroStat, InfoCallout, PageHeader, QuickLink, StatusPill } from '../components/ui/AppFrame'

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
  }, [])

  const quickFacts = useMemo(
    () => [
      { label: 'Model', value: form.model, hint: 'Changes response style and attack behavior.', tone: 'electric' },
      { label: 'Iterations', value: form.max_iterations, hint: 'Higher values usually explore deeper variants.', tone: 'warning' },
      {
        label: 'Run mode',
        value: apiConnected ? 'Live API' : isDemoModeEnabled ? 'Demo fallback' : 'Offline',
        hint: apiConnected ? 'Requests are sent to the backend.' : 'Live execution is not currently available.',
        tone: apiConnected ? 'success' : 'danger',
      },
    ],
    [apiConnected, form.max_iterations, form.model]
  )

  async function loadModels() {
    try {
      const models = await getModels()
      if (models.length > 0) {
        setModelList(models.map((model) => ({ value: model, label: model, provider: 'Auto detected' })))
      }
    } catch {
      setModelList(DEFAULT_MODELS)
    }
  }

  async function checkApiStatus() {
    try {
      await attackApi.test()
      setApiConnected(true)
    } catch {
      setApiConnected(false)
    }
  }

  async function handleSubmit(formData) {
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
        toast('Switched to demo mode because the backend is offline.', { icon: '⚠️' })
        return
      }

      const data = await attackApi.run(formData)
      setResult(data)
      toast.success('Attack run completed.')
    } catch (error) {
      const detail = error.response?.data?.detail || error.response?.data?.message || 'Request failed.'
      toast.error(detail)
      if (isDemoModeEnabled) {
        setResult(buildDemoResult(formData))
      }
    } finally {
      setLoading(false)
    }
  }

  function handleLoadTemplate(template) {
    setForm((current) => ({
      ...current,
      prompt: template.content || template.prompt || '',
      target_behavior: template.target || current.target_behavior,
    }))
    toast.success(`Loaded template: ${template.name}`)
  }

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="ATTACK LAB"
        title="Attack Testing Console"
        description="Run prompt attack scenarios, compare model behavior, and review the generated result in a single workflow."
        badge={<StatusPill online={apiConnected} onlineLabel="Live API" offlineLabel="Offline" />}
      />

      <section className="hero-panel">
        <div className="relative z-10 grid gap-4 lg:grid-cols-[1.3fr_0.9fr]">
          <div className="space-y-3">
            <span className="badge badge-neutral">Attack form state is persisted locally so you can resume quickly.</span>
            <h2 className="font-display text-3xl font-bold tracking-tight text-graphite-950">
              Treat every run like a real operator workflow, not a one-off form submit.
            </h2>
            <p className="max-w-2xl text-sm text-graphite-600 sm:text-base">
              The page keeps the model choice, prompt, target behavior, and result panel close together so we can move faster
              without losing context between retries.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            {quickFacts.map((item) => (
              <HeroStat key={item.label} label={item.label} value={item.value} hint={item.hint} tone={item.tone} />
            ))}
          </div>
        </div>
      </section>

      <div className="page-grid">
        <motion.div initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }}>
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

        <motion.div initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} className="space-y-6">
          <AttackResult result={result} />

          <InfoCallout
            title="Before you submit"
            description="Write the target behavior as an observable outcome so the result panel is easier to evaluate."
            cta={
              <div className="space-y-3">
                <QuickLink label="Start with prompt injection" description="Best for validating system-prompt hardening." />
                <QuickLink label="Retry with jailbreak" description="Useful when you want stronger role-play pressure." />
              </div>
            }
            icon={Sparkles}
          />

          <div className="card">
            <div className="mb-4 flex items-center gap-2">
              <TerminalSquare className="h-4 w-4 text-electric-600" />
              <h3 className="text-sm font-semibold text-graphite-900">Review checklist</h3>
            </div>
            <div className="space-y-3 text-sm text-graphite-600">
              <p>1. Check the risk score first, then inspect the model response, then decide whether a defense change is needed.</p>
              <p>2. If the page is in demo mode, rerun the same prompt against the live backend before treating it as a real finding.</p>
              <p>3. For high-risk prompts, save the scenario into your regression suite so future fixes stay covered.</p>
            </div>
            <div className="glass-divider my-4" />
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="badge badge-neutral">
                <ShieldAlert className="h-3.5 w-3.5" /> Attack status
              </span>
              <span className="badge badge-neutral">
                <BarChart3 className="h-3.5 w-3.5" /> Risk scoring
              </span>
              <span className="badge badge-neutral">
                <Sparkles className="h-3.5 w-3.5" /> Demo fallback
              </span>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
