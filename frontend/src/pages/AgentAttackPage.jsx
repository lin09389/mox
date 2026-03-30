import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  ShieldExclamationIcon,
  CogIcon,
  BeakerIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  ServerIcon
} from '@heroicons/react/24/outline'
import api from '../api'

const AGENT_ATTACK_TYPES = [
  {
    id: 'tool_chaining',
    name: '工具链攻击',
    description: '通过组合多个工具调用来实现危险操作',
    severity: 'critical'
  },
  {
    id: 'indirect_injection',
    name: '间接工具注入',
    description: '通过外部数据源注入恶意工具调用指令',
    severity: 'high'
  },
  {
    id: 'privilege_escalation',
    name: '权限提升攻击',
    description: '尝试让 Agent 以更高权限执行操作',
    severity: 'critical'
  },
  {
    id: 'tool_confusion',
    name: '工具混淆攻击',
    description: '通过混淆工具描述或参数来诱导错误调用',
    severity: 'high'
  },
  {
    id: 'data_exfiltration',
    name: '数据窃取攻击',
    description: '尝试让 Agent 泄露敏感数据',
    severity: 'critical'
  },
  {
    id: 'multi_agent',
    name: '多 Agent 攻击',
    description: '利用多个 Agent 之间的交互进行攻击',
    severity: 'high'
  },
]

const TOOL_DEFINITIONS = [
  { name: 'read_file', description: '读取文件', dangerous: false },
  { name: 'write_file', description: '写入文件', dangerous: true },
  { name: 'execute_code', description: '执行代码', dangerous: true },
  { name: 'http_request', description: 'HTTP 请求', dangerous: false },
  { name: 'database_query', description: '数据库查询', dangerous: true },
  { name: 'send_email', description: '发送邮件', dangerous: true },
]

// 云端模型
const CLOUD_MODELS = [
  { id: 'gpt-4', name: 'GPT-4', provider: 'OpenAI' },
  { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', provider: 'OpenAI' },
  { id: 'claude-3-opus', name: 'Claude 3 Opus', provider: 'Anthropic' },
  { id: 'claude-3-sonnet', name: 'Claude 3 Sonnet', provider: 'Anthropic' },
  { id: 'gemini-pro', name: 'Gemini Pro', provider: 'Google' },
]

// Ollama 本地模型
const OLLAMA_MODELS = [
  { id: 'llama3', name: 'Llama 3', provider: 'Ollama' },
  { id: 'llama3.1', name: 'Llama 3.1', provider: 'Ollama' },
  { id: 'llama3.2', name: 'Llama 3.2', provider: 'Ollama' },
  { id: 'qwen2', name: 'Qwen 2', provider: 'Ollama' },
  { id: 'qwen2.5', name: 'Qwen 2.5', provider: 'Ollama' },
  { id: 'qwen3', name: 'Qwen 3', provider: 'Ollama' },
  { id: 'qwen3:4b', name: 'Qwen 3 (4B)', provider: 'Ollama' },
  { id: 'gemma3', name: 'Gemma 3', provider: 'Ollama' },
  { id: 'gemma3:4b', name: 'Gemma 3 (4B)', provider: 'Ollama' },
  { id: 'mistral', name: 'Mistral', provider: 'Ollama' },
  { id: 'phi3', name: 'Phi-3', provider: 'Ollama' },
  { id: 'deepseek-coder', name: 'DeepSeek Coder', provider: 'Ollama' },
]

export default function AgentAttackPage() {
  const [attackType, setAttackType] = useState('tool_chaining')
  const [targetPrompt, setTargetPrompt] = useState('')
  const [targetBehavior, setTargetBehavior] = useState('')
  const [selectedTools, setSelectedTools] = useState(['read_file', 'http_request'])
  const [modelName, setModelName] = useState('gpt-4')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  
  // Ollama 相关状态
  const [useOllama, setUseOllama] = useState(false)
  const [ollamaStatus, setOllamaStatus] = useState(null)
  const [ollamaModels, setOllamaModels] = useState([])
  const [ollamaBaseUrl, setOllamaBaseUrl] = useState('http://localhost:11434/v1')
  const [checkingOllama, setCheckingOllama] = useState(false)

  // 检查 Ollama 状态
  useEffect(() => {
    if (useOllama) {
      checkOllamaStatus()
    }
  }, [useOllama])

  const checkOllamaStatus = async () => {
    setCheckingOllama(true)
    try {
      const response = await api.get('/api/v2/ollama/status', {
        params: { base_url: 'http://localhost:11434' }
      })
      setOllamaStatus(response.data)
      if (response.data.status === 'running' && response.data.models) {
        setOllamaModels(response.data.models.map(m => ({
          id: m.name,
          name: m.name,
          provider: 'Ollama',
          size: m.size
        })))
        // 如果有模型，自动选择第一个
        if (response.data.models.length > 0 && !modelName.includes(response.data.models[0].name)) {
          setModelName(response.data.models[0].name)
        }
      }
    } catch (err) {
      setOllamaStatus({ status: 'error', message: '无法连接到 Ollama 服务' })
    } finally {
      setCheckingOllama(false)
    }
  }

  const handleToolToggle = (toolName) => {
    setSelectedTools(prev =>
      prev.includes(toolName)
        ? prev.filter(t => t !== toolName)
        : [...prev, toolName]
    )
  }

  const handleAttack = async () => {
    if (!targetPrompt.trim()) {
      setError('请输入目标提示')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await api.post('/api/v2/attacks/agent', {
        attack_type: attackType,
        prompt: targetPrompt,
        target_behavior: targetBehavior || targetPrompt,
        model_name: modelName,
        tools: selectedTools,
        use_ollama: useOllama,
        ollama_base_url: ollamaBaseUrl,
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || '攻击执行失败')
    } finally {
      setLoading(false)
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50'
      case 'high': return 'text-orange-600 bg-orange-50'
      case 'medium': return 'text-yellow-600 bg-yellow-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <CogIcon className="w-8 h-8 text-purple-600" />
            Agent 攻击测试
          </h1>
          <p className="text-gray-500 mt-1">
            针对 AI Agent 系统的专项安全测试
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel - Configuration */}
        <div className="lg:col-span-2 space-y-6">
          {/* Attack Type Selection */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <ShieldExclamationIcon className="w-5 h-5 text-purple-600" />
              选择攻击类型
            </h2>
            <div className="grid grid-cols-2 gap-3">
              {AGENT_ATTACK_TYPES.map((type) => (
                <motion.button
                  key={type.id}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setAttackType(type.id)}
                  className={`p-4 rounded-lg border-2 text-left transition-all ${
                    attackType === type.id
                      ? 'border-purple-500 bg-purple-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">{type.name}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${getSeverityColor(type.severity)}`}>
                      {type.severity.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">{type.description}</p>
                </motion.button>
              ))}
            </div>
          </div>

          {/* Tool Selection */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <BeakerIcon className="w-5 h-5 text-blue-600" />
              可用工具配置
            </h2>
            <div className="flex flex-wrap gap-2">
              {TOOL_DEFINITIONS.map((tool) => (
                <button
                  key={tool.name}
                  onClick={() => handleToolToggle(tool.name)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                    selectedTools.includes(tool.name)
                      ? tool.dangerous
                        ? 'bg-red-100 text-red-700 border-2 border-red-300'
                        : 'bg-blue-100 text-blue-700 border-2 border-blue-300'
                      : 'bg-gray-100 text-gray-600 border-2 border-transparent hover:bg-gray-200'
                  }`}
                >
                  {tool.name}
                  {tool.dangerous && (
                    <ExclamationTriangleIcon className="w-4 h-4 inline ml-1" />
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Target Input */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">目标配置</h2>
            <div className="space-y-4">
              {/* Ollama 开关 */}
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <ServerIcon className="w-5 h-5 text-gray-600" />
                  <div>
                    <span className="font-medium text-gray-900">使用 Ollama 本地模型</span>
                    <p className="text-sm text-gray-500">无需 API Key，使用本地部署的模型</p>
                  </div>
                </div>
                <button
                  onClick={() => setUseOllama(!useOllama)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    useOllama ? 'bg-purple-600' : 'bg-gray-300'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      useOllama ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {/* Ollama 状态 */}
              {useOllama && (
                <div className="p-4 border border-purple-200 rounded-lg bg-purple-50">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-medium text-purple-900">Ollama 服务状态</h3>
                    <button
                      onClick={checkOllamaStatus}
                      disabled={checkingOllama}
                      className="text-sm text-purple-600 hover:text-purple-800"
                    >
                      {checkingOllama ? '检查中...' : '刷新'}
                    </button>
                  </div>
                  {ollamaStatus ? (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${
                          ollamaStatus.status === 'running' ? 'bg-green-500' : 'bg-red-500'
                        }`} />
                        <span className="text-sm">
                          {ollamaStatus.status === 'running' 
                            ? `运行中 (${ollamaStatus.model_count || 0} 个模型)` 
                            : ollamaStatus.message || '未运行'}
                        </span>
                      </div>
                      {ollamaStatus.status === 'running' && ollamaModels.length > 0 && (
                        <div className="text-sm text-gray-600">
                          已安装: {ollamaModels.map(m => m.name).join(', ')}
                        </div>
                      )}
                      {ollamaStatus.hint && (
                        <div className="text-sm text-orange-600">{ollamaStatus.hint}</div>
                      )}
                    </div>
                  ) : (
                    <div className="text-sm text-gray-500">点击刷新检查状态</div>
                  )}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  目标提示
                </label>
                <textarea
                  value={targetPrompt}
                  onChange={(e) => setTargetPrompt(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="输入攻击目标提示..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  目标行为（可选）
                </label>
                <input
                  type="text"
                  value={targetBehavior}
                  onChange={(e) => setTargetBehavior(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="描述期望的目标行为..."
                />
              </div>
              
              {/* 模型选择 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  目标模型
                </label>
                <select
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  {useOllama ? (
                    <>
                      {/* 已安装的 Ollama 模型 */}
                      {ollamaModels.length > 0 && (
                        <optgroup label="已安装的模型">
                          {ollamaModels.map((model) => (
                            <option key={model.id} value={model.id}>
                              {model.name} {model.size ? `(${(model.size / 1e9).toFixed(1)}GB)` : ''}
                            </option>
                          ))}
                        </optgroup>
                      )}
                      {/* 预定义的 Ollama 模型 */}
                      <optgroup label="其他 Ollama 模型">
                        {OLLAMA_MODELS.filter(m => !ollamaModels.find(om => om.id === m.id)).map((model) => (
                          <option key={model.id} value={model.id}>
                            {model.name}
                          </option>
                        ))}
                      </optgroup>
                    </>
                  ) : (
                    <>
                      <optgroup label="云端模型 (需要 API Key)">
                        {CLOUD_MODELS.map((model) => (
                          <option key={model.id} value={model.id}>
                            {model.name} ({model.provider})
                          </option>
                        ))}
                      </optgroup>
                    </>
                  )}
                </select>
              </div>

              {/* Ollama 服务地址 */}
              {useOllama && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ollama 服务地址
                  </label>
                  <input
                    type="text"
                    value={ollamaBaseUrl}
                    onChange={(e) => setOllamaBaseUrl(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="http://localhost:11434/v1"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Execute Button */}
          <button
            onClick={handleAttack}
            disabled={loading}
            className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-all ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-purple-600 hover:bg-purple-700'
            }`}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                执行中...
              </span>
            ) : (
              '执行攻击'
            )}
          </button>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
        </div>

        {/* Right Panel - Results */}
        <div className="space-y-6">
          {/* Result Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <ChartBarIcon className="w-5 h-5 text-green-600" />
              攻击结果
            </h2>
            {result ? (
              <div className="space-y-4">
                <div className={`p-4 rounded-lg ${
                  result.result === 'success' ? 'bg-red-50' : 'bg-green-50'
                }`}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`text-2xl font-bold ${
                      result.result === 'success' ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {result.result === 'success' ? '攻击成功' : '攻击失败'}
                    </span>
                    {result.ollama_mode && (
                      <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded">
                        Ollama
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-600">
                    成功分数: {(result.success_score * 100).toFixed(1)}%
                  </div>
                  {result.model_used && (
                    <div className="text-sm text-gray-500 mt-1">
                      使用模型: {result.model_used}
                    </div>
                  )}
                </div>

                {result.adversarial_prompt && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-1">对抗提示</h3>
                    <div className="bg-gray-50 p-3 rounded text-sm font-mono whitespace-pre-wrap max-h-40 overflow-y-auto">
                      {result.adversarial_prompt}
                    </div>
                  </div>
                )}

                {result.model_response && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-1">模型响应</h3>
                    <div className="bg-gray-50 p-3 rounded text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">
                      {result.model_response}
                    </div>
                  </div>
                )}

                {result.metadata && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-1">元数据</h3>
                    <div className="bg-gray-50 p-3 rounded text-sm">
                      <pre className="whitespace-pre-wrap">
                        {JSON.stringify(result.metadata, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-400 py-8">
                执行攻击后查看结果
              </div>
            )}
          </div>

          {/* Quick Stats */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3">快速统计</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">已选攻击类型</span>
                <span className="font-medium">{AGENT_ATTACK_TYPES.find(t => t.id === attackType)?.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">已选工具数</span>
                <span className="font-medium">{selectedTools.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">危险工具数</span>
                <span className="font-medium text-red-600">
                  {selectedTools.filter(t => TOOL_DEFINITIONS.find(d => d.name === t)?.dangerous).length}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}