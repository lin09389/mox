import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { BarChart3, ChevronDown, ChevronUp, ShieldAlert, Sparkles, TerminalSquare, AlertTriangle } from 'lucide-react'
import { AttackForm, AttackResult, AttackPageShell, AttackPanelIntro, AttackLabHero } from '../components/attack'
import { isDemoModeEnabled } from '../api'
import { useApiStatus } from '../hooks/useApiStatus'
import { useLocalStorage } from '../hooks/useCommon'
import { useAttackTemplatesQuery, useModels, useRunAttack } from '../hooks/queries'
import { InfoCallout, QuickLink, StatusPill } from '../components/ui/AppFrame'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

// Fallback logic for demo
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

const attackSchema = z.object({
  attack_type: z.string().min(1, '请选择攻击类型'),
  model: z.string().min(1, '请选择目标模型'),
  max_iterations: z.number().min(1).max(100),
  prompt: z.string().min(5, '提示词至少需要 5 个字符'),
  target_behavior: z.string().min(5, '目标行为描述至少需要 5 个字符'),
})

import { itemVariants } from '../utils/animations'

export default function AttackPage() {
  const [result, setResult] = useState(null)
  const [heroOpen, setHeroOpen] = useState(false)
  
  // React Query Hooks
  const { data: modelsData } = useModels()
  const { data: templatesData } = useAttackTemplatesQuery()
  const attackMutation = useRunAttack()

  const [savedForm, setSavedForm] = useLocalStorage('attack_form', {
    attack_type: 'prompt_injection',
    model: 'gpt-4',
    prompt: '',
    target_behavior: '',
    max_iterations: 10,
  })

  const form = useForm({
    resolver: zodResolver(attackSchema),
    defaultValues: savedForm,
  })

  const watchAllFields = form.watch()

  useEffect(() => {
    // Sync local storage on form change
    const subscription = form.watch((value) => {
      setSavedForm(value)
    })
    return () => subscription.unsubscribe()
  }, [form.watch, setSavedForm])

  const basicTemplates = useMemo(() => {
    return templatesData?.filter(t => t.category === 'basic') || []
  }, [templatesData])

  const modelOptions = useMemo(() => {
    return modelsData?.map(m => ({ value: m, label: m, provider: 'Auto detected' })) || [
      { value: 'gpt-4', label: 'gpt-4', provider: 'Auto detected' },
      { value: 'claude-3', label: 'claude-3', provider: 'Auto detected' }
    ]
  }, [modelsData])

  const { isConnected: apiConnected } = useApiStatus()

  const quickFacts = useMemo(
    () => [
      { label: '目标模型', value: watchAllFields.model || '-', hint: '模型的选择将直接影响攻击链路与结果', tone: 'electric' },
      { label: '迭代深度', value: watchAllFields.max_iterations || 10, hint: '更深的迭代可能发掘隐藏的漏洞', tone: 'warning' },
      {
        label: '运行模式',
        value: apiConnected ? 'Live API' : isDemoModeEnabled ? 'Demo Fallback' : 'Offline',
        hint: apiConnected ? '请求直达安全测试后端引擎' : '当前API离线，正使用本地演示数据',
        tone: apiConnected ? 'success' : 'danger',
      },
    ],
    [apiConnected, watchAllFields.max_iterations, watchAllFields.model]
  )

  const onSubmit = async (formData) => {
    setResult(null)
    try {
      if (!apiConnected && isDemoModeEnabled) {
        await new Promise((resolve) => window.setTimeout(resolve, 900))
        setResult(buildDemoResult(formData))
        toast('Switched to demo mode because the backend is offline.', { icon: '⚠️' })
        return
      }
      
      const data = await attackMutation.mutateAsync(formData)
      setResult(data)
      toast.success('Attack run completed.')
    } catch (error) {
      const detail = error.response?.data?.detail || error.response?.data?.message || 'Request failed.'
      toast.error(detail)
      if (isDemoModeEnabled) {
        setResult(buildDemoResult(formData))
      }
    }
  }

  function handleLoadTemplate(template) {
    form.setValue('prompt', template.content || template.prompt || '', { shouldValidate: true })
    form.setValue('target_behavior', template.target || watchAllFields.target_behavior, { shouldValidate: true })
    toast.success(`Loaded template: ${template.name}`)
  }

  return (
    <AttackPageShell>
      <AttackPanelIntro
        description="执行自动化对抗攻击场景，在同一工作台内配置、运行并分析测试结果。"
        badge={<StatusPill online={apiConnected} onlineLabel="Live API 正常" offlineLabel="演示模式运行中" />}
      />

      <motion.div variants={itemVariants}>
        <button
          type="button"
          className="ws-lab-hero hero-panel mb-4 flex w-full items-center justify-between gap-3 text-left lg:hidden"
          onClick={() => setHeroOpen((open) => !open)}
          aria-expanded={heroOpen}
        >
          <div className="relative z-10 min-w-0">
            <p className="text-xs font-bold uppercase tracking-widest text-cyan-500">攻击实验室</p>
            <p className="mt-1 truncate text-sm font-bold text-[var(--text-main)]">
              {watchAllFields.model || '未选模型'} · {watchAllFields.max_iterations || 10} 轮迭代
            </p>
          </div>
          {heroOpen ? (
            <ChevronUp className="relative z-10 h-5 w-5 shrink-0 text-[var(--text-muted)]" />
          ) : (
            <ChevronDown className="relative z-10 h-5 w-5 shrink-0 text-[var(--text-muted)]" />
          )}
        </button>

        <div className={heroOpen ? 'block lg:hidden mb-4' : 'hidden'}>
          <AttackLabHero
            eyebrow="攻击实验室"
            title="将每次测试视为真实的网络攻防演练。"
            subtitle="状态已自动保存至本地缓存，可随时继续上次配置。"
            stats={quickFacts.map((item) => ({
              label: item.label,
              value: item.value,
              hint: item.hint,
              tone: item.tone,
            }))}
          />
        </div>

        <div className="hidden lg:block mb-4">
          <AttackLabHero
            eyebrow="攻击实验室"
            title="将每次测试视为真实的网络攻防演练，而不仅仅是提交一次表单。"
            subtitle="实验室面板紧凑整合了模型选取、提示词构造、目标预期和测试结果，实现高效攻防迭代。"
            stats={quickFacts.map((item) => ({
              label: item.label,
              value: item.value,
              hint: item.hint,
              tone: item.tone,
            }))}
          />
        </div>
      </motion.div>

      <div className="page-grid">
        <motion.div variants={itemVariants}>
          <div className="card p-6 shadow-soft h-full">
            <AttackForm
              form={form}
              onSubmit={form.handleSubmit(onSubmit)}
              loading={attackMutation.isPending}
              apiConnected={apiConnected}
              templates={basicTemplates}
              onLoadTemplate={handleLoadTemplate}
              modelOptions={modelOptions}
            />
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="space-y-6">
          <div className="card p-6 shadow-soft min-h-[300px]">
            <AttackResult result={result} />
          </div>

          <InfoCallout
            title="测试建议"
            description="建议将目标行为描述为一个清晰可观测的后果，这样当系统输出结果时，能够更直观地判断防线是否被突破。"
            cta={
              <div className="space-y-3 mt-4">
                <QuickLink label="使用提示词注入 (Prompt Injection)" description="最适合用于验证系统 Prompt 硬化程度的基础攻击方法。" />
                <QuickLink label="使用越狱攻击 (Jailbreak)" description="当你希望通过复杂的角色扮演绕过安全限制时使用。" />
              </div>
            }
            icon={AlertTriangle}
            tone="warning"
          />

          <div className="card p-6 shadow-fine">
            <div className="mb-5 flex items-center gap-3 border-b border-[var(--border-glass)] pb-4">
              <div className="p-2 bg-cyan-500/10 rounded-lg">
                <TerminalSquare className="h-5 w-5 text-cyan-500" />
              </div>
              <h3 className="text-base font-bold font-display text-[var(--text-main)]">攻击审查清单</h3>
            </div>
            <div className="space-y-4 text-sm font-medium text-[var(--text-muted)]">
              <div className="flex gap-3">
                <span className="text-cyan-500 font-bold">01.</span>
                <p>优先查看风险评分，随后深入审查模型的具体响应文本，再决定是否调整底层安全防御策略。</p>
              </div>
              <div className="flex gap-3">
                <span className="text-cyan-500 font-bold">02.</span>
                <p>如果在演示模式下测试成功，务必在 Live API 恢复后对同一指令进行真实回归测试。</p>
              </div>
              <div className="flex gap-3">
                <span className="text-cyan-500 font-bold">03.</span>
                <p>对于能造成高危影响的提示词，请将其添加到回归测试用例集中，确保未来的版本补丁不会遗漏此漏洞。</p>
              </div>
            </div>
            <div className="glass-divider my-5" />
            <div className="flex flex-wrap gap-3">
              <span className="badge badge-neutral bg-[var(--bg-glass-strong)] border-[var(--border-glass-strong)]">
                <ShieldAlert className="h-3.5 w-3.5" /> 测试状态
              </span>
              <span className="badge badge-neutral bg-[var(--bg-glass-strong)] border-[var(--border-glass-strong)]">
                <BarChart3 className="h-3.5 w-3.5" /> 风险标定
              </span>
              <span className="badge badge-neutral bg-[var(--bg-glass-strong)] border-[var(--border-glass-strong)]">
                <Sparkles className="h-3.5 w-3.5" /> 演示回退
              </span>
            </div>
          </div>
        </motion.div>
      </div>
    </AttackPageShell>
  )
}
