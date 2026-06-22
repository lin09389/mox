import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'react-hot-toast'
import { AlertTriangle, Code2, ShieldAlert, ShieldCheck, Loader2 } from 'lucide-react'
import { evaluationApi, isDemoModeEnabled } from '../api'
import { MetricCard, PanelHeader } from '../components/ui/AppFrame'
import ModelSelect from '../components/ui/ModelSelect'
import { HubPanelIntro } from '../context/HubContext'

const CWE_TYPES = [
  { cwe: 'CWE-89', name: 'SQL 注入', severity: 'critical' },
  { cwe: 'CWE-79', name: 'XSS 跨站脚本', severity: 'high' },
  { cwe: 'CWE-78', name: '命令注入', severity: 'critical' },
  { cwe: 'CWE-22', name: '路径遍历', severity: 'high' },
  { cwe: 'CWE-287', name: '鉴权缺陷', severity: 'high' },
  { cwe: 'CWE-200', name: '敏感信息泄露', severity: 'high' },
]

function demoResult(text) {
  const critical = text.toLowerCase().includes('exec') || text.toLowerCase().includes('shell')
  return {
    _demo_mode: true,
    vulnerabilities: [
      critical
        ? { cwe: 'CWE-78', name: '命令注入', severity: 'critical', detail: '检测到可执行命令拼接，存在严重的 RCE 风险。' }
        : { cwe: 'CWE-79', name: 'XSS 风险', severity: 'high', detail: '输出内容缺少转义处理，可能导致跨站脚本攻击。' },
      { cwe: 'CWE-22', name: '路径遍历', severity: 'medium', detail: '文件路径输入缺少白名单限制，可能被构造跨目录读取文件。' },
    ],
    summary: critical ? '扫描发现高危注入风险 (RCE级别)，建议立即切断该函数的外部输入源，并进行严格转义过滤。' : '代码整体通过基本校验，但仍存在中高危风险，建议补充上下文感知过滤。'
  }
}

import { containerVariants, itemVariants } from '../utils/animations'

export default function CodeSecurityPage() {
  const [selectedModel, setSelectedModel] = useState('qwen:4b')
  const [codePrompt, setCodePrompt] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const runSecurityTest = async () => {
    if (!codePrompt.trim()) {
      toast.error('请输入代码或需求描述。')
      return
    }

    setLoading(true)
    setResult(null)
    try {
      const data = await evaluationApi.codeSecurity({ prompt: codePrompt, model: selectedModel })
      setResult(data)
      toast.success('代码安全检测完成。')
    } catch {
      if (isDemoModeEnabled) {
        setResult(demoResult(codePrompt))
        toast('后端不可用，已展示演示检测结果。', { icon: '⚠️' })
      } else {
        toast.error('代码安全检测失败，请检查后端连接。')
      }
    }
    setLoading(false)
  }

  const vulnerabilities = result?.vulnerabilities || []
  const criticalCount = vulnerabilities.filter((item) => item.severity === 'critical').length

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="page-shell">
      <HubPanelIntro description="使用 AI 引擎进行静态代码分析，快速识别常见 CWE 漏洞与注入风险。" />

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <motion.section variants={itemVariants} className="card p-6 h-fit lg:sticky lg:top-6">
          <PanelHeader title="检测配置" description="输入代码片段或需求描述后开始扫描。" />
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">检测引擎模型</label>
              <ModelSelect value={selectedModel} onChange={setSelectedModel} />
            </div>
            
            <div className="space-y-2">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest flex items-center justify-between">
                <span>代码片段</span>
                <span className="text-cyan-500 font-mono">{codePrompt.length} 字符</span>
              </label>
              <div className="relative">
                <textarea 
                  rows={10} 
                  className="input-field font-mono text-sm leading-relaxed resize-none p-4" 
                  value={codePrompt} 
                  onChange={(event) => setCodePrompt(event.target.value)} 
                  placeholder="粘贴需要进行安全审查的代码片段...&#10;&#10;例如：&#10;function executeUserCommand(cmd) {&#10;  exec('bash -c ' + cmd);&#10;}" 
                />
              </div>
            </div>
            
            <button 
              type="button" 
              onClick={runSecurityTest} 
              disabled={loading || !codePrompt.trim()} 
              className="btn-primary w-full justify-center py-3 bg-cyan-500 hover:bg-cyan-600 border-cyan-500 text-white shadow-[0_0_20px_rgba(6,182,212,0.3)] text-base font-bold disabled:opacity-50 disabled:shadow-none"
            >
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <ShieldAlert className="h-5 w-5" />}
              {loading ? '代码安全扫描中...' : '运行安全检测'}
            </button>
          </div>
        </motion.section>

        <motion.section variants={itemVariants} className="card p-6 bg-[var(--bg-glass-strong)] border-[var(--border-glass)]">
          <PanelHeader title="检测结果" description="按漏洞类型和严重程度展示扫描报告。" />
          
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div 
                key="result"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="space-y-6"
              >
                {result._demo_mode && (
                  <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-3 flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                    <span className="text-xs font-bold text-amber-500 tracking-wide">演示模式：本地环境离线分析</span>
                  </div>
                )}
                
                <div className="grid gap-4 sm:grid-cols-3">
                  <MetricCard icon={Code2} label="检测规则" value={CWE_TYPES.length} hint="已加载项" tone="electric" />
                  <MetricCard icon={ShieldAlert} label="发现漏洞" value={vulnerabilities.length} hint="需修复项" tone="lava" />
                  <MetricCard icon={AlertTriangle} label="高危数量" value={criticalCount} hint="P0/P1级别" tone="amber" />
                </div>
                
                <div className="space-y-4 pt-2">
                  <h4 className="text-sm font-bold font-display text-[var(--text-main)] border-b border-[var(--border-glass)] pb-2 flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-rose-500" /> 漏洞清单</h4>
                  {vulnerabilities.map((item, index) => (
                    <motion.div 
                      key={`${item.cwe}-${index}`} 
                      initial={{ opacity: 0, y: 10 }} 
                      animate={{ opacity: 1, y: 0 }} 
                      transition={{ delay: index * 0.1 }}
                      className={`rounded-xl border p-4 transition-all ${item.severity === 'critical' ? 'bg-rose-500/5 border-rose-500/20' : item.severity === 'high' ? 'bg-amber-500/5 border-amber-500/20' : 'bg-cyan-500/5 border-cyan-500/20'}`}
                    >
                      <div className="mb-2 flex items-center justify-between">
                        <p className={`text-sm font-bold font-mono ${item.severity === 'critical' ? 'text-rose-500' : item.severity === 'high' ? 'text-amber-500' : 'text-cyan-500'}`}>{item.cwe} <span className="font-sans px-2 text-[var(--text-muted)]">·</span> {item.name}</p>
                        <span className={`badge border font-bold uppercase tracking-widest text-[10px] ${item.severity === 'critical' ? 'bg-rose-500/10 text-rose-500 border-rose-500/20' : item.severity === 'high' ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' : 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20'}`}>
                          {item.severity === 'critical' ? 'CRITICAL' : item.severity.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm font-medium text-[var(--text-muted)] leading-relaxed">{item.detail}</p>
                    </motion.div>
                  ))}
                  
                  {vulnerabilities.length === 0 && (
                    <div className="flex items-center gap-3 p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 text-emerald-500">
                      <ShieldCheck className="h-5 w-5" />
                      <span className="text-sm font-bold">未检测到安全漏洞，代码合规。</span>
                    </div>
                  )}
                </div>

                <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-5">
                  <p className="text-sm font-bold text-[var(--text-main)] mb-2 flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-cyan-500" />
                    AI 综合治理建议
                  </p>
                  <p className="text-sm font-medium text-[var(--text-muted)] leading-relaxed bg-[var(--bg-main)]/50 p-3 rounded-lg border border-[var(--border-glass)]">
                    {result.summary || '暂无总结信息。'}
                  </p>
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
                  {loading ? (
                    <div className="w-10 h-10 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
                  ) : (
                    <Code2 className="h-10 w-10 text-[var(--text-muted)] opacity-60" />
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[var(--text-main)]">{loading ? '静态语法分析中...' : '检测面板就绪'}</h3>
                  <p className="mt-2 text-sm font-medium text-[var(--text-muted)] max-w-sm">
                    {loading ? '正在分析代码执行流并匹配 CWE 规则库，识别潜在注入风险。' : '在左侧输入需要检查的代码片段或安全需求，启动一键扫描以获取安全闭环建议。'}
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
