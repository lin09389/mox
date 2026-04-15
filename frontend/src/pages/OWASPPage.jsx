import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle2, Play, Shield, ShieldAlert } from 'lucide-react'
import { runOWASPTests } from '../api/security'
import { MetricCard, PageHeader, PanelHeader, ProgressMeter } from '../components/ui/AppFrame'

const CATEGORIES = [
  { id: 'LLM01', name: '提示词注入', description: '通过恶意输入绕过系统策略。', severity: 'critical' },
  { id: 'LLM02', name: '敏感信息泄露', description: '模型泄露不应暴露的数据。', severity: 'critical' },
  { id: 'LLM03', name: '供应链风险', description: '第三方模型或插件引入风险。', severity: 'high' },
  { id: 'LLM04', name: '数据投毒', description: '恶意数据影响模型行为。', severity: 'high' },
  { id: 'LLM05', name: '输出处理不当', description: '未对模型输出进行安全校验。', severity: 'medium' },
  { id: 'LLM06', name: '系统提示泄露', description: '内部规则被推断或直接暴露。', severity: 'high' },
  { id: 'LLM07', name: '插件不安全', description: '插件边界过弱导致能力滥用。', severity: 'critical' },
  { id: 'LLM08', name: '过度授权', description: '模型执行权限超出必要范围。', severity: 'critical' },
  { id: 'LLM09', name: '过度依赖', description: '业务盲信输出导致决策失真。', severity: 'medium' },
  { id: 'LLM10', name: '向量与检索弱点', description: 'RAG 上下文被注入污染。', severity: 'high' },
]

const severityBadge = {
  critical: 'badge-danger',
  high: 'badge-warning',
  medium: 'badge-neutral',
}

export default function OWASPPage() {
  const [results, setResults] = useState([])
  const [running, setRunning] = useState(false)
  const [model, setModel] = useState('qwen3:4b')

  const passCount = useMemo(() => results.filter((item) => item.passed).length, [results])
  const passRate = useMemo(
    () => (results.length ? Math.round((passCount / results.length) * 100) : 0),
    [passCount, results.length]
  )

  const handleRun = async () => {
    setRunning(true)
    try {
      const data = await runOWASPTests(model)
      setResults(data)
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="OWASP SUITE"
        title="OWASP LLM Top 10 专项测试"
        description="使用标准化类目快速判断模型在关键风险域的通过率，结果可直接用于治理复盘。"
      />

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <section className="card card-glow">
          <PanelHeader title="测试配置" description="选择目标模型并运行完整套件。" />
          <div className="space-y-5">
            <div>
              <label className="label">目标模型</label>
              <input value={model} onChange={(event) => setModel(event.target.value)} className="input-field" />
            </div>
            <button type="button" onClick={handleRun} disabled={running} className="btn-primary w-full justify-center py-3">
              <Play className="h-4 w-4" />
              {running ? '正在执行 OWASP 套件' : '运行 OWASP 测试'}
            </button>
            <div className="space-y-3">
              {CATEGORIES.map((category) => (
                <div key={category.id} className="rounded-[18px] border border-graphite-200/70 bg-white/80 px-4 py-3">
                  <div className="mb-1 flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-graphite-900">{category.id} · {category.name}</p>
                    <span className={`badge ${severityBadge[category.severity]}`}>{category.severity.toUpperCase()}</span>
                  </div>
                  <p className="text-xs text-graphite-500">{category.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="card card-glow">
          <PanelHeader title="测试结果" description="通过率、失败项和风险说明统一呈现。" />
          {results.length > 0 ? (
            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-3">
                <MetricCard icon={Shield} label="总测试项" value={results.length} hint="OWASP Top 10" tone="electric" />
                <MetricCard icon={CheckCircle2} label="通过项" value={passCount} hint={`${passRate}%`} tone="neon" />
                <MetricCard icon={AlertTriangle} label="失败项" value={results.length - passCount} hint={`${100 - passRate}%`} tone="lava" />
              </div>
              <ProgressMeter value={passRate} tone={passRate >= 70 ? 'success' : 'warning'} label="总体通过率" />
              <div className="space-y-3">
                {results.map((result, index) => {
                  const ref = CATEGORIES.find((item) => item.id === result.category)
                  return (
                    <motion.div key={`${result.category}-${index}`} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="rounded-[18px] border border-graphite-200/70 bg-white/80 px-4 py-3">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-semibold text-graphite-900">{result.category} · {ref?.name || result.test}</p>
                        <span className={`badge ${result.passed ? 'badge-success' : 'badge-danger'}`}>
                          {result.passed ? '通过' : '失败'}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-graphite-500">{result.test}</p>
                    </motion.div>
                  )
                })}
              </div>
            </div>
          ) : (
            <div className="panel-muted flex min-h-[420px] flex-col items-center justify-center gap-3 text-center">
              <ShieldAlert className="h-8 w-8 text-graphite-600" />
              <p className="text-sm text-graphite-500">尚未运行测试，请先选择模型并启动 OWASP 套件。</p>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
