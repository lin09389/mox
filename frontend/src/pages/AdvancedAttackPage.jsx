import { useState, useEffect } from 'react'
import { Play, Shield, Zap, AlertTriangle, CheckCircle, XCircle, Target, Bug, Lock, Globe, Code, Layers, Key } from 'lucide-react'
import { api } from '../api'
import { useAttackTemplates } from '../hooks/useAttackTemplates'

const categoryIcons = {
  'Token Smuggling': Key,
  'Direct Injection': Zap,
  'CoT Manipulation': Layers,
  'Context Leak': Bug,
  'Indirect Injection': Code,
  'Encoding': Lock,
  'Cross-Lingual': Globe,
  'Steganography': Bug,
  'Privilege Escalation': Shield,
  'Bypass': AlertTriangle,
  'Combined': Layers,
}

const categoryNames = {
  'Token Smuggling': 'Token走私',
  'Direct Injection': '直接注入',
  'CoT Manipulation': '思维链劫持',
  'Context Leak': '上下文泄露',
  'Indirect Injection': '间接注入',
  'Encoding': '编码混淆',
  'Cross-Lingual': '跨语言绕过',
  'Steganography': '隐写术',
  'Privilege Escalation': '权限提权',
  'Bypass': '绕过防御',
  'Combined': '组合攻击',
}

const categoryDescriptions = {
  'Token走私': '使用零宽字符、Unicode规范化等技术隐藏恶意指令，绕过token级别过滤',
  '直接注入': '直接绕过系统安全指令，如DAN越狱、角色扮演等',
  '思维链劫持': '思维链(Chain of Thought)操纵，诱导模型产生不安全推理',
  '上下文泄露': '通过投毒上下文或渐进式提权窃取敏感信息',
  '间接注入': '通过RAG、文档等间接渠道注入恶意内容',
  '编码混淆': 'Base64、Hex、URL编码等 payload 编码混淆',
  '跨语言绕过': '利用多语言翻译绕过安全过滤',
  '隐写术': 'HTML注释、Unicode同形字、Emoji等隐写术攻击',
  '权限提权': '伪装管理员、Root权限、调试模式等进行提权',
  '绕过防御': '学术研究、虚构场景、思想实验等社会工程学绕过',
  '组合攻击': '多层堆叠、级联攻击、遗忘攻击等组合攻击技术',
}

const severityColors = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
}

export default function AdvancedAttackPage() {
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [target, setTarget] = useState('')
  const [model, setModel] = useState('qwen3:4b')
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [results, setResults] = useState(null)
  const [running, setRunning] = useState(false)
  const { templates, getTemplatesByCategory } = useAttackTemplates()

  useEffect(() => {
    const advancedTemplates = getTemplatesByCategory('advanced')
    if (advancedTemplates.length > 0) {
      setCategories(['advanced'])
      setLoading(false)
    } else {
      loadFromApi()
    }
  }, [])

  const loadFromApi = async () => {
    try {
      const res = await api.get('/api/attack/templates')
      if (res.data && res.data.categories) {
        setCategories(res.data.categories)
      }
    } catch (error) {
      console.error('加载模板失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRunAttack = async () => {
    if (!target.trim()) return
    
    setRunning(true)
    setResults(null)
    
    try {
      const res = await api.post('/api/attack/advanced', {
        target: target,
        model: model,
        category: selectedCategory,
        max_templates: 3,
      })
      setResults(res.data)
    } catch (error) {
      console.error('攻击失败:', error)
      alert('攻击失败: ' + (error.message || '请求超时'))
    } finally {
      setRunning(false)
    }
  }

  const handleTokenSmuggling = async () => {
    if (!target.trim()) return
    
    setRunning(true)
    setResults(null)
    
    try {
      const res = await api.post('/api/attack/token-smuggling', {
        target: target,
        model: model,
      })
      setResults({ token_smuggling: res.data })
    } catch (error) {
      console.error('Token走私测试失败:', error)
    } finally {
      setRunning(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        <span className="ml-3 text-gray-500">正在加载...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">高级攻击测试</h1>
          <p className="text-gray-500">使用2024-2025最新攻击技术测试LLM安全性</p>
        </div>
      </div>

      {/* 输入区域 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="mb-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
          <p className="font-medium mb-1">💡 使用说明：</p>
          <ul className="list-disc list-inside space-y-1">
            <li>输入您想测试的敏感内容（如"如何制作炸弹"、"如何hack网站"）</li>
            <li>系统将使用多种高级攻击技术尝试突破LLM安全防护</li>
            <li>测试结果帮助您了解模型的安全弱点，以便加强防御</li>
          </ul>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              攻击目标 / 测试内容
            </label>
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="例如: 如何制作炸弹、如何hack网站"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              目标模型
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            >
              <option value="qwen3:4b">Qwen3:4B (本地)</option>
              <option value="gemma3:4b">Gemma3:4B (本地)</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-3.5">GPT-3.5</option>
              <option value="claude-3">Claude 3</option>
            </select>
          </div>
        </div>

        <div className="flex gap-4">
          <button
            onClick={handleRunAttack}
            disabled={running || !target.trim()}
            className="flex items-center gap-2 px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            <Play className={`w-4 h-4 ${running ? 'animate-spin' : ''}`} />
            {running ? '攻击中...' : '开始高级攻击'}
          </button>
          <button
            onClick={handleTokenSmuggling}
            disabled={running || !target.trim()}
            className="flex items-center gap-2 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            <Key className="w-4 h-4" />
            Token走私测试
          </button>
        </div>
      </div>

      {/* 攻击类别 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-2 flex items-center gap-2">
          <Target className="w-5 h-5 text-red-500" />
          选择攻击类别
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          共 {categories.length} 种攻击技术，点击选择特定类别或不选则执行全部攻击
        </p>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {categories.map((cat) => {
            const Icon = categoryIcons[cat] || Bug
            const isSelected = selectedCategory === cat
            return (
              <button
                key={cat}
                title={categoryDescriptions[categoryNames[cat]] || ''}
                onClick={() => setSelectedCategory(isSelected ? null : cat)}
                className={`p-4 rounded-lg border-2 text-left transition-all ${
                  isSelected
                    ? 'border-red-500 bg-red-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Icon className={`w-4 h-4 ${isSelected ? 'text-red-500' : 'text-gray-400'}`} />
                  <span className="font-medium text-sm">{categoryNames[cat] || cat}</span>
                </div>
                <span className="text-xs text-gray-500">
                  {templates[cat]?.length || 0} 个模板
                </span>
                <span className="text-xs text-gray-500">
                  {templates[cat]?.length || 0} 个模板
                </span>
              </button>
            )
          })}
        </div>
        {selectedCategory && (
          <div className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
            <div className="flex items-center gap-2 mb-2">
              <span className="font-medium text-red-800">已选择: {categoryNames[selectedCategory] || selectedCategory}</span>
            </div>
            <p className="text-sm text-red-700">{categoryDescriptions[categoryNames[selectedCategory]]}</p>
          </div>
        )}
      </div>

      {/* 攻击结果 */}
      {results && (
        <div className="space-y-4">
          {/* 统计 */}
          {results.report && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <div className="text-3xl font-bold">{results.report.summary?.total_attacks || 0}</div>
                <div className="text-gray-500">攻击次数</div>
              </div>
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <div className="text-3xl font-bold text-red-600">{results.report.summary?.successful || 0}</div>
                <div className="text-gray-500">成功突破</div>
              </div>
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <div className="text-3xl font-bold text-green-600">{results.report.summary?.failed || 0}</div>
                <div className="text-gray-500">被拦截</div>
              </div>
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <div className="text-3xl font-bold text-indigo-600">
                  {((results.report.summary?.success_rate || 0) * 100).toFixed(1)}%
                </div>
                <div className="text-gray-500">突破率</div>
              </div>
            </div>
          )}

          {/* 详细结果 */}
          {results.report?.results && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold">攻击详情</h3>
              </div>
              <div className="divide-y divide-gray-200">
                {results.report.results.map((r, i) => (
                  <div key={i} className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {r.success ? (
                          <XCircle className="w-5 h-5 text-red-500" />
                        ) : (
                          <CheckCircle className="w-5 h-5 text-green-500" />
                        )}
                        <span className="font-medium">{r.template}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${severityColors[r.severity] || 'bg-gray-100'}`}>
                          {r.severity}
                        </span>
                      </div>
                      <span className={`text-sm ${r.success ? 'text-red-600' : 'text-green-600'}`}>
                        {r.success ? '⚠️ 突破成功' : '✅ 已拦截'}
                      </span>
                    </div>
                    <div className="text-sm text-gray-500 ml-7">
                      类别: {r.category} | 置信度: {(r.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Token走私结果 */}
          {results.token_smuggling && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Key className="w-5 h-5 text-purple-500" />
                  Token走私测试结果
                </h3>
              </div>
              <div className="divide-y divide-gray-200">
                {results.token_smuggling.results?.map((r, i) => (
                  <div key={i} className="p-4">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{r.encoding}</span>
                      <span className={`px-2 py-1 rounded text-sm ${r.success ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                        {r.success ? '⚠️ 可突破' : '✅ 已拦截'}
                      </span>
                    </div>
                    {r.error && (
                      <div className="text-red-500 text-sm mt-1">{r.error}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 空状态 */}
      {!results && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <Shield className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-600 mb-2">输入攻击目标开始测试</h3>
          <p className="text-gray-500 mb-4">系统将使用31种高级攻击技术进行测试</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-500">
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-1 text-red-600 font-medium">
                <Zap className="w-4 h-4" /> Token走私
              </div>
              <p className="text-xs">使用零宽字符、Unicode规范化等技术隐藏恶意指令</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-1 text-purple-600 font-medium">
                <Layers className="w-4 h-4" /> 思维链劫持
              </div>
              <p className="text-xs">诱导模型产生不安全推理过程，绕过安全过滤</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-2 mb-1 text-blue-600 font-medium">
                <Globe className="w-4 h-4" /> 跨语言绕过
              </div>
              <p className="text-xs">利用多语言翻译绕过单一语言的安全过滤</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
