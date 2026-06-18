import { useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, CheckCircle2, Play, Shield, Skull, Target, Loader2 } from 'lucide-react'
import { runRedTeam } from '../api/security'
import { useLocalStorage } from '../hooks/useLocalStorage'
import { MetricCard, PageHeader, PanelHeader, ProgressMeter } from '../components/ui/AppFrame'
import { PingButton } from '../components/ui/PingButton'

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

import { containerVariants, itemVariants } from '../utils/animations'

export default function RedTeamPage() {
  const [results, setResults] = useState([])
  const [running, setRunning] = useState(false)
  const [targetModel, setTargetModel] = useLocalStorage('mox_redteam_model', 'qwen3:4b')
  const [selected, setSelected] = useLocalStorage('mox_redteam_techniques', TECHNIQUES.map((item) => item.id))
  const [hybridMode, setHybridMode] = useLocalStorage('mox_redteam_hybrid', true)
  const [selectedDimensions, setSelectedDimensions] = useLocalStorage('mox_redteam_dimensions', ['safety', 'bias'])

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
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="page-shell">
      <motion.div variants={itemVariants}>
        <PageHeader
          eyebrow="RED TEAM"
          title="红队演练中心"
          description="按攻击技术组合进行红队压力测试，快速定位高风险能力缺口。"
        />
      </motion.div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <motion.section variants={itemVariants} className="card p-6 h-fit sticky top-6">
          <PanelHeader title="演练配置" description="选择模型与技术组合，执行一轮红队演练。" />
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest block mb-2">目标模型</label>
              <div className="flex items-center gap-2">
                <input className="input-field font-mono flex-1" value={targetModel} onChange={(event) => setTargetModel(event.target.value)} />
                <PingButton targetModel={targetModel} />
              </div>
            </div>
            
            <div className="space-y-3">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest flex justify-between">
                <span>攻击技术向量</span>
                <span className="text-cyan-500">{selected.length} / {TECHNIQUES.length} 已选</span>
              </label>
              <div className="grid gap-3 sm:grid-cols-2">
                {TECHNIQUES.map((technique) => {
                  const active = selected.includes(technique.id)
                  return (
                    <button
                      key={technique.id}
                      type="button"
                      onClick={() => toggle(technique.id)}
                      className={`relative overflow-hidden rounded-xl border p-3 text-left transition-all duration-300 ${
                        active
                          ? 'border-cyan-500/50 bg-cyan-500/10 shadow-[inset_0_0_15px_rgba(6,182,212,0.1)] transform scale-[1.02]'
                          : 'border-[var(--border-glass)] bg-[var(--bg-glass)] hover:bg-[var(--bg-glass-strong)] hover:border-cyan-500/30'
                      }`}
                    >
                      <p className={`relative z-10 text-sm font-bold font-display transition-colors mb-1 ${active ? 'text-cyan-500' : 'text-[var(--text-main)]'}`}>{technique.name}</p>
                      <p className={`relative z-10 text-xs font-medium transition-colors ${active ? 'text-cyan-500/70' : 'text-[var(--text-muted)]'}`}>{technique.description}</p>
                    </button>
                  )
                })}
              </div>
            </div>
            
            <div className="grid gap-5 sm:grid-cols-2 p-4 rounded-xl border border-[var(--border-glass)] bg-[var(--bg-glass-strong)]">
              <div>
                <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">评估维度 (LLM Judge)</label>
                <div className="flex flex-wrap gap-2 mt-3">
                  {DIMENSIONS.map((dim) => {
                    const active = selectedDimensions.includes(dim.id)
                    return (
                      <button
                        key={dim.id}
                        type="button"
                        onClick={() => toggleDimension(dim.id)}
                        className={`relative overflow-hidden rounded-lg border px-3 py-1.5 text-xs font-bold transition-all duration-200 ${
                          active
                            ? 'border-emerald-500 bg-emerald-500/10 text-emerald-500 shadow-sm'
                            : 'border-[var(--border-glass-strong)] bg-transparent text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-glass)]'
                        }`}
                      >
                        {dim.label}
                      </button>
                    )
                  })}
                </div>
              </div>
              <div className="flex flex-col justify-center">
                <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">混合裁判模式</label>
                <div className="mt-3 flex items-center gap-3">
                  <div className={`relative inline-flex h-5 w-9 cursor-pointer items-center rounded-full transition-colors ${hybridMode ? 'bg-cyan-500' : 'bg-[var(--border-glass-strong)]'}`} onClick={() => setHybridMode(!hybridMode)}>
                    <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${hybridMode ? 'translate-x-4.5' : 'translate-x-1'}`} />
                  </div>
                  <span className="text-xs font-bold text-[var(--text-main)]">启用多模型评判</span>
                </div>
              </div>
            </div>

            <button 
              type="button" 
              onClick={handleRun} 
              disabled={running || selected.length === 0} 
              className="btn-primary w-full justify-center py-3 bg-cyan-500 hover:bg-cyan-600 border-cyan-500 text-white shadow-[0_0_20px_rgba(6,182,212,0.3)] text-base font-bold disabled:opacity-50 disabled:shadow-none"
            >
              {running ? <Loader2 className="h-5 w-5 animate-spin" /> : <Play className="h-5 w-5" />}
              {running ? '正在执行红队演练...' : '启动演练'}
            </button>
          </div>
        </motion.section>

        <motion.section variants={itemVariants} className="card p-6 bg-gradient-to-br from-[var(--bg-glass-strong)] to-[var(--bg-glass)] border-[var(--border-glass)]">
          <PanelHeader title="演练结果" description="关注成功率、失败场景和技术分布。" />
          
          <AnimatePresence mode="wait">
            {results.length ? (
              <motion.div 
                key="results"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="space-y-6"
              >
                <div className="grid gap-4 sm:grid-cols-3">
                  <MetricCard icon={Target} label="技术总数" value={results.length} hint="本轮执行项" tone="electric" />
                  <MetricCard icon={Skull} label="攻击成功" value={successCount} hint={`${successRate}%`} tone="lava" />
                  <MetricCard icon={Shield} label="攻击失败" value={results.length - successCount} hint={`${100 - successRate}%`} tone="neon" />
                </div>
                
                <div className="p-5 rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)]">
                  <ProgressMeter value={successRate} tone={successRate >= 40 ? 'warning' : 'success'} label="攻击成功率 (渗透率)" />
                </div>
                
                <div className="space-y-3 pt-2">
                  <h4 className="text-sm font-bold font-display text-[var(--text-main)] mb-4 flex items-center gap-2"><Target className="h-4 w-4 text-rose-500" /> 渗透链路追踪</h4>
                  {results.map((item, index) => (
                    <motion.div 
                      key={`${item.technique}-${index}`} 
                      initial={{ opacity: 0, y: 10 }} 
                      animate={{ opacity: 1, y: 0 }} 
                      transition={{ delay: index * 0.05 }}
                      className={`rounded-xl border p-4 transition-all ${item.success ? 'bg-rose-500/5 border-rose-500/20 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-rose-500/10' : 'bg-[var(--bg-glass)] border-[var(--border-glass)] opacity-80'}`}
                    >
                      <div className="mb-2 flex items-center justify-between">
                        <p className={`text-sm font-bold font-mono ${item.success ? 'text-rose-500' : 'text-[var(--text-main)]'}`}>{item.technique || item.scenario}</p>
                        <span className={`badge border font-bold uppercase tracking-widest text-[10px] ${item.success ? 'bg-rose-500/10 text-rose-500 border-rose-500/20' : 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'}`}>
                          {item.success ? '防线击穿' : '防御成功'}
                        </span>
                      </div>
                      <p className="text-xs font-medium text-[var(--text-muted)] leading-relaxed bg-[var(--bg-main)]/50 p-2 rounded-lg">{item.scenario || '未返回场景描述'}</p>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            ) : (
              <motion.div 
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex min-h-[400px] flex-col items-center justify-center gap-4 text-center p-8"
              >
                <div className="w-20 h-20 rounded-full bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] flex items-center justify-center">
                  {running ? (
                    <div className="w-10 h-10 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
                  ) : (
                    <Target className="h-10 w-10 text-[var(--text-muted)] opacity-60" />
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[var(--text-main)]">{running ? '演练执行中...' : '系统就绪'}</h3>
                  <p className="mt-2 text-sm font-medium text-[var(--text-muted)] max-w-sm">
                    {running ? '正在组装红队攻击向量矩阵对目标模型进行压力渗透测试，请耐心等待。' : '尚未运行红队演练，请配置左侧演练环境并启动。'}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.section>
      </div>
    </motion.div>
  )
}
