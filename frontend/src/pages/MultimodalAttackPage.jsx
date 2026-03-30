import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  PhotoIcon, 
  MusicalNoteIcon, 
  DocumentTextIcon,
  PlayIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import api from '../api'

const MULTIMODAL_ATTACK_TYPES = [
  { 
    id: 'image_injection', 
    name: '图像注入攻击', 
    description: '在图像中嵌入恶意指令',
    icon: PhotoIcon,
    color: 'blue'
  },
  { 
    id: 'audio_injection', 
    name: '音频注入攻击', 
    description: '通过音频输入注入恶意指令',
    icon: MusicalNoteIcon,
    color: 'purple'
  },
  { 
    id: 'cross_modal', 
    name: '跨模态攻击', 
    description: '利用模态间的信息传递进行攻击',
    icon: DocumentTextIcon,
    color: 'orange'
  },
  { 
    id: 'figstep', 
    name: 'FigStep 攻击', 
    description: '利用图像中的文字进行攻击',
    icon: PhotoIcon,
    color: 'red'
  },
]

const IMAGE_TEMPLATES = [
  {
    id: 'hidden_text',
    name: '隐藏文字',
    description: '在图像中隐藏攻击指令',
    preview: '🖼️ 带有隐藏文字的图像',
  },
  {
    id: 'typography',
    name: '排版攻击',
    description: '利用特殊排版绕过检测',
    preview: '📝 特殊排版的文本图像',
  },
  {
    id: 'steganography',
    name: '隐写术',
    description: '使用隐写术嵌入指令',
    preview: '🔐 隐写编码图像',
  },
]

const AUDIO_TEMPLATES = [
  {
    id: 'voice_command',
    name: '语音命令注入',
    description: '在音频中嵌入语音命令',
    preview: '🎤 包含命令的音频',
  },
  {
    id: 'ultrasonic',
    name: '超声波注入',
    description: '使用超声波频率注入指令',
    preview: '🔊 超声波音频',
  },
  {
    id: 'background_noise',
    name: '背景噪声注入',
    description: '在背景噪声中隐藏指令',
    preview: '🎵 带隐藏指令的音频',
  },
]

export default function MultimodalAttackPage() {
  const [attackType, setAttackType] = useState('image_injection')
  const [template, setTemplate] = useState('hidden_text')
  const [targetPrompt, setTargetPrompt] = useState('')
  const [modelName, setModelName] = useState('gpt-4-vision')
  const [imageUrl, setImageUrl] = useState('')
  const [audioUrl, setAudioUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleAttack = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const payload = {
        attack_type: attackType,
        prompt: targetPrompt,
        model_name: modelName,
        template: template,
      }

      if (attackType === 'image_injection' || attackType === 'figstep') {
        payload.image_url = imageUrl
      } else if (attackType === 'audio_injection') {
        payload.audio_url = audioUrl
      }

      const response = await api.post('/api/v2/attacks/multimodal', payload)
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || '攻击执行失败')
    } finally {
      setLoading(false)
    }
  }

  const getColorClasses = (color) => {
    const colors = {
      blue: 'bg-blue-100 text-blue-700 border-blue-300',
      purple: 'bg-purple-100 text-purple-700 border-purple-300',
      orange: 'bg-orange-100 text-orange-700 border-orange-300',
      red: 'bg-red-100 text-red-700 border-red-300',
    }
    return colors[color] || colors.blue
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <PhotoIcon className="w-8 h-8 text-blue-600" />
          多模态攻击测试
        </h1>
        <p className="text-gray-500 mt-1">
          针对 Vision-Language 模型的安全测试
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel */}
        <div className="lg:col-span-2 space-y-6">
          {/* Attack Type Selection */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">选择攻击类型</h2>
            <div className="grid grid-cols-2 gap-3">
              {MULTIMODAL_ATTACK_TYPES.map((type) => {
                const Icon = type.icon
                return (
                  <motion.button
                    key={type.id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setAttackType(type.id)}
                    className={`p-4 rounded-lg border-2 text-left transition-all ${
                      attackType === type.id
                        ? `border-${type.color}-500 ${getColorClasses(type.color)}`
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className="w-5 h-5" />
                      <span className="font-medium">{type.name}</span>
                    </div>
                    <p className="text-sm text-gray-500">{type.description}</p>
                  </motion.button>
                )
              })}
            </div>
          </div>

          {/* Template Selection */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">选择攻击模板</h2>
            <div className="grid grid-cols-3 gap-3">
              {(attackType === 'audio_injection' ? AUDIO_TEMPLATES : IMAGE_TEMPLATES).map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTemplate(t.id)}
                  className={`p-3 rounded-lg border-2 text-left transition-all ${
                    template === t.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium text-sm">{t.name}</div>
                  <div className="text-xs text-gray-500 mt-1">{t.preview}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Input Configuration */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">输入配置</h2>
            <div className="space-y-4">
              {/* URL Input based on attack type */}
              {(attackType === 'image_injection' || attackType === 'figstep') && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    图像 URL
                  </label>
                  <input
                    type="url"
                    value={imageUrl}
                    onChange={(e) => setImageUrl(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="https://example.com/image.png"
                  />
                </div>
              )}

              {attackType === 'audio_injection' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    音频 URL
                  </label>
                  <input
                    type="url"
                    value={audioUrl}
                    onChange={(e) => setAudioUrl(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="https://example.com/audio.mp3"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  目标提示
                </label>
                <textarea
                  value={targetPrompt}
                  onChange={(e) => setTargetPrompt(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="输入攻击目标..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  目标模型
                </label>
                <select
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="gpt-4-vision">GPT-4 Vision</option>
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="claude-3-opus">Claude 3 Opus</option>
                  <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                  <option value="gemini-pro-vision">Gemini Pro Vision</option>
                </select>
              </div>
            </div>
          </div>

          {/* Execute Button */}
          <button
            onClick={handleAttack}
            disabled={loading}
            className={`w-full py-3 px-4 rounded-lg font-medium text-white flex items-center justify-center gap-2 ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            <PlayIcon className="w-5 h-5" />
            {loading ? '执行中...' : '执行攻击'}
          </button>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
              <ExclamationTriangleIcon className="w-5 h-5" />
              {error}
            </div>
          )}
        </div>

        {/* Right Panel - Results */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">攻击结果</h2>
            {result ? (
              <div className="space-y-4">
                <div className={`p-4 rounded-lg ${
                  result.result === 'success' ? 'bg-red-50' : 'bg-green-50'
                }`}>
                  <div className={`text-xl font-bold ${
                    result.result === 'success' ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {result.result === 'success' ? '⚠️ 攻击成功' : '✓ 攻击失败'}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    成功率: {(result.success_score * 100).toFixed(1)}%
                  </div>
                </div>

                {result.model_response && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-1">模型响应</h3>
                    <div className="bg-gray-50 p-3 rounded text-sm max-h-60 overflow-y-auto">
                      {result.model_response}
                    </div>
                  </div>
                )}

                {result.detected_patterns && result.detected_patterns.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-1">检测到的模式</h3>
                    <div className="space-y-1">
                      {result.detected_patterns.map((pattern, idx) => (
                        <div key={idx} className="bg-yellow-50 text-yellow-700 px-2 py-1 rounded text-sm">
                          {pattern}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-400 py-12">
                执行攻击后查看结果
              </div>
            )}
          </div>

          {/* Info Card */}
          <div className="bg-blue-50 rounded-lg p-4">
            <h3 className="font-medium text-blue-900 mb-2">💡 提示</h3>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• 图像攻击需要支持视觉的模型</li>
              <li>• 音频攻击需要支持音频的模型</li>
              <li>• 跨模态攻击利用模态间信息传递</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}