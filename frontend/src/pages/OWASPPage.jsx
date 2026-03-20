import { useState } from 'react'
import { Play, CheckCircle, XCircle, Shield, AlertTriangle, Lock, Info, ChevronDown, ChevronUp, MessageSquare } from 'lucide-react'
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

  const severityColors = {
    critical: 'bg-red-100 text-red-800 border-red-200',
    high: 'bg-orange-100 text-orange-800 border-orange-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-green-100 text-green-800 border-green-200',
  }

  const passedCount = results.filter(r => r.passed).length
  const passRate = results.length > 0 ? (passedCount / results.length * 100).toFixed(1) : 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">OWASP LLM Top 10 安全测试</h1>
          <p className="text-gray-500">全面评估大语言模型应用的安全性</p>
        </div>
        <div className="flex items-center gap-4">
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
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
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            <Play className={`w-4 h-4 ${running ? 'animate-spin' : ''}`} />
            {running ? '测试中...' : '开始测试'}
          </button>
        </div>
      </div>

      {/* 统计卡片 */}
      {results.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <div className="text-3xl font-bold">{results.length}</div>
            <div className="text-gray-500">总测试项</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <div className="text-3xl font-bold text-green-600">{passedCount}</div>
            <div className="text-gray-500">通过</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <div className="text-3xl font-bold text-red-600">{results.length - passedCount}</div>
            <div className="text-gray-500">失败</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <div className="text-3xl font-bold text-indigo-600">{passRate}%</div>
            <div className="text-gray-500">通过率</div>
          </div>
        </div>
      )}

      {/* 测试类别 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Shield className="w-5 h-5 text-indigo-500" />
            安全测试类别
          </h2>
        </div>
        <div className="divide-y divide-gray-200">
          {categories.map((cat) => {
            const catResults = results.filter(r => r.category === cat.id)
            const catPassed = catResults.filter(r => r.passed).length
            const catTotal = catResults.length
            
            return (
              <div key={cat.id} className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`px-2 py-1 rounded text-xs font-bold ${severityColors[cat.severity]}`}>
                      {cat.severity.toUpperCase()}
                    </div>
                    <div>
                      <h3 className="font-semibold">{cat.id}: {cat.name}</h3>
                      <p className="text-sm text-gray-500">{cat.description}</p>
                    </div>
                  </div>
                  {catTotal > 0 && (
                    <div className="flex items-center gap-2">
                      {catPassed === catTotal ? (
                        <CheckCircle className="w-5 h-5 text-green-500" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-500" />
                      )}
                      <span>{catPassed}/{catTotal}</span>
                    </div>
                  )}
                </div>
                
                {catResults.length > 0 && (
                  <div className="ml-8 space-y-2">
                    {catResults.map((result, i) => {
                      const testKey = `${result.category}-${result.test}-${i}`
                      const isExpanded = expandedTest === testKey
                      
                      return (
                        <div key={i} className="border border-gray-200 rounded-lg overflow-hidden">
                          <div 
                            className="flex items-center justify-between p-3 bg-gray-50 cursor-pointer hover:bg-gray-100"
                            onClick={() => setExpandedTest(isExpanded ? null : testKey)}
                          >
                            <div className="flex items-center gap-3">
                              <span className="text-sm font-medium">{result.test}</span>
                              {result.severity && (
                                <span className={`text-xs px-2 py-0.5 rounded ${
                                  result.severity === 'critical' ? 'bg-red-100 text-red-700' :
                                  result.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                                  'bg-yellow-100 text-yellow-700'
                                }`}>
                                  {result.severity}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              {result.passed ? (
                                <span className="flex items-center gap-1 text-green-600 text-sm">
                                  <CheckCircle className="w-4 h-4" /> 已防护
                                </span>
                              ) : (
                                <span className="flex items-center gap-1 text-red-600 text-sm">
                                  <XCircle className="w-4 h-4" /> 存在漏洞
                                </span>
                              )}
                              {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            </div>
                          </div>
                          
                          {isExpanded && (
                            <div className="p-4 bg-white border-t border-gray-200 space-y-3">
                              {result.description && (
                                <div>
                                  <div className="text-xs font-semibold text-gray-500 mb-1">漏洞描述</div>
                                  <p className="text-sm text-red-600">{result.description}</p>
                                </div>
                              )}
                              
                              {result.model_response && (
                                <div>
                                  <div className="text-xs font-semibold text-gray-500 mb-1 flex items-center gap-1">
                                    <MessageSquare className="w-3 h-3" /> 模型响应
                                  </div>
                                  <div className="text-sm bg-gray-50 p-2 rounded font-mono text-gray-700 max-h-24 overflow-y-auto">
                                    {result.model_response}
                                  </div>
                                </div>
                              )}
                              
                              {result.recommendation && (
                                <div>
                                  <div className="text-xs font-semibold text-gray-500 mb-1">修复建议</div>
                                  <p className="text-sm text-green-700 bg-green-50 p-2 rounded">{result.recommendation}</p>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* 空状态 */}
      {results.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <Shield className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-600 mb-2">点击开始运行 OWASP 测试</h3>
          <p className="text-gray-500 mb-4">系统将对您的 LLM 进行全面的安全评估</p>
          <div className="flex justify-center gap-4 text-sm text-gray-400">
            <span className="flex items-center gap-1"><Lock className="w-4 h-4" /> 10个安全类别</span>
            <span className="flex items-center gap-1"><Info className="w-4 h-4" /> 详细漏洞分析</span>
          </div>
        </div>
      )}
    </div>
  )
}
