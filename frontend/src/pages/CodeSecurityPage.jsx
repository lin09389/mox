import { useState } from 'react'
import { motion } from 'framer-motion'
import { toast } from 'react-hot-toast'
import { api } from '../api'
import { useCommon } from '../hooks/useCommon'
import { ShieldAlert, AlertTriangle, CheckCircle2, Bug, Code2 } from 'lucide-react'

const cweTypes = [
  { cwe: 'CWE-89', name: 'SQL 注入', severity: 'critical' },
  { cwe: 'CWE-79', name: 'XSS 跨站脚本', severity: 'high' },
  { cwe: 'CWE-78', name: '命令注入', severity: 'critical' },
  { cwe: 'CWE-22', name: '路径遍历', severity: 'high' },
  { cwe: 'CWE-502', name: '不安全反序列化', severity: 'critical' },
  { cwe: 'CWE-287', name: '身份验证缺陷', severity: 'high' },
  { cwe: 'CWE-200', name: '敏感数据泄露', severity: 'high' },
  { cwe: 'CWE-918', name: 'SSRF', severity: 'high' },
]

const severityConfig = {
  critical: { bg: 'bg-lava-100', text: 'text-lava-700', border: 'border-lava-200/70' },
  high: { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-200/70' },
  medium: { bg: 'bg-electric-100', text: 'text-electric-700', border: 'border-electric-200/70' },
  low: { bg: 'bg-neon-100', text: 'text-neon-700', border: 'border-neon-200/70' },
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
}

const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } },
}

export default function CodeSecurityPage() {
  const { models, loading: modelsLoading } = useCommon()
  const [selectedModel, setSelectedModel] = useState('qwen:4b')
  const [codePrompt, setCodePrompt] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)

  const runSecurityTest = async () => {
    if (!codePrompt.trim()) {
      toast.error('请输入代码需求')
      return
    }

    setLoading(true)
    try {
      const response = await api.post('/api/code/security', {
        prompt: codePrompt,
        model: selectedModel,
      })
      setResults(response.data)
      toast.success('安全检测完成')
    } catch (error) {
      toast.error('检测失败: ' + (error.message || '未知错误'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      {/* 页面标题 */}
      <motion.div variants={item} className="flex items-center gap-3">
        <div className="w-11 h-11 bg-electric-100 rounded-lg flex items-center justify-center border border-electric-200/70">
          <ShieldAlert className="w-5.5 h-5.5 text-electric-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold font-display text-graphite-900 tracking-tight">
            代码安全检测
          </h1>
          <p className="text-sm text-graphite-500">检测 LLM 生成代码中的安全漏洞 (CWE 分类)</p>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左侧表单 */}
        <motion.div variants={item} className="space-y-5">
          <div className="card">
            <h3 className="text-sm font-semibold text-graphite-900 mb-4">测试配置</h3>

            <div className="mb-4">
              <label className="label mb-2">选择模型</label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="select-field"
                disabled={modelsLoading}
              >
                <option value="qwen3:4b">Qwen3:4B (本地)</option>
                <option value="gemma3:4b">Gemma3:4B (本地)</option>
                <option value="llama3">Llama 3 (本地)</option>
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-3.5-turbo">GPT-3.5</option>
              </select>
            </div>

            <div className="mb-5">
              <label className="label mb-2">代码需求描述</label>
              <textarea
                value={codePrompt}
                onChange={(e) => setCodePrompt(e.target.value)}
                placeholder="例如: 写一个用户登录的Python函数"
                rows={4}
                className="textarea-field font-mono text-sm"
              />
            </div>

            <motion.button
              className="btn-primary w-full"
              onClick={runSecurityTest}
              disabled={loading}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              {loading ? (
                <>
                  <div className="spinner" />
                  检测中...
                </>
              ) : (
                <>
                  <Bug className="w-4 h-4" />
                  开始安全检测
                </>
              )}
            </motion.button>
          </div>
        </motion.div>

        {/* 右侧支持的漏洞类型 */}
        <motion.div variants={item} className="card">
          <h3 className="text-sm font-semibold text-graphite-900 mb-4">支持的漏洞类型</h3>
          <div className="space-y-3">
            {cweTypes.map((item) => {
              const severity = severityConfig[item.severity] || severityConfig.medium
              return (
                <div
                  key={item.cwe}
                  className="flex items-center justify-between p-3 bg-graphite-50/50 rounded-lg border border-graphite-200/60"
                >
                  <div>
                    <span className="text-[11px] text-graphite-400 font-mono">{item.cwe}</span>
                    <p className="font-medium text-sm text-graphite-900">{item.name}</p>
                  </div>
                  <span
                    className={`text-xs px-2 py-1 rounded font-medium ${severity.bg} ${severity.text}`}
                  >
                    {item.severity}
                  </span>
                </div>
              )
            })}
          </div>
        </motion.div>
      </div>

      {results && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="card"
        >
          <h3 className="text-sm font-semibold text-graphite-900 mb-5">检测结果</h3>

          {/* 统计卡片 */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="card text-center bg-lava-50/50 border-lava-200/70">
              <p className="text-2xl font-bold font-display text-lava-600">
                {results.critical || 0}
              </p>
              <p className="text-xs text-graphite-500 mt-1">严重</p>
            </div>
            <div className="card text-center bg-amber-50/50 border-amber-200/70">
              <p className="text-2xl font-bold font-display text-amber-600">
                {results.high || 0}
              </p>
              <p className="text-xs text-graphite-500 mt-1">高危</p>
            </div>
            <div className="card text-center bg-electric-50/50 border-electric-200/70">
              <p className="text-2xl font-bold font-display text-electric-600">
                {results.medium || 0}
              </p>
              <p className="text-xs text-graphite-500 mt-1">中危</p>
            </div>
            <div className="card text-center bg-neon-50/50 border-neon-200/70">
              <p className="text-2xl font-bold font-display text-neon-600">
                {results.low || 0}
              </p>
              <p className="text-xs text-graphite-500 mt-1">低危</p>
            </div>
          </div>

          <div className="space-y-4">
            {results.vulnerabilities?.map((vuln, idx) => (
              <div
                key={idx}
                className="p-4 bg-graphite-50/50 rounded-lg border-l-4 border-lava-500"
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className="text-[11px] text-graphite-400 font-mono">{vuln.cwe_id}</span>
                    <h4 className="font-semibold text-sm text-graphite-900">{vuln.name}</h4>
                  </div>
                  <span
                    className={`text-xs px-2 py-1 rounded font-medium ${
                      severityConfig[vuln.severity]?.bg || severityConfig.medium.bg
                    } ${severityConfig[vuln.severity]?.text || severityConfig.medium.text}`}
                  >
                    {vuln.severity}
                  </span>
                </div>
                <p className="text-sm text-graphite-600 mb-2">{vuln.description}</p>
                {vuln.code_snippet && (
                  <pre className="text-xs bg-graphite-900 text-electric-400 p-3 rounded-md overflow-x-auto font-mono">
                    {vuln.code_snippet}
                  </pre>
                )}
                <p className="text-xs text-neon-600 mt-2 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  修复建议: {vuln.recommendation}
                </p>
              </div>
            ))}

            {results.total_issues === 0 && (
              <div className="text-center py-8">
                <div className="w-12 h-12 mx-auto mb-3 bg-neon-100 rounded-full flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6 text-neon-600" />
                </div>
                <p className="text-lg font-semibold text-neon-700">未检测到安全漏洞</p>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
