import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle2, Play, Shield, Skull, Target } from 'lucide-react'
import { runRedTeam } from '../api/security'
import { MetricCard, PageHeader, PanelHeader, ProgressMeter } from '../components/ui/AppFrame'

const TECHNIQUES = [
  { id: 'prompt_injection', name: '提示词注入', description: '直接覆盖或绕过系统约束。' },
  { id: 'jailbreak', name: '越狱攻击', description: '通过角色扮演突破模型边界。' },
  { id: 'role_play', name: '角色诱导', description: '诱导模型切换高风险角色。' },
  { id: 'encoding', name: '编码绕过', description: '利用编码和混淆规避过滤器。' },
  { id: 'context_injection', name: '上下文注入', description: '通过外部上下文影响响应。' },
  { id: 'chain_of_thought', name: '推理链窃取', description: '尝试提取推理细节与内部逻辑。' },
  { id: 'privilege_escalation', name: '权限提升', description: '诱导模型执行高权限动作。' },
  { id: 'data_exfiltration', name: '数据泄露', description: '尝试获取敏感训练信息。' },
]

const DIMENSIONS = [
  { id: 'safety', label: '安全性' },
  { id: 'bias', label: '偏见性' },
  { id: 'relevance', label: '相关性' },
  { id: 'coherence', label: '连贯性' },
]

export default function RedTeamPage() {
  const [results, setResults] = useState([])
  const [running, setRunning] = useState(false)
  const [targetModel, setTargetModel] = useState('qwen3:4b')
  const [selected, setSelected] = useState(TECHNIQUES.map((item) => item.id))
  const [hybridMode, setHybridMode] = useState(true)
  const [selectedDimensions, setSelectedDimensions] = useState(['safety', 'bias'])

  const successCount = useMemo(() => results.filter((item) => item.success).length, [results])
  const successRate = useMemo(
    () => (results.length ? Math.round((successCount / results.length) * 100) : 0),
    [results.length, successCount]
  )

  const toggle = (id) => {
    setSelected((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
    )
  }

  const handleRun = async () => {
    setRunning(true)
    try {
      const data = await runRedTeam(targetModel, selected, {
        hybrid_mode: hybridMode,
        dimensions: selectedDimensions
      })
      setResults(data)
    } finally {
      setRunning(false)
    }
  }

  const toggleDimension = (id) => {
    setSelectedDimensions((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
    )
  }

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="RED TEAM"
        title="红队演练中心"
        description="按攻击技术组合进行红队压力测试，快速定位高风险能力缺口。"
      />

      <div className="grid gap-6 xl:grid-cols-[0.98fr_1.02fr]">
        <section className="card card-glow">
          <PanelHeader title="演练配置" description="选择模型与技术组合，执行一轮红队演练。" />
          <div className="space-y-5">
            <div>
              <label className="label">目标模型</label>
              <input className="input-field" value={targetModel} onChange={(event) => setTargetModel(event.target.value)} />
            </div>
            <div>
              <label className="label">攻击技术</label>
              <div className="grid gap-3 sm:grid-cols-2">
                {TECHNIQUES.map((technique) => {
                  const active = selected.includes(technique.id)
                  return (
                    <button
                      key={technique.id}
                      type="button"
                      onClick={() => toggle(technique.id)}
                      className={`relative overflow-hidden rounded-[18px] border px-4 py-3 text-left transition-all duration-300 ${
                        active
                          ? 'border-electric-300 bg-electric-50/90 shadow-sm transform scale-[1.02]'
                          : 'border-graphite-200/70 bg-white/75 hover:border-electric-200'
                      }`}
                    >
                      {active && <div className="absolute inset-0 bg-gradient-to-br from-electric-100/40 to-transparent pointer-events-none" />}
                      <p className={`relative z-10 text-sm font-semibold transition-colors ${active ? 'text-electric-900' : 'text-graphite-900'}`}>{technique.name}</p>
                      <p className={`relative z-10 mt-1 text-xs transition-colors ${active ? 'text-electric-700/80' : 'text-graphite-500'}`}>{technique.description}</p>
                    </button>
                  )
                })}
              </div>
            </div>
            
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="label">评估维度 (LLM Judge)</label>
                <div className="flex flex-wrap gap-2 mt-2">
                  {DIMENSIONS.map((dim) => (
                    <button
                      key={dim.id}
                      type="button"
                      onClick={() => toggleDimension(dim.id)}
                      className={`relative overflow-hidden rounded-full border px-4 py-1.5 text-xs font-semibold transition-all duration-300 ${
                        selectedDimensions.includes(dim.id)
                          ? 'border-electric-400 bg-gradient-to-r from-electric-500 to-electric-600 text-white shadow-md transform scale-105'
                          : 'border-graphite-200/70 bg-white text-graphite-600 hover:bg-graphite-50 hover:border-graphite-300'
                      }`}
                    >
                      {dim.label}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="label">混合裁判模式</label>
                <div className="mt-2 flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="hybrid-mode"
                    checked={hybridMode}
                    onChange={(e) => setHybridMode(e.target.checked)}
                    className="h-4 w-4 rounded border-graphite-300 text-electric-600 focus:ring-electric-600"
                  />
                  <label htmlFor="hybrid-mode" className="text-sm text-graphite-700">启用多模型混合评判 (更高准确率)</label>
                </div>
              </div>
            </div>

            <button type="button" onClick={handleRun} disabled={running || selected.length === 0} className="btn-primary w-full justify-center py-3">
              <Play className="h-4 w-4" />
              {running ? '正在执行红队演练' : '启动演练'}
            </button>
          </div>
        </section>

        <section className="card card-glow">
          <PanelHeader title="演练结果" description="关注成功率、失败场景和技术分布。" />
          {results.length ? (
            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-3">
                <MetricCard icon={Target} label="技术总数" value={results.length} hint="本轮执行项" tone="electric" />
                <MetricCard icon={Skull} label="攻击成功" value={successCount} hint={`${successRate}%`} tone="lava" />
                <MetricCard icon={Shield} label="攻击失败" value={results.length - successCount} hint={`${100 - successRate}%`} tone="neon" />
              </div>
              <ProgressMeter value={successRate} tone={successRate >= 40 ? 'warning' : 'success'} label="攻击成功率" />
              <div className="space-y-3">
                {results.map((item, index) => (
                  <motion.div key={`${item.technique}-${index}`} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="rounded-[18px] border border-graphite-200/70 bg-white/80 px-4 py-3">
                    <div className="mb-1 flex items-center justify-between">
                      <p className="text-sm font-semibold text-graphite-900">{item.technique || item.scenario}</p>
                      <span className={`badge ${item.success ? 'badge-danger' : 'badge-success'}`}>
                        {item.success ? '攻击成功' : '攻击失败'}
                      </span>
                    </div>
                    <p className="text-xs text-graphite-500">{item.scenario || '未返回场景描述'}</p>
                  </motion.div>
                ))}
              </div>
            </div>
          ) : (
            <div className="panel-muted flex min-h-[430px] flex-col items-center justify-center gap-3 text-center">
              <AlertTriangle className="h-8 w-8 text-graphite-400" />
              <p className="text-sm text-graphite-500">尚未运行红队演练，配置后即可查看结果。</p>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
