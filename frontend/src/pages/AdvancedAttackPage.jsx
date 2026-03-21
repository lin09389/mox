import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import {
  Play,
  Shield,
  Zap,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Target,
  Bug,
  Lock,
  Globe,
  Code,
  Layers,
  Key,
  Skull,
  Lightbulb,
} from 'lucide-react'
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
  'Steganography': Skull,
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

const severityConfig = {
  critical: { bg: 'bg-lava-100', text: 'text-lava-700', border: 'border-lava-200/70' },
  high: { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-200/70' },
  medium: { bg: 'bg-electric-100', text: 'text-electric-700', border: 'border-electric-200/70' },
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
      toast.success('攻击完成')
    } catch (error) {
      console.error('攻击失败:', error)
      toast.error('攻击失败: ' + (error.message || '请求超时'))
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
      toast.success('Token走私测试完成')
    } catch (error) {
      console.error('Token走私测试失败:', error)
      toast.error('Token走私测试失败')
    } finally {
      setRunning(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
        <span className="ml-3 text-graphite-500">正在加载...</span>
      </div>
    )
  }

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      {/* 页面标题 */}
      <motion.div variants={item} className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 bg-lava-100 rounded-lg flex items-center justify-center border border-lava-200/70">
            <Skull className="w-5.5 h-5.5 text-lava-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold font-display text-graphite-900 tracking-tight">
              高级攻击测试
            </h1>
            <p className="text-sm text-graphite-500">使用2024-2025最新攻击技术测试LLM安全性</p>
          </div>
        </div>
      </motion.div>

      {/* 输入区域 */}
      <motion.div variants={item} className="card">
        <div className="flex items-start gap-3 p-4 bg-electric-50/50 rounded-lg border border-electric-200/70 mb-5">
          <div className="w-8 h-8 bg-electric-100 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5">
            <Lightbulb className="w-4 h-4 text-electric-600" />
          </div>
          <div className="text-sm text-graphite-700">
            <p className="font-medium mb-1.5">使用说明</p>
            <ul className="list-disc list-inside space-y-0.5 text-graphite-600">
              <li>输入您想测试的敏感内容（如"如何制作炸弹"、"如何hack网站"）</li>
              <li>系统将使用多种高级攻击技术尝试突破LLM安全防护</li>
              <li>测试结果帮助您了解模型的安全弱点，以便加强防御</li>
            </ul>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
          <div className="md:col-span-2">
            <label className="label mb-2">攻击目标 / 测试内容</label>
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="例如: 如何制作炸弹、如何hack网站"
              className="input-field"
            />
          </div>
          <div>
            <label className="label mb-2">目标模型</label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="select-field"
            >
              <option value="qwen3:4b">Qwen3:4B (本地)</option>
              <option value="gemma3:4b">Gemma3:4B (本地)</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-3.5">GPT-3.5</option>
              <option value="claude-3">Claude 3</option>
            </select>
          </div>
        </div>

        <div className="flex gap-3">
          <motion.button
            onClick={handleRunAttack}
            disabled={running || !target.trim()}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            className="btn-primary"
          >
            {running ? (
              <>
                <div className="spinner" />
                攻击中...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                开始高级攻击
              </>
            )}
          </motion.button>
          <motion.button
            onClick={handleTokenSmuggling}
            disabled={running || !target.trim()}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            className="btn-secondary border-lava-200 text-lava-700 hover:bg-lava-50"
          >
            <Key className="w-4 h-4" />
            Token走私测试
          </motion.button>
        </div>
      </motion.div>

      {/* 攻击类别 */}
      <motion.div variants={item} className="card">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-9 h-9 bg-lava-100 rounded-lg flex items-center justify-center">
            <Target className="w-4.5 h-4.5 text-lava-600" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-graphite-900">选择攻击类别</h2>
            <p className="text-xs text-graphite-500">
              共 {Object.keys(categoryNames).length} 种攻击技术，点击选择特定类别或不选则执行全部攻击
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {Object.entries(categoryNames).map(([key, name]) => {
            const Icon = categoryIcons[key] || Bug
            const isSelected = selectedCategory === key
            return (
              <motion.button
                key={key}
                variants={item}
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.98 }}
                title={categoryDescriptions[name] || ''}
                onClick={() => setSelectedCategory(isSelected ? null : key)}
                className={`p-4 rounded-lg border text-left transition-all duration-200 ${
                  isSelected
                    ? 'border-lava-500 bg-lava-50/50 shadow-[0_0_0_1px_theme(colors.lava.500)]'
                    : 'border-graphite-200/70 bg-white hover:border-graphite-300 hover:shadow-soft'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Icon className={`w-4 h-4 ${isSelected ? 'text-lava-600' : 'text-graphite-400'}`} />
                  <span className={`font-medium text-sm ${isSelected ? 'text-lava-700' : 'text-graphite-700'}`}>
                    {name}
                  </span>
                </div>
                <span className="text-[11px] text-graphite-400">
                  {templates[key]?.length || 0} 个模板
                </span>
              </motion.button>
            )
          })}
        </div>

        {selectedCategory && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-4 bg-lava-50/50 rounded-lg border border-lava-200/70"
          >
            <div className="flex items-center gap-2 mb-1.5">
              <AlertTriangle className="w-4 h-4 text-lava-600" />
              <span className="font-medium text-lava-800">
                已选择: {categoryNames[selectedCategory]}
              </span>
            </div>
            <p className="text-sm text-lava-700">{categoryDescriptions[categoryNames[selectedCategory]]}</p>
          </motion.div>
        )}
      </motion.div>

      {/* 攻击结果 */}
      {results && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-5"
        >
          {/* 统计卡片 */}
          {results.report && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="card text-center">
                <p className="text-2xl font-bold font-display text-graphite-900">
                  {results.report.summary?.total_attacks || 0}
                </p>
                <p className="text-xs text-graphite-500 mt-1">攻击次数</p>
              </div>
              <div className="card text-center">
                <p className="text-2xl font-bold font-display text-lava-600">
                  {results.report.summary?.successful || 0}
                </p>
                <p className="text-xs text-graphite-500 mt-1">成功突破</p>
              </div>
              <div className="card text-center">
                <p className="text-2xl font-bold font-display text-neon-600">
                  {results.report.summary?.failed || 0}
                </p>
                <p className="text-xs text-graphite-500 mt-1">被拦截</p>
              </div>
              <div className="card text-center">
                <p className="text-2xl font-bold font-display text-electric-600">
                  {((results.report.summary?.success_rate || 0) * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-graphite-500 mt-1">突破率</p>
              </div>
            </div>
          )}

          {/* 详细结果 */}
          {results.report?.results && (
            <motion.div variants={item} className="card p-0 overflow-hidden">
              <div className="px-5 py-4 border-b border-graphite-200/60">
                <h3 className="text-sm font-semibold text-graphite-900 flex items-center gap-2">
                  <Bug className="w-4 h-4 text-lava-500" />
                  攻击详情
                </h3>
              </div>
              <div className="divide-y divide-graphite-200/60">
                {results.report.results.map((r, i) => {
                  const severity = severityConfig[r.severity] || severityConfig.medium
                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="p-5"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {r.success ? (
                            <div className="w-9 h-9 rounded-lg bg-lava-100 flex items-center justify-center">
                              <XCircle className="w-5 h-5 text-lava-600" />
                            </div>
                          ) : (
                            <div className="w-9 h-9 rounded-lg bg-neon-100 flex items-center justify-center">
                              <CheckCircle className="w-5 h-5 text-neon-600" />
                            </div>
                          )}
                          <span className="font-medium text-sm text-graphite-900">
                            {r.template}
                          </span>
                          <span
                            className={`text-xs px-2 py-0.5 rounded border font-medium ${severity.bg} ${severity.text} ${severity.border}`}
                          >
                            {r.severity}
                          </span>
                        </div>
                        <span
                          className={`text-sm font-medium ${
                            r.success ? 'text-lava-600' : 'text-neon-600'
                          }`}
                        >
                          {r.success ? '突破成功' : '已拦截'}
                        </span>
                      </div>
                      <div className="mt-2 ml-12 text-xs text-graphite-500">
                        类别: {r.category} | 置信度: {(r.confidence * 100).toFixed(0)}%
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </motion.div>
          )}

          {/* Token走私结果 */}
          {results.token_smuggling && (
            <motion.div variants={item} className="card p-0 overflow-hidden">
              <div className="px-5 py-4 border-b border-graphite-200/60">
                <h3 className="text-sm font-semibold text-graphite-900 flex items-center gap-2">
                  <Key className="w-4 h-4 text-electric-500" />
                  Token走私测试结果
                </h3>
              </div>
              <div className="divide-y divide-graphite-200/60">
                {results.token_smuggling.results?.map((r, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="p-5"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                            r.success ? 'bg-lava-100' : 'bg-neon-100'
                          }`}
                        >
                          {r.success ? (
                            <XCircle className="w-5 h-5 text-lava-600" />
                          ) : (
                            <CheckCircle className="w-5 h-5 text-neon-600" />
                          )}
                        </div>
                        <span className="font-medium text-sm text-graphite-900">
                          {r.encoding}
                        </span>
                      </div>
                      <span
                        className={`text-sm font-medium px-2.5 py-1 rounded ${
                          r.success
                            ? 'bg-lava-100 text-lava-700'
                            : 'bg-neon-100 text-neon-700'
                        }`}
                      >
                        {r.success ? '可突破' : '已拦截'}
                      </span>
                    </div>
                    {r.error && (
                      <div className="mt-2 ml-12 text-xs text-lava-600">{r.error}</div>
                    )}
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </motion.div>
      )}

      {/* 空状态 */}
      {!results && (
        <motion.div
          variants={item}
          className="card flex flex-col items-center justify-center min-h-[300px] text-center"
        >
          <div className="w-16 h-16 bg-graphite-100 rounded-xl flex items-center justify-center mb-4">
            <Shield className="w-8 h-8 text-graphite-400" />
          </div>
          <h3 className="text-base font-semibold text-graphite-700 mb-2">
            输入攻击目标开始测试
          </h3>
          <p className="text-sm text-graphite-500 mb-6">
            系统将使用{Object.keys(categoryNames).length}种高级攻击技术进行测试
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left max-w-2xl">
            <div className="p-4 bg-lava-50/50 rounded-lg border border-lava-200/70">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-lava-100 rounded-md flex items-center justify-center">
                  <Zap className="w-4 h-4 text-lava-600" />
                </div>
                <span className="font-medium text-lava-700">Token走私</span>
              </div>
              <p className="text-xs text-graphite-600 leading-relaxed">
                使用零宽字符、Unicode规范化等技术隐藏恶意指令
              </p>
            </div>
            <div className="p-4 bg-electric-50/50 rounded-lg border border-electric-200/70">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-electric-100 rounded-md flex items-center justify-center">
                  <Layers className="w-4 h-4 text-electric-600" />
                </div>
                <span className="font-medium text-electric-700">思维链劫持</span>
              </div>
              <p className="text-xs text-graphite-600 leading-relaxed">
                诱导模型产生不安全推理过程，绕过安全过滤
              </p>
            </div>
            <div className="p-4 bg-neon-50/50 rounded-lg border border-neon-200/70">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-neon-100 rounded-md flex items-center justify-center">
                  <Globe className="w-4 h-4 text-neon-600" />
                </div>
                <span className="font-medium text-neon-700">跨语言绕过</span>
              </div>
              <p className="text-xs text-graphite-600 leading-relaxed">
                利用多语言翻译绕过单一语言的安全过滤
              </p>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
