import { useState } from 'react'
import { toast } from 'react-hot-toast'
import { api } from '../api'
import { useCommon } from '../hooks/useCommon'

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
        model: selectedModel
      })
      setResults(response.data)
      toast.success('安全检测完成')
    } catch (error) {
      toast.error('检测失败: ' + (error.message || '未知错误'))
    } finally {
      setLoading(false)
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-500'
      case 'high': return 'bg-orange-500'
      case 'medium': return 'bg-yellow-500'
      case 'low': return 'bg-blue-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>代码安全检测</h1>
        <p className="text-gray-400">检测 LLM 生成代码中的安全漏洞 (CWE 分类)</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="card-title">测试配置</h2>
          
          <div className="form-group">
            <label>选择模型</label>
            <select 
              value={selectedModel} 
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={modelsLoading}
            >
              <option value="qwen3:4b">Qwen3:4B (本地)</option>
              <option value="gemma3:4b">Gemma3:4B (本地)</option>
              <option value="llama3">Llama 3 (本地)</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-3.5-turbo">GPT-3.5</option>
            </select>
          </div>

          <div className="form-group">
            <label>代码需求描述</label>
            <textarea
              value={codePrompt}
              onChange={(e) => setCodePrompt(e.target.value)}
              placeholder="例如: 写一个用户登录的Python函数"
              rows={4}
            />
          </div>

          <button 
            className="btn btn-primary w-full"
            onClick={runSecurityTest}
            disabled={loading}
          >
            {loading ? '检测中...' : '开始安全检测'}
          </button>
        </div>

        <div className="card">
          <h2 className="card-title">支持的漏洞类型</h2>
          <div className="space-y-3">
            {[
              { cwe: 'CWE-89', name: 'SQL 注入', severity: 'critical' },
              { cwe: 'CWE-79', name: 'XSS 跨站脚本', severity: 'high' },
              { cwe: 'CWE-78', name: '命令注入', severity: 'critical' },
              { cwe: 'CWE-22', name: '路径遍历', severity: 'high' },
              { cwe: 'CWE-502', name: '不安全反序列化', severity: 'critical' },
              { cwe: 'CWE-287', name: '身份验证缺陷', severity: 'high' },
              { cwe: 'CWE-200', name: '敏感数据泄露', severity: 'high' },
              { cwe: 'CWE-918', name: 'SSRF', severity: 'high' },
            ].map((item) => (
              <div key={item.cwe} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                <div>
                  <span className="text-xs text-gray-400">{item.cwe}</span>
                  <p className="font-medium">{item.name}</p>
                </div>
                <span className={`px-2 py-1 text-xs rounded ${getSeverityColor(item.severity)} text-white`}>
                  {item.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {results && (
        <div className="card mt-6">
          <h2 className="card-title">检测结果</h2>
          
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="stat-card bg-red-900/30 border-red-500">
              <p className="text-2xl font-bold text-red-400">{results.critical || 0}</p>
              <p className="text-sm text-gray-400">严重</p>
            </div>
            <div className="stat-card bg-orange-900/30 border-orange-500">
              <p className="text-2xl font-bold text-orange-400">{results.high || 0}</p>
              <p className="text-sm text-gray-400">高危</p>
            </div>
            <div className="stat-card bg-yellow-900/30 border-yellow-500">
              <p className="text-2xl font-bold text-yellow-400">{results.medium || 0}</p>
              <p className="text-sm text-gray-400">中危</p>
            </div>
            <div className="stat-card bg-blue-900/30 border-blue-500">
              <p className="text-2xl font-bold text-blue-400">{results.low || 0}</p>
              <p className="text-sm text-gray-400">低危</p>
            </div>
          </div>

          <div className="space-y-4">
            {results.vulnerabilities?.map((vuln, idx) => (
              <div key={idx} className="p-4 bg-gray-800 rounded-lg border-l-4 border-red-500">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className="text-xs text-gray-400">{vuln.cwe_id}</span>
                    <h3 className="font-bold">{vuln.name}</h3>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded ${getSeverityColor(vuln.severity)} text-white`}>
                    {vuln.severity}
                  </span>
                </div>
                <p className="text-sm text-gray-300 mb-2">{vuln.description}</p>
                {vuln.code_snippet && (
                  <pre className="text-xs bg-black p-2 rounded overflow-x-auto text-red-300">
                    {vuln.code_snippet}
                  </pre>
                )}
                <p className="text-xs text-green-400 mt-2">修复建议: {vuln.recommendation}</p>
              </div>
            ))}
            
            {results.total_issues === 0 && (
              <div className="text-center py-8 text-green-400">
                <p className="text-xl">✓ 未检测到安全漏洞</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
