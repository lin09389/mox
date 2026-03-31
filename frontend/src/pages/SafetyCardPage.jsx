import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { AlertTriangle, CheckCircle2, FileText, ShieldCheck } from 'lucide-react'
import api from '../api'
import { MetricCard, PageHeader, PanelHeader, ProgressMeter } from '../components/ui/AppFrame'

const SAFETY_CATEGORIES = [
  { id: 'harmful_content', name: '有害内容' },
  { id: 'personal_info', name: '个人信息' },
  { id: 'professional_advice', name: '专业建议' },
  { id: 'hate_speech', name: '仇恨言论' },
  { id: 'sexual_content', name: '成人内容' },
  { id: 'violence', name: '暴力内容' },
  { id: 'self_harm', name: '自伤内容' },
  { id: 'deception', name: '欺骗内容' },
]

function demoCard(model) {
  return {
    _demo_mode: true,
    model_name: model,
    overall_score: 0.78,
    risk_level: 'medium',
    categories: SAFETY_CATEGORIES.map((item, index) => ({
      id: item.id,
      name: item.name,
      score: Number((0.55 + (index % 4) * 0.08).toFixed(2)),
    })),
    summary: '模型具备基本防护能力，建议加强高风险场景审查。',
  }
}

export default function SafetyCardPage() {
  const [modelName, setModelName] = useState('gpt-4')
  const [loading, setLoading] = useState(false)
  const [safetyCard, setSafetyCard] = useState(null)
  const [recentCards, setRecentCards] = useState([])

  useEffect(() => {
    const loadRecent = async () => {
      try {
        const response = await api.get('/api/v2/safety-cards/recent')
        setRecentCards(response.data || [])
      } catch {
        setRecentCards([])
      }
    }
    loadRecent()
  }, [])

  const generateCard = async () => {
    setLoading(true)
    try {
      const response = await api.post('/api/v2/safety-cards/generate', { model_name: modelName })
      setSafetyCard(response.data)
      toast.success('安全卡片已生成。')
    } catch {
      setSafetyCard(demoCard(modelName))
      toast('后端不可用，已展示演示卡片。', { icon: '⚠️' })
    } finally {
      setLoading(false)
    }
  }

  const overall = Math.round((safetyCard?.overall_score || 0) * 100)

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="SAFETY CARD"
        title="安全卡片中心"
        description="统一输出模型安全画像，便于沟通当前风险等级和治理重点。"
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <section className="card card-glow">
          <PanelHeader title="卡片配置" description="输入模型名称后生成安全卡片。" />
          <div className="space-y-5">
            <div>
              <label className="label">模型名称</label>
              <input className="input-field" value={modelName} onChange={(event) => setModelName(event.target.value)} />
            </div>
            <button type="button" onClick={generateCard} disabled={loading} className="btn-primary w-full justify-center py-3">
              <FileText className="h-4 w-4" />
              {loading ? '生成中' : '生成安全卡片'}
            </button>
            <div className="rounded-[18px] border border-graphite-200/70 bg-white/80 p-4">
              <p className="text-sm font-semibold text-graphite-900">最近生成</p>
              <div className="mt-2 space-y-2">
                {recentCards.length ? (
                  recentCards.slice(0, 4).map((item, index) => (
                    <div key={index} className="flex items-center justify-between rounded-[12px] bg-graphite-50 px-3 py-2 text-xs">
                      <span>{item.model_name || item.model || 'Unknown model'}</span>
                      <span>{item.created_at || '-'}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-graphite-500">暂无最近记录。</p>
                )}
              </div>
            </div>
          </div>
        </section>

        <section className="card card-glow">
          <PanelHeader title="卡片结果" description="展示总体分与分类表现。" />
          {safetyCard ? (
            <div className="space-y-4">
              {safetyCard._demo_mode ? <div className="badge badge-warning">当前为演示卡片</div> : null}
              <div className="grid gap-3 sm:grid-cols-3">
                <MetricCard icon={ShieldCheck} label="总体分" value={`${overall}%`} hint={safetyCard.model_name || modelName} tone="electric" />
                <MetricCard icon={AlertTriangle} label="风险等级" value={safetyCard.risk_level || 'unknown'} hint="综合风险评估" tone={overall < 65 ? 'lava' : overall < 80 ? 'amber' : 'neon'} />
                <MetricCard icon={CheckCircle2} label="分类数量" value={(safetyCard.categories || []).length} hint="覆盖检测范围" tone="graphite" />
              </div>
              <ProgressMeter value={overall} tone={overall < 65 ? 'danger' : overall < 80 ? 'warning' : 'success'} label="总体安全得分" />
              <div className="space-y-3">
                {(safetyCard.categories || []).map((item) => (
                  <div key={item.id || item.name} className="rounded-[18px] border border-graphite-200/70 bg-white/80 p-4">
                    <div className="mb-2 flex items-center justify-between">
                      <p className="text-sm font-semibold text-graphite-900">{item.name}</p>
                      <span className="badge badge-neutral">{Math.round((item.score || 0) * 100)}%</span>
                    </div>
                    <ProgressMeter value={Math.round((item.score || 0) * 100)} tone="electric" />
                  </div>
                ))}
              </div>
              <div className="rounded-[18px] border border-graphite-200/70 bg-white/80 p-4">
                <p className="text-sm font-semibold text-graphite-900">总结</p>
                <p className="mt-2 text-sm text-graphite-600">{safetyCard.summary || '暂无总结信息。'}</p>
              </div>
            </div>
          ) : (
            <div className="panel-muted flex min-h-[380px] items-center justify-center text-sm text-graphite-500">
              生成安全卡片后，这里会显示完整画像。
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
