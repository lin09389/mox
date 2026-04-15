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
import { benchmarkApi } from '../api'
import { MetricCard, PageHeader, PanelHeader, ProgressMeter } from '../components/ui/AppFrame'

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

export default function BenchmarkPage() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [progress, setProgress] = useState(0)
  const [form, setForm] = useState({
    dataset: 'advbench',
    attack_type: 'prompt_injection',
    model: 'gpt-4',
    max_cases: 20,
  })

  const metrics = useMemo(() => {
    if (!result) return null
    return [
      { icon: Database, label: '总样本数', value: result.total, hint: `数据集 ${result.dataset}` },
      { icon: AlertTriangle, label: '攻击成功', value: result.success, hint: `成功率 ${result.successRate}` },
      { icon: CheckCircle2, label: '攻击失败', value: result.fail, hint: '防线拦截有效样本' },
      { icon: TrendingUp, label: '平均迭代', value: result.avgIterations, hint: `耗时 ${result.duration}` },
    ]
  }, [result])

  const handleRun = async () => {
    setLoading(true)
    setProgress(0)
    setResult(null)

    const ticks = [15, 35, 55, 75, 92]
    let index = 0
    const timer = window.setInterval(() => {
      if (index < ticks.length) {
        setProgress(ticks[index])
        index += 1
      }
    }, 360)

    try {
      const data = await benchmarkApi.run(form)
      setProgress(100)
      setResult(data)
      toast.success('基准评测已完成。')
    } catch {
      setProgress(100)
      setResult(buildDemoResult(form))
      toast('后端不可用，已展示演示评测结果。', { icon: '⚠️' })
    } finally {
      window.clearInterval(timer)
      setLoading(false)
    }
  }

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="BENCHMARK LAB"
        title="基准评测中心"
        description="在同一监控台中完成数据集选择、攻击类型配置和结果比对，避免分散式评测。"
      />

      <div className="grid gap-6 xl:grid-cols-[1.02fr_0.98fr]">
        <section className="card card-glow">
          <PanelHeader title="评测配置" description="选择数据集、目标模型和攻击策略后，一键运行。" />
          <div className="space-y-5">
            <div>
              <label className="label">数据集</label>
              <div className="grid gap-3 sm:grid-cols-2">
                {DATASETS.map((dataset) => {
                  const active = form.dataset === dataset.value
                  return (
                    <button
                      key={dataset.value}
                      type="button"
                      onClick={() => setForm((current) => ({ ...current, dataset: dataset.value }))}
                      className={`rounded-[18px] border px-4 py-4 text-left transition-all ${
                        active
                          ? 'border-electric-200 bg-electric-900/75'
                          : 'border-graphite-200/70 bg-white/75'
                      }`}
                    >
                      <p className="text-sm font-semibold text-graphite-900">{dataset.label}</p>
                      <p className="mt-1 text-xs text-graphite-500">{dataset.desc}</p>
                      <p className="mt-2 text-xs text-graphite-600">样本量 {dataset.count}</p>
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="label">攻击类型</label>
                <select
                  className="select-field"
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
              <div>
                <label className="label">目标模型</label>
                <select
                  className="select-field"
                  value={form.model}
                  onChange={(event) => setForm((current) => ({ ...current, model: event.target.value }))}
                >
                  {MODELS.map((model) => (
                    <option key={model.value} value={model.value}>
                      {model.label} · {model.provider}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="label">样本上限</label>
              <div className="rounded-[18px] border border-graphite-200/70 bg-white/80 px-4 py-4">
                <div className="mb-2 flex items-center justify-between text-sm text-graphite-600">
                  <span>最大测试样本数</span>
                  <strong className="text-electric-700">{form.max_cases}</strong>
                </div>
                <input
                  type="range"
                  min={5}
                  max={100}
                  value={form.max_cases}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, max_cases: Number.parseInt(event.target.value, 10) }))
                  }
                  className="w-full accent-electric-500"
                />
              </div>
            </div>

            <button type="button" onClick={handleRun} disabled={loading} className="btn-primary w-full justify-center py-3">
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  正在执行评测
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  运行基准评测
                </>
              )}
            </button>
          </div>
        </section>

        <section className="card card-glow">
          <PanelHeader title="评测结果" description="展示本次测试的攻防结果和关键指标。" />

          <AnimatePresence mode="wait">
            {loading ? (
              <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
                <ProgressMeter value={progress} tone="electric" label="评测进度" />
                <div className="panel-muted flex min-h-[280px] items-center justify-center">
                  <Loader2 className="h-7 w-7 animate-spin text-electric-700" />
                </div>
              </motion.div>
            ) : result ? (
              <motion.div key="result" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                {result._demo_mode ? (
                  <div className="badge badge-warning px-3 py-2">当前为演示结果</div>
                ) : null}
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-[18px] border border-graphite-200/70 bg-white/80 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-graphite-600">数据集</p>
                    <p className="mt-2 text-lg font-semibold text-graphite-900">{result.dataset || result['数据集']}</p>
                  </div>
                  <div className="rounded-[18px] border border-graphite-200/70 bg-white/80 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-graphite-600">攻击类型</p>
                    <p className="mt-2 text-lg font-semibold text-graphite-900">{result.attackType || result['攻击类型']}</p>
                  </div>
                </div>

                {metrics ? (
                  <div className="grid gap-3 sm:grid-cols-2">
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
                  <div className="space-y-3">
                    {(result.details || result['详细结果']).map((entry) => (
                      <div key={entry.attack || entry['攻击方式']} className="rounded-[18px] border border-graphite-200/70 bg-white/80 p-4">
                        <div className="mb-2 flex items-center justify-between">
                          <p className="text-sm font-semibold text-graphite-900">{entry.attack || entry['攻击方式']}</p>
                          <span className="badge badge-neutral">
                            成功 {(entry.success || entry['成功数'] || 0)} / 失败 {(entry.fail || entry['失败数'] || 0)}
                          </span>
                        </div>
                        <ProgressMeter
                          value={Math.round(
                            ((entry.success || entry['成功数'] || 0) /
                              Math.max(1, (entry.success || entry['成功数'] || 0) + (entry.fail || entry['失败数'] || 0))) * 100
                          )}
                          tone="danger"
                        />
                      </div>
                    ))}
                  </div>
                ) : null}
              </motion.div>
            ) : (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="panel-muted flex min-h-[340px] flex-col items-center justify-center gap-3 text-center">
                <BarChart3 className="h-8 w-8 text-graphite-600" />
                <p className="text-sm text-graphite-500">运行评测后，这里会显示完整结果。</p>
              </motion.div>
            )}
          </AnimatePresence>
        </section>
      </div>
    </div>
  )
}
