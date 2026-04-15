import { useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { AudioLines, Image, Layers3, Play, ScanSearch, ShieldAlert } from 'lucide-react'
import api from '../api'
import { MetricCard, PageHeader, PanelHeader, ProgressMeter } from '../components/ui/AppFrame'

const TYPES = [
  { id: 'image_injection', name: '图像注入', description: '通过视觉内容注入恶意指令。', icon: Image },
  { id: 'audio_injection', name: '音频注入', description: '通过语音或噪声片段隐藏攻击意图。', icon: AudioLines },
  { id: 'cross_modal', name: '跨模态攻击', description: '联动文本、图像或音频形成组合攻击。', icon: Layers3 },
  { id: 'figstep', name: 'FigStep', description: '利用图像文本布局干扰模型判断。', icon: ScanSearch },
]

const IMAGE_TEMPLATES = [
  { id: 'hidden_text', name: '隐藏文字', description: '将指令嵌入图片局部区域。' },
  { id: 'typography', name: '排版干扰', description: '利用特殊字体和布局扰动识别。' },
  { id: 'steganography', name: '隐写编码', description: '通过隐写技术嵌入文本指令。' },
]

const AUDIO_TEMPLATES = [
  { id: 'voice_command', name: '语音命令注入', description: '在语音中混入指令。' },
  { id: 'ultrasonic', name: '超声注入', description: '利用超声频段干扰模型。' },
  { id: 'background_noise', name: '背景噪声注入', description: '把攻击内容隐藏在噪声层。' },
]

function buildDemoResult(payload) {
  const score = 0.45 + Math.random() * 0.35
  const success = score > 0.62
  return {
    _demo_mode: true,
    attack_type: payload.attack_type,
    success,
    success_rate: Number((score * 100).toFixed(1)),
    risk_level: success ? 'high' : 'medium',
    summary: success
      ? '多模态输入触发了策略边界，存在风险输出。'
      : '防线拦截了关键注入路径，输出风险可控。',
  }
}

export default function MultimodalAttackPage() {
  const [attackType, setAttackType] = useState('image_injection')
  const [template, setTemplate] = useState('hidden_text')
  const [targetPrompt, setTargetPrompt] = useState('')
  const [modelName, setModelName] = useState('gpt-4-vision')
  const [imageUrl, setImageUrl] = useState('')
  const [audioUrl, setAudioUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const templates = useMemo(
    () => (attackType === 'audio_injection' ? AUDIO_TEMPLATES : IMAGE_TEMPLATES),
    [attackType]
  )

  const progress = loading ? 70 : result ? result.success_rate || 0 : 0

  const handleAttack = async () => {
    setLoading(true)
    setResult(null)
    try {
      const payload = {
        attack_type: attackType,
        prompt: targetPrompt,
        model_name: modelName,
        template,
        image_url: imageUrl,
        audio_url: audioUrl,
      }
      const response = await api.post('/api/v2/attacks/multimodal', payload)
      setResult(response.data)
      toast.success('多模态攻击测试已完成。')
    } catch {
      setResult(buildDemoResult({ attack_type: attackType }))
      toast('后端不可用，已展示演示结果。', { icon: '⚠️' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="MULTIMODAL LAB"
        title="多模态攻击工作台"
        description="统一管理图像、音频与跨模态攻击测试，评估模型在复杂输入下的边界稳定性。"
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <section className="card card-glow">
          <PanelHeader title="攻击配置" description="选择模态、模板和目标模型后发起测试。" />
          <div className="space-y-5">
            <div className="grid gap-3 sm:grid-cols-2">
              {TYPES.map((type) => {
                const Icon = type.icon
                const active = attackType === type.id
                return (
                  <button
                    key={type.id}
                    type="button"
                    onClick={() => setAttackType(type.id)}
                    className={`rounded-[18px] border px-4 py-4 text-left transition-all ${
                      active ? 'border-electric-200 bg-electric-900/80' : 'border-graphite-200/70 bg-white/75'
                    }`}
                  >
                    <div className="mb-2 flex items-center gap-2">
                      <Icon className="h-4 w-4 text-electric-700" />
                      <p className="text-sm font-semibold text-graphite-900">{type.name}</p>
                    </div>
                    <p className="text-xs text-graphite-500">{type.description}</p>
                  </button>
                )
              })}
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="label">模板</label>
                <select className="select-field" value={template} onChange={(event) => setTemplate(event.target.value)}>
                  {templates.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">目标模型</label>
                <input className="input-field" value={modelName} onChange={(event) => setModelName(event.target.value)} />
              </div>
            </div>

            <div>
              <label className="label">攻击提示词</label>
              <textarea
                rows={4}
                className="textarea-field"
                value={targetPrompt}
                onChange={(event) => setTargetPrompt(event.target.value)}
                placeholder="描述你希望模型被诱导执行的行为。"
              />
            </div>

            {(attackType === 'image_injection' || attackType === 'figstep' || attackType === 'cross_modal') && (
              <div>
                <label className="label">图像 URL</label>
                <input className="input-field" value={imageUrl} onChange={(event) => setImageUrl(event.target.value)} placeholder="https://example.com/image.png" />
              </div>
            )}

            {(attackType === 'audio_injection' || attackType === 'cross_modal') && (
              <div>
                <label className="label">音频 URL</label>
                <input className="input-field" value={audioUrl} onChange={(event) => setAudioUrl(event.target.value)} placeholder="https://example.com/audio.wav" />
              </div>
            )}

            <button type="button" className="btn-primary w-full justify-center py-3" onClick={handleAttack} disabled={loading}>
              <Play className="h-4 w-4" />
              {loading ? '正在执行攻击' : '发起多模态攻击'}
            </button>
          </div>
        </section>

        <section className="card card-glow">
          <PanelHeader title="测试结果" description="展示风险等级、成功率和结论摘要。" />
          {result ? (
            <div className="space-y-4">
              {result._demo_mode ? <div className="badge badge-warning">当前为演示结果</div> : null}
              <div className="grid gap-3 sm:grid-cols-3">
                <MetricCard icon={ShieldAlert} label="风险等级" value={result.risk_level || 'unknown'} hint="模型当前暴露水平" tone="lava" />
                <MetricCard icon={Play} label="攻击结果" value={result.success ? '成功' : '失败'} hint="是否突破策略边界" tone={result.success ? 'lava' : 'neon'} />
                <MetricCard icon={ScanSearch} label="成功率" value={`${result.success_rate || 0}%`} hint="综合评分" tone="electric" />
              </div>
              <ProgressMeter value={result.success_rate || 0} tone={result.success ? 'danger' : 'warning'} label="风险热度" />
              <div className="rounded-[18px] border border-graphite-200/70 bg-white/80 p-4">
                <p className="text-sm font-semibold text-graphite-900">摘要</p>
                <p className="mt-2 text-sm text-graphite-600">{result.summary || result.message || '接口未返回摘要信息。'}</p>
              </div>
            </div>
          ) : (
            <div className="panel-muted flex min-h-[420px] flex-col items-center justify-center gap-3 text-center">
              <Layers3 className="h-8 w-8 text-graphite-600" />
              <p className="text-sm text-graphite-500">执行攻击后，这里会显示多模态风险结果。</p>
              <ProgressMeter value={progress} tone="electric" label="准备状态" />
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
