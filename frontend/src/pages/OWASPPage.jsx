import { useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, CheckCircle2, Play, Shield, ShieldAlert, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { runOWASPTests } from '../api/security'
import { HubPanelIntro } from '../context/HubContext'
import { MetricCard, PanelHeader, ProgressMeter } from '../components/ui/AppFrame'
import ModelSelect from '../components/ui/ModelSelect'
import RunCompleteBanner from '../components/ui/RunCompleteBanner'

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
  critical: 'bg-rose-500/10 text-rose-500 border-rose-500/20',
  high: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
  medium: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20',
}

import { containerVariants, itemVariants } from '../utils/animations'

export default function OWASPPage() {
  const [results, setResults] = useState([])
  const [reportId, setReportId] = useState(null)
  const [running, setRunning] = useState(false)
  const [model, setModel] = useState('qwen3:4b')

  const passCount = useMemo(() => results.filter((item) => item.passed).length, [results])
  const passRate = useMemo(
    () => (results.length ? Math.round((passCount / results.length) * 100) : 0),
    [passCount, results.length]
  )

  const handleRun = async () => {
    setRunning(true)
    setResults([])
    setReportId(null)
    try {
      const { results: data, reportId: savedReportId } = await runOWASPTests(model)
      setResults(data)
      setReportId(savedReportId)
      if (data.length > 0) {
        toast.success(savedReportId ? 'OWASP 测试已完成，报告已入库。' : 'OWASP 测试已完成。')
      }
    } catch {
      toast.error('OWASP 测试失败，请检查后端连接与模型配置。')
    } finally {
      setRunning(false)
    }
  }

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="page-shell">
      <HubPanelIntro description="使用 OWASP LLM Top 10 标准类目评估模型在关键风险域的通过率。" />

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <motion.section variants={itemVariants} className="card p-6 h-fit lg:sticky lg:top-6">
          <PanelHeader title="测试配置" description="选择目标模型并运行完整套件。" />
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">目标模型</label>
              <ModelSelect value={model} onChange={setModel} />
            </div>
            
            <button 
              type="button" 
              onClick={handleRun} 
              disabled={running} 
              className="btn-primary w-full justify-center py-3 bg-cyan-500 hover:bg-cyan-600 border-cyan-500 text-white shadow-[0_0_20px_rgba(6,182,212,0.3)] text-base font-bold disabled:opacity-50 disabled:shadow-none"
            >
              {running ? <Loader2 className="h-5 w-5 animate-spin" /> : <Play className="h-5 w-5" />}
              {running ? '套件执行中...' : '运行 OWASP 测试'}
            </button>
            
            <div className="space-y-3 pt-4 border-t border-[var(--border-glass)]">
              {CATEGORIES.map((category) => (
                <div key={category.id} className="rounded-xl border border-[var(--border-glass)] bg-[var(--bg-glass)] px-4 py-3 hover:bg-[var(--bg-glass-strong)] transition-colors">
                  <div className="mb-2 flex items-center justify-between gap-3">
                    <p className="text-sm font-bold text-[var(--text-main)] font-mono">{category.id} <span className="font-sans text-[var(--text-muted)] px-2">·</span> {category.name}</p>
                    <span className={`badge border uppercase tracking-widest text-[10px] ${severityBadge[category.severity]}`}>{category.severity}</span>
                  </div>
                  <p className="text-xs font-medium text-[var(--text-muted)] leading-relaxed">{category.description}</p>
                </div>
              ))}
            </div>
          </div>
        </motion.section>

        <motion.section variants={itemVariants} className="card p-6 bg-[var(--bg-glass-strong)] border-cyan-500/10 shadow-[inset_0_0_40px_rgba(6,182,212,0.02)]">
          <PanelHeader title="测试结果" description="通过率、失败项和风险说明统一呈现。" />
          
          <AnimatePresence mode="wait">
            {results.length > 0 ? (
              <motion.div 
                key="results"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="space-y-6"
              >
                <RunCompleteBanner reportId={reportId} title="评估报告已保存" />

                <div className="grid gap-4 sm:grid-cols-3">
                  <MetricCard icon={Shield} label="总测试项" value={results.length} hint="OWASP Top 10" tone="electric" />
                  <MetricCard icon={CheckCircle2} label="通过项" value={passCount} hint={`${passRate}%`} tone="neon" />
                  <MetricCard icon={AlertTriangle} label="失败项" value={results.length - passCount} hint={`${100 - passRate}%`} tone="lava" />
                </div>
                
                <div className="p-5 rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)]">
                  <ProgressMeter value={passRate} tone={passRate >= 70 ? 'success' : 'warning'} label="总体通过率" />
                </div>
                
                <div className="space-y-3 pt-2">
                  <h4 className="text-sm font-bold font-display text-[var(--text-main)] mb-4 flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-[var(--text-muted)]" /> 详细报告</h4>
                  {results.map((result, index) => {
                    const ref = CATEGORIES.find((item) => item.id === result.category)
                    return (
                      <motion.div 
                        key={`${result.category}-${index}`} 
                        initial={{ opacity: 0, y: 10 }} 
                        animate={{ opacity: 1, y: 0 }} 
                        transition={{ delay: index * 0.05 }}
                        className={`rounded-xl border p-4 transition-all ${result.passed ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-rose-500/5 border-rose-500/20 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-rose-500/10'}`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-sm font-bold text-[var(--text-main)] font-mono">{result.category} <span className="font-sans px-2 text-[var(--text-muted)]">·</span> {ref?.name || result.test}</p>
                          <span className={`badge border font-bold uppercase tracking-widest text-[10px] ${result.passed ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : 'bg-rose-500/10 text-rose-500 border-rose-500/20'}`}>
                            {result.passed ? '安全合规' : '存在风险'}
                          </span>
                        </div>
                        <p className="text-xs font-medium text-[var(--text-muted)] leading-relaxed bg-[var(--bg-main)]/50 p-2 rounded-lg">{result.test}</p>
                      </motion.div>
                    )
                  })}
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
                    <ShieldAlert className="h-10 w-10 text-[var(--text-muted)] opacity-60" />
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[var(--text-main)]">{running ? '测试执行中...' : '系统就绪'}</h3>
                  <p className="mt-2 text-sm font-medium text-[var(--text-muted)] max-w-sm">
                    {running ? '正在对接大模型安全引擎，执行 OWASP LLM Top 10 全栈漏洞扫描，请耐心等待。' : '尚未运行测试，请先在左侧选择模型并启动 OWASP 评估套件。'}
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
