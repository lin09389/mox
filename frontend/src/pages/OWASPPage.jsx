import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Play,
  CheckCircle,
  XCircle,
  Shield,
  AlertTriangle,
  Lock,
  Info,
  ChevronDown,
  ChevronUp,
  MessageSquare
} from 'lucide-react'
import { runOWASPTests } from '../api/security'

const categories = [
  { id: 'LLM01', name: '提示词注入', description: '通过恶意提示词绕过安全限制', severity: 'critical' },
  { id: 'LLM02', name: '敏感信息泄露', description: '模型意外暴露敏感数据', severity: 'critical' },
  { id: 'LLM03', name: '供应链漏洞', description: '第三方组件和模型的安全问题', severity: 'high' },
  { id: 'LLM04', name: '数据投毒', description: '恶意训练数据影响模型行为', severity: 'high' },
  { id: 'LLM05', name: '错误处理不当', description: '错误信息泄露系统细节', severity: 'medium' },
  { id: 'LLM06', name: '提示词漏洞', description: '提示词设计不当导致被利用', severity: 'high' },
  { id: 'LLM07', name: '不安全的插件', description: '插件设计缺陷被攻击', severity: 'critical' },
  { id: 'LLM08', name: '过度授权', description: '模型拥有过多执行权限', severity: 'critical' },
  { id: 'LLM09', name: '过度依赖', description: '盲目信任模型输出导致错误', severity: 'medium' },
  { id: 'LLM10', name: '向量嵌入弱点', description: 'RAG系统被注入恶意上下文', severity: 'high' },
]

const severityConfig = {
  critical: { label: '严重', bg: 'bg-crimson-50', text: 'text-crimson-700', border: 'border-crimson-200/70' },
  high: { label: '高危', bg: 'bg-lava-50', text: 'text-lava-700', border: 'border-lava-200/70' },
  medium: { label: '中危', bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200/70' },
  low: { label: '低危', bg: 'bg-neon-50', text: 'text-neon-700', border: 'border-neon-200/70' },
}

export default function OWASPPage() {
  const [results, setResults] = useState([])
  const [running, setRunning] = useState(false)
  const [model, setModel] = useState('qwen3:4b')
  const [expandedTest, setExpandedTest] = useState(null)

  const handleRunTests = async () => {
    setRunning(true)
    try {
      const testResults = await runOWASPTests(model)
      setResults(testResults)
    } catch (error) {
      console.error('运行测试失败:', error)
    } finally {
      setRunning(false)
    }
  }

  const passedCount = results.filter(r => r.passed).length
  const passRate = results.length > 0 ? (passedCount / results.length * 100).toFixed(1) : 0

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-electric-100 rounded-lg flex items-center justify-center border border-electric-200/70">
            <Shield className="w-6 h-6 text-electric-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold font-display text-graphite-900 tracking-tight">
              OWASP LLM Top 10 安全测试
            </h1>
            <p className="text-sm text-graphite-500 mt-0.5">全面评估大语言模型应用的安全性</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="select-field w-40"
          >
            <option value="qwen3:4b">Qwen3:4B (本地)</option>
            <option value="gemma3:4b">Gemma3:4B (本地)</option>
            <option value="gpt-4">GPT-4</option>
            <option value="gpt-3.5">GPT-3.5</option>
            <option value="claude-3">Claude 3</option>
            <option value="gemini-pro">Gemini Pro</option>
          </select>
          <button
            onClick={handleRunTests}
            disabled={running}
            className="btn-primary"
          >
            {running ? (
              <>
                <div className="spinner" />
                测试中...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                开始测试
              </>
            )}
          </button>
        </div>
      </motion.div>

      {/* 统计卡片 */}
      {results.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-4"
        >
          <div className="card text-center">
            <p className="text-3xl font-bold font-display text-graphite-900">{results.length}</p>
            <p className="text-xs text-graphite-500 mt-1">总测试项</p>
          </div>
          <div className="card text-center">
            <p className="text-3xl font-bold font-display text-neon-600">{passedCount}</p>
            <p className="text-xs text-graphite-500 mt-1">通过</p>
          </div>
          <div className="card text-center">
            <p className="text-3xl font-bold font-display text-lava-600">{results.length - passedCount}</p>
            <p className="text-xs text-graphite-500 mt-1">失败</p>
          </div>
          <div className="card text-center">
            <p className="text-3xl font-bold font-display text-electric-600">{passRate}%</p>
            <p className="text-xs text-graphite-500 mt-1">通过率</p>
          </div>
        </motion.div>
      )}

      {/* 测试类别 */}
      <div className="card p-0 overflow-hidden">
        <div className="px-5 py-4 border-b border-graphite-200/60">
          <h2 className="text-base font-semibold text-graphite-900 flex items-center gap-2">
            <Shield className="w-4.5 h-4.5 text-electric-500" />
            安全测试类别
          </h2>
        </div>
        <div className="divide-y divide-graphite-200/60">
          {categories.map((cat, catIdx) => {
            const catResults = results.filter(r => r.category === cat.id)
            const catPassed = catResults.filter(r => r.passed).length
            const catTotal = catResults.length
            const sev = severityConfig[cat.severity]

            return (
              <motion.div
                key={cat.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: catIdx * 0.05 }}
                className="p-5"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className={`px-2.5 py-1 rounded-sm text-xs font-bold ${sev.bg} ${sev.text} ${sev.border} border`}>
                      {sev.label}
                    </span>
                    <div>
                      <h3 className="font-semibold text-sm text-graphite-900">{cat.id}: {cat.name}</h3>
                      <p className="text-xs text-graphite-500">{cat.description}</p>
                    </div>
                  </div>
                  {catTotal > 0 && (
                    <div className="flex items-center gap-2">
                      {catPassed === catTotal ? (
                        <CheckCircle className="w-5 h-5 text-neon-500" />
                      ) : (
                        <XCircle className="w-5 h-5 text-lava-500" />
                      )}
                      <span className="text-sm font-medium text-graphite-700">{catPassed}/{catTotal}</span>
                    </div>
                  )}
                </div>

                {catResults.length > 0 && (
                  <div className="ml-6 space-y-2">
                    {catResults.map((result, i) => {
                      const testKey = `${result.category}-${result.test}-${i}`
                      const isExpanded = expandedTest === testKey

                      return (
                        <div key={i} className="border border-graphite-200/60 rounded-md overflow-hidden">
                          <div
                            className="flex items-center justify-between p-3 bg-graphite-50/60 cursor-pointer hover:bg-graphite-100/60 transition-colors"
                            onClick={() => setExpandedTest(isExpanded ? null : testKey)}
                          >
                            <div className="flex items-center gap-3">
                              <span className="text-sm font-medium text-graphite-800">{result.test}</span>
                              {result.severity && (
                                <span className={`text-[11px] px-2 py-0.5 rounded ${
                                  result.severity === 'critical' ? 'bg-crimson-50 text-crimson-700' :
                                  result.severity === 'high' ? 'bg-lava-50 text-lava-700' :
                                  'bg-amber-50 text-amber-700'
                                }`}>
                                  {result.severity}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              {result.passed ? (
                                <span className="flex items-center gap-1 text-neon-600 text-xs font-medium">
                                  <CheckCircle className="w-3.5 h-3.5" /> 已防护
                                </span>
                              ) : (
                                <span className="flex items-center gap-1 text-lava-600 text-xs font-medium">
                                  <XCircle className="w-3.5 h-3.5" /> 存在漏洞
                                </span>
                              )}
                              {isExpanded ? <ChevronUp className="w-4 h-4 text-graphite-400" /> : <ChevronDown className="w-4 h-4 text-graphite-400" />}
                            </div>
                          </div>

                          {isExpanded && (
                            <div className="p-4 bg-white border-t border-graphite-200/60 space-y-3">
                              {result.description && (
                                <div>
                                  <div className="text-[11px] font-semibold text-graphite-500 mb-1">漏洞描述</div>
                                  <p className="text-sm text-lava-700">{result.description}</p>
                                </div>
                              )}

                              {result.model_response && (
                                <div>
                                  <div className="text-[11px] font-semibold text-graphite-500 mb-1 flex items-center gap-1">
                                    <MessageSquare className="w-3 h-3" /> 模型响应
                                  </div>
                                  <div className="text-xs bg-graphite-50 p-3 rounded font-mono text-graphite-700 max-h-20 overflow-y-auto leading-relaxed">
                                    {result.model_response}
                                  </div>
                                </div>
                              )}

                              {result.recommendation && (
                                <div>
                                  <div className="text-[11px] font-semibold text-graphite-500 mb-1">修复建议</div>
                                  <p className="text-sm text-neon-700 bg-neon-50/50 p-3 rounded border border-neon-200/60">{result.recommendation}</p>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* 空状态 */}
      {results.length === 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="card flex flex-col items-center justify-center min-h-[300px] text-center"
        >
          <div className="w-16 h-16 rounded-xl bg-graphite-100 flex items-center justify-center mb-4">
            <Shield className="w-8 h-8 text-graphite-400" />
          </div>
          <h3 className="text-base font-semibold text-graphite-700 mb-2">点击开始运行 OWASP 测试</h3>
          <p className="text-sm text-graphite-500 mb-5">系统将对您的 LLM 进行全面的安全评估</p>
          <div className="flex justify-center gap-6 text-xs text-graphite-400">
            <span className="flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5" />
              10个安全类别
            </span>
            <span className="flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5" />
              详细漏洞分析
            </span>
          </div>
        </motion.div>
      )}
    </div>
  )
}
