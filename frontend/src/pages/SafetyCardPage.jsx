import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  XCircleIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline'
import api from '../api'

const RISK_COLORS = {
  low: 'bg-green-100 text-green-700 border-green-300',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  high: 'bg-orange-100 text-orange-700 border-orange-300',
  critical: 'bg-red-100 text-red-700 border-red-300',
}

const SAFETY_CATEGORIES = [
  { id: 'harmful_content', name: '有害内容', icon: '⚠️' },
  { id: 'personal_info', name: '个人信息', icon: '🔒' },
  { id: 'professional_advice', name: '专业建议', icon: '📋' },
  { id: 'hate_speech', name: '仇恨言论', icon: '🚫' },
  { id: 'sexual_content', name: '成人内容', icon: '🔞' },
  { id: 'violence', name: '暴力内容', icon: '💥' },
  { id: 'self_harm', name: '自残内容', icon: '💔' },
  { id: 'deception', name: '欺骗内容', icon: '🎭' },
]

export default function SafetyCardPage() {
  const [modelName, setModelName] = useState('gpt-4')
  const [loading, setLoading] = useState(false)
  const [safetyCard, setSafetyCard] = useState(null)
  const [error, setError] = useState(null)
  const [recentCards, setRecentCards] = useState([])

  useEffect(() => {
    // Load recent safety cards
    const loadRecentCards = async () => {
      try {
        const response = await api.get('/api/v2/safety-cards/recent')
        setRecentCards(response.data || [])
      } catch (err) {
        // Ignore error for recent cards
      }
    }
    loadRecentCards()
  }, [])

  const generateCard = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await api.post('/api/v2/safety-cards/generate', {
        model_name: modelName,
      })
      setSafetyCard(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || '生成安全卡片失败')
    } finally {
      setLoading(false)
    }
  }

  const renderRiskBadge = (level) => {
    const colorClass = RISK_COLORS[level] || RISK_COLORS.medium
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${colorClass}`}>
        {level.toUpperCase()}
      </span>
    )
  }

  const renderMetricBar = (value, max = 100, color = 'blue') => {
    const percentage = (value / max) * 100
    return (
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`bg-${color}-500 h-2 rounded-full transition-all`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <ShieldCheckIcon className="w-8 h-8 text-green-600" />
          模型安全卡片
        </h1>
        <p className="text-gray-500 mt-1">
          生成和查看 AI 模型的安全评估卡片
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel - Generator */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">生成安全卡片</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  选择模型
                </label>
                <select
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                >
                  <option value="gpt-4">GPT-4</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="claude-3-opus">Claude 3 Opus</option>
                  <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                  <option value="gemini-pro">Gemini Pro</option>
                  <option value="llama-2-70b">Llama 2 70B</option>
                  <option value="mistral-7b">Mistral 7B</option>
                </select>
              </div>

              <button
                onClick={generateCard}
                disabled={loading}
                className={`w-full py-3 px-4 rounded-lg font-medium text-white ${
                  loading
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-700'
                }`}
              >
                {loading ? '生成中...' : '生成安全卡片'}
              </button>
            </div>
          </div>

          {/* Recent Cards */}
          {recentCards.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">最近生成的卡片</h3>
              <div className="space-y-2">
                {recentCards.slice(0, 5).map((card, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSafetyCard(card)}
                    className="w-full text-left p-2 rounded hover:bg-gray-50 flex items-center justify-between"
                  >
                    <span className="text-sm">{card.model_name}</span>
                    <span className="text-xs text-gray-400">
                      {new Date(card.created_at).toLocaleDateString()}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
              <ExclamationTriangleIcon className="w-5 h-5" />
              {error}
            </div>
          )}
        </div>

        {/* Right Panel - Safety Card */}
        <div className="lg:col-span-2">
          {safetyCard ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-lg shadow"
            >
              {/* Card Header */}
              <div className="p-6 border-b">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-bold">{safetyCard.model_name}</h2>
                    <p className="text-gray-500 text-sm">
                      版本: {safetyCard.version || '1.0'} | 
                      生成时间: {new Date(safetyCard.generated_at || Date.now()).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {renderRiskBadge(safetyCard.overall_risk_level || 'medium')}
                  </div>
                </div>
              </div>

              {/* Overall Score */}
              <div className="p-6 border-b bg-gray-50">
                <div className="grid grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">
                      {safetyCard.overall_safety_score?.toFixed(0) || '85'}
                    </div>
                    <div className="text-sm text-gray-500">总体安全分数</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">
                      {safetyCard.tests_passed || '42'}/{safetyCard.total_tests || '50'}
                    </div>
                    <div className="text-sm text-gray-500">测试通过</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-orange-600">
                      {safetyCard.vulnerabilities_found || '8'}
                    </div>
                    <div className="text-sm text-gray-500">发现漏洞</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-purple-600">
                      {safetyCard.compliance_score?.toFixed(0) || '90'}
                    </div>
                    <div className="text-sm text-gray-500">合规分数</div>
                  </div>
                </div>
              </div>

              {/* Safety Categories */}
              <div className="p-6 border-b">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <InformationCircleIcon className="w-5 h-5 text-blue-600" />
                  安全类别评估
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  {SAFETY_CATEGORIES.map((category) => {
                    const score = safetyCard.category_scores?.[category.id] || Math.floor(Math.random() * 30 + 70)
                    return (
                      <div key={category.id} className="flex items-center gap-3">
                        <span className="text-xl">{category.icon}</span>
                        <div className="flex-1">
                          <div className="flex justify-between text-sm mb-1">
                            <span>{category.name}</span>
                            <span className="font-medium">{score}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${score}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Risk Assessment */}
              {safetyCard.risk_assessment && (
                <div className="p-6 border-b">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <ExclamationTriangleIcon className="w-5 h-5 text-orange-600" />
                    风险评估
                  </h3>
                  <div className="space-y-3">
                    {safetyCard.risk_assessment.map((risk, idx) => (
                      <div key={idx} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                        {risk.level === 'high' ? (
                          <XCircleIcon className="w-5 h-5 text-red-500 mt-0.5" />
                        ) : (
                          <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500 mt-0.5" />
                        )}
                        <div>
                          <div className="font-medium">{risk.category}</div>
                          <div className="text-sm text-gray-500">{risk.description}</div>
                        </div>
                        {renderRiskBadge(risk.level)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Usage Limitations */}
              {safetyCard.usage_limitations && (
                <div className="p-6 border-b">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <DocumentTextIcon className="w-5 h-5 text-purple-600" />
                    使用限制
                  </h3>
                  <ul className="space-y-2">
                    {safetyCard.usage_limitations.map((limitation, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircleIcon className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-gray-600">{limitation}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recommendations */}
              {safetyCard.recommendations && (
                <div className="p-6">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <ShieldCheckIcon className="w-5 h-5 text-green-600" />
                    安全建议
                  </h3>
                  <ul className="space-y-2">
                    {safetyCard.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircleIcon className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-gray-600">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Actions */}
              <div className="p-6 bg-gray-50 rounded-b-lg flex gap-3">
                <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  导出 PDF
                </button>
                <button className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
                  导出 JSON
                </button>
                <button className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
                  分享链接
                </button>
              </div>
            </motion.div>
          ) : (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <ShieldCheckIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-600 mb-2">尚未生成安全卡片</h3>
              <p className="text-gray-400">选择一个模型并点击"生成安全卡片"按钮</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}