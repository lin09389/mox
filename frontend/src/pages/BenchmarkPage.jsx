import { useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import toast from 'react-hot-toast'
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Database,
  Loader2,
  Play,
  Shield,
  Target,
  TrendingUp,
  XCircle,
} from 'lucide-react'
import { benchmarkApi, isDemoModeEnabled } from '../api'
import { HubPanelIntro } from '../context/HubContext'
import { MetricCard, PanelHeader, ProgressMeter } from '../components/ui/AppFrame'
import ModelSelect from '../components/ui/ModelSelect'
import RunCompleteBanner from '../components/ui/RunCompleteBanner'
import { useTaskStore } from '../store/useTaskStore'

const DATASETS = [
  { value: 'advbench', label: 'AdvBench', desc: '对抗样本覆盖广，适合基础防线回归。', count: 150 },
  { value: 'harmbench', label: 'HarmBench', desc: '聚焦高风险内容，适合专项攻击验证。', count: 200 },
]

const MODELS = [
  { value: 'gpt-4', label: 'GPT-4', provider: 'OpenAI' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5', provider: 'OpenAI' },
  { value: 'claude-3-opus-20240229', label: 'Claude 3', provider: 'Anthropic' },
  { value: 'abab2.5-chat', label: 'MiniMax abab2.5', provider: 'MiniMax' },
  { value: 'qwen:4b', label: 'Qwen 4B', provider: 'Ollama' },
  { value: 'llama3', label: 'Llama 3', provider: 'Ollama' },
]

const ATTACK_TYPES = [
  { value: 'prompt_injection', label: '提示词注入', desc: '通过覆盖或绕过指令测试模型边界。' },
  { value: 'jailbreak', label: '越狱攻击', desc: '模拟角色扮演与边界突破攻击。' },
]

function normalizeBenchmarkResponse(data, form) {
  if (!data || data._demo_mode || data.total !== undefined) {
    return data
  }

  const total = data.total_cases ?? 0
  const success = data.successful_attacks ?? 0
  const fail = data.failed_attacks ?? Math.max(0, total - success)
  const rate = total ? Math.round((success / total) * 100) : 0
  const detailed = Array.isArray(data.detailed_results) ? data.detailed_results : []
  const avgIterations = detailed.length
    ? Math.round(detailed.reduce((sum, item) => sum + (item.iterations || 0), 0) / detailed.length)
    : 0

  return {
    dataset: DATASETS.find((item) => item.value === data.dataset)?.label || data.dataset,
    attackType: ATTACK_TYPES.find((item) => item.value === data.attack_type)?.label || data.attack_type,
    model: MODELS.find((item) => item.value === data.model)?.label || form.model,
    total,
    success,
    fail,
    successRate: `${rate}%`,
    avgIterations,
    duration: '—',
    details: [
      {
        attack: ATTACK_TYPES.find((item) => item.value === data.attack_type)?.label || data.attack_type,
        success,
        fail,
      },
    ],
    reportId: data.report_id ?? null,
    _demo_mode: false,
  }
}

function buildDemoResult(form) {
  const total = form.max_cases
  const success = Math.max(1, Math.round(total * 0.35))
  const fail = total - success
  const rate = total ? Math.round((success / total) * 100) : 0

  return {
    dataset: DATASETS.find((item) => item.value === form.dataset)?.label,
    attackType: ATTACK_TYPES.find((item) => item.value === form.attack_type)?.label,
    model: MODELS.find((item) => item.value === form.model)?.label,
    total,
    success,
    fail,
    successRate: `${rate}%`,
    avgIterations: Math.round(4 + Math.random() * 6),
    duration: `${(5 + Math.random() * 8).toFixed(1)} 秒`,
    details: ATTACK_TYPES.map((item) => ({
      attack: item.label,
      success: item.value === form.attack_type ? success : Math.round(success * 0.56),
      fail: item.value === form.attack_type ? fail : Math.max(0, total - Math.round(success * 0.56)),
    })),
    _demo_mode: true,
  }
}

import { containerVariants, itemVariants } from '../utils/animations'

export default function BenchmarkPage() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [progress, setProgress] = useState(0)
  const registerLocalTask = useTaskStore((state) => state.registerLocalTask)
  const updateLocalTask = useTaskStore((state) => state.updateLocalTask)
  const finishLocalTask = useTaskStore((state) => state.finishLocalTask)
  const removeLocalTask = useTaskStore((state) => state.removeLocalTask)

  const [form, setForm] = useState({
    dataset: 'advbench',
    attack_type: 'prompt_injection',
    model: 'gpt-4',
    max_cases: 20,
  })

  const metrics = useMemo(() => {
    if (!result) return null
    return [
      { icon: Database, label: '总测试样本数', value: result.total, hint: `数据集: ${result.dataset}` },
      { icon: AlertTriangle, label: '攻击成功', value: result.success, hint: `穿透率 ${result.successRate}` },
      { icon: CheckCircle2, label: '防御拦截', value: result.fail, hint: '防线依然稳固' },
      { icon: TrendingUp, label: '平均迭代次', value: result.avgIterations, hint: `测试耗时 ${result.duration}` },
    ]
  }, [result])

  const handleRun = async () => {
    setLoading(true)
    setProgress(0)
    setResult(null)

    const localTaskId = `bench-${Date.now().toString(36)}`
    registerLocalTask({
      id: localTaskId,
      name: `基准评测 (${form.model})`,
      source: 'benchmark',
    })

    const ticks = [15, 35, 55, 75, 92]
    let index = 0
    const timer = window.setInterval(() => {
      if (index < ticks.length) {
        const next = ticks[index]
        setProgress(next)
        updateLocalTask(localTaskId, { progress: next })
        index += 1
      }
    }, 360)

    try {
      const data = await benchmarkApi.run(form)
      const normalized = normalizeBenchmarkResponse(data, form)
      setProgress(100)
      setResult(normalized)
      finishLocalTask(localTaskId, {
        progress: 100,
        status: 'completed',
        report_id: normalized?.reportId ?? null,
      })
      toast.success(normalized?.reportId ? '基准评测已完成，报告已入库。' : '基准评测已完成。')
    } catch {
      window.clearInterval(timer)
      if (!isDemoModeEnabled) {
        removeLocalTask(localTaskId)
        setLoading(false)
        toast.error('基准评测失败，请检查后端连接。')
        return
      }
      setTimeout(() => {
        setProgress(100)
        setResult(buildDemoResult(form))
        finishLocalTask(localTaskId, { progress: 100, status: 'completed' })
        setLoading(false)
        toast('后端不可用，已展示演示评测结果。', { icon: '⚠️' })
      }, 1800)
      return
    }
    window.clearInterval(timer)
    setLoading(false)
  }

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="page-shell">
      <HubPanelIntro description="使用标准数据集对目标模型执行自动化对抗评测与打分。" />

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <motion.section variants={itemVariants} className="card p-6 h-fit lg:sticky lg:top-6">
          <PanelHeader title="评测基准配置" description="组装评测矩阵 (数据集 × 攻击类型 × 目标模型)。" />
          <div className="space-y-6">
            <div className="space-y-3">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">选择数据集</label>
              <div className="grid gap-3 sm:grid-cols-2">
                {DATASETS.map((dataset) => {
                  const active = form.dataset === dataset.value
                  return (
                    <button
                      key={dataset.value}
                      type="button"
                      onClick={() => setForm((current) => ({ ...current, dataset: dataset.value }))}
                      className={`rounded-xl border p-4 text-left transition-all duration-300 ${
                        active
                          ? 'border-cyan-500/50 bg-cyan-500/10 shadow-[inset_0_0_15px_rgba(6,182,212,0.1)] transform scale-[1.02]'
                          : 'border-[var(--border-glass)] bg-[var(--bg-glass)] hover:bg-[var(--bg-glass-strong)] hover:border-cyan-500/30'
                      }`}
                    >
                      <p className={`text-sm font-bold font-display mb-1 ${active ? 'text-cyan-500' : 'text-[var(--text-main)]'}`}>{dataset.label}</p>
                      <p className={`text-xs font-medium mb-3 ${active ? 'text-cyan-500/70' : 'text-[var(--text-muted)]'}`}>{dataset.desc}</p>
                      <p className="text-[10px] font-bold uppercase tracking-widest bg-[var(--bg-main)]/50 px-2 py-1 rounded inline-block text-[var(--text-muted)]">样本量 {dataset.count}</p>
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">攻击类型</label>
                <select
                  className="input-field appearance-none bg-no-repeat bg-[right_0.5rem_center] bg-[length:1.5em_1.5em]"
                  value={form.attack_type}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, attack_type: event.target.value }))
                  }
                >
                  {ATTACK_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">目标模型</label>
                <ModelSelect
                  value={form.model}
                  onChange={(model) => setForm((current) => ({ ...current, model }))}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">最大测试样本数 (打分切片)</label>
              <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-4">
                <div className="mb-4 flex items-center justify-between">
                  <span className="text-sm font-medium text-[var(--text-muted)]">当前截取限制</span>
                  <strong className="text-cyan-500 font-mono text-lg">{form.max_cases} <span className="text-[10px] uppercase text-[var(--text-muted)]">Samples</span></strong>
                </div>
                <input
                  type="range"
                  min={5}
                  max={100}
                  value={form.max_cases}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, max_cases: Number.parseInt(event.target.value, 10) }))
                  }
                  className="w-full h-1.5 rounded-lg bg-[var(--bg-glass-strong)] appearance-none cursor-pointer accent-cyan-500"
                />
              </div>
            </div>

            <button type="button" onClick={handleRun} disabled={loading} className="btn-primary w-full justify-center py-3 bg-cyan-500 hover:bg-cyan-600 border-cyan-500 text-white shadow-[0_0_20px_rgba(6,182,212,0.3)] text-base font-bold disabled:opacity-50 disabled:shadow-none">
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  矩阵执行中 ({progress}%)
                </>
              ) : (
                <>
                  <Play className="h-5 w-5" />
                  运行基准评测
                </>
              )}
            </button>
          </div>
        </motion.section>

        <motion.section variants={itemVariants} className="card p-6 bg-[var(--bg-glass-strong)] border-[var(--border-glass)] shadow-[inset_0_0_40px_rgba(6,182,212,0.02)]">
          <PanelHeader title="评测报告摘要" description="攻防对抗结果与安全评估指标反馈。" />

          <AnimatePresence mode="wait">
            {loading ? (
              <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6 pt-4">
                <div className="p-5 rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)]">
                   <ProgressMeter value={progress} tone="electric" label="引擎评测进度" />
                </div>
                <div className="flex min-h-[300px] flex-col items-center justify-center gap-4 text-center opacity-60">
                  <div className="w-16 h-16 border-4 border-[var(--border-glass)] border-t-cyan-500 rounded-full animate-spin"></div>
                  <p className="text-sm font-bold text-[var(--text-muted)]">正在进行对抗推演分析...</p>
                </div>
              </motion.div>
            ) : result ? (
              <motion.div key="result" initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -15 }} className="space-y-6">
                {result._demo_mode ? (
                  <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-3 flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                    <span className="text-xs font-bold text-amber-500 tracking-wide">演示模式：本地环境评估展示</span>
                  </div>
                ) : null}
                <RunCompleteBanner reportId={result.reportId} title="评测报告已保存" />
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-4 flex flex-col justify-center">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)] mb-1">测试数据集</p>
                    <p className="text-base font-bold font-display text-[var(--text-main)]">{result.dataset || result['数据集']}</p>
                  </div>
                  <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-4 flex flex-col justify-center">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)] mb-1">渗透攻击类型</p>
                    <p className="text-base font-bold font-display text-[var(--text-main)]">{result.attackType || result['攻击类型']}</p>
                  </div>
                </div>

                {metrics ? (
                  <div className="grid gap-4 sm:grid-cols-2">
                    {metrics.map((metric, index) => (
                      <MetricCard
                        key={metric.label}
                        icon={metric.icon}
                        label={metric.label}
                        value={metric.value}
                        hint={metric.hint}
                        tone={index === 1 ? 'lava' : index === 2 ? 'neon' : 'electric'}
                      />
                    ))}
                  </div>
                ) : null}

                {(result.details || result['详细结果']) ? (
                  <div className="space-y-4 pt-2">
                    <h4 className="text-sm font-bold font-display text-[var(--text-main)] border-b border-[var(--border-glass)] pb-2 flex items-center gap-2"><Target className="h-4 w-4 text-rose-500" /> 细分维度详情</h4>
                    {(result.details || result['详细结果']).map((entry) => {
                      const successCount = (entry.success || entry['成功数'] || 0)
                      const failCount = (entry.fail || entry['失败数'] || 0)
                      const rate = Math.round((successCount / Math.max(1, successCount + failCount)) * 100)
                      return (
                        <div key={entry.attack || entry['攻击方式']} className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-5 transition-transform hover:-translate-y-0.5">
                          <div className="mb-4 flex items-center justify-between">
                            <p className="text-sm font-bold text-[var(--text-main)] font-mono">{entry.attack || entry['攻击方式']}</p>
                            <span className="badge border font-mono tracking-wide bg-[var(--bg-glass-strong)] border-[var(--border-glass)]">
                              <span className="text-rose-500">攻击 {successCount}</span>
                              <span className="text-[var(--text-muted)] px-1">/</span>
                              <span className="text-emerald-500">防御 {failCount}</span>
                            </span>
                          </div>
                          <ProgressMeter value={rate} tone={rate > 50 ? 'danger' : 'warning'} label="该策略攻击成功率" />
                        </div>
                      )
                    })}
                  </div>
                ) : null}
              </motion.div>
            ) : (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex min-h-[400px] flex-col items-center justify-center gap-4 text-center p-8">
                <div className="w-20 h-20 rounded-full bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] flex items-center justify-center">
                   <BarChart3 className="h-10 w-10 text-[var(--text-muted)] opacity-60" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[var(--text-main)]">暂无评测数据</h3>
                  <p className="mt-2 text-sm font-medium text-[var(--text-muted)] max-w-sm">在左侧配置完成后运行基准评测，平台将为您输出完整的攻防比对结论。</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.section>
      </div>
    </motion.div>
  )
}
