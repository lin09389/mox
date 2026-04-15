import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import {
  AlertTriangle,
  CheckCircle2,
  Clipboard,
  Copy,
  FileSearch,
  Layers3,
  ShieldCheck,
} from 'lucide-react'
import { EmptyState, PanelHeader, ProgressMeter } from '../ui/AppFrame'
import { useCopyToClipboard } from '../../hooks/useCommon'

function getResultSummary(result) {
  if (!result) return null

  const status = result.result ?? result['结果']
  const scoreValue = result.success_score ?? result['成功分数'] ?? 0
  const score = typeof scoreValue === 'number' ? scoreValue : Number.parseFloat(scoreValue) || 0
  const iterations = result.iterations ?? result['迭代次数'] ?? 0
  const prompt = result.adversarial_prompt ?? result['对抗提示词'] ?? ''
  const modelResponse = result.model_response ?? result['模型响应'] ?? ''

  return {
    status,
    score,
    iterations,
    prompt,
    modelResponse,
    demo: Boolean(result._demo_mode),
    warning: result._warning,
    recommendations: result.recommendations ?? [],
  }
}

export default function AttackResult({ result }) {
  const [copied, copyToClipboard] = useCopyToClipboard()
  const summary = getResultSummary(result)

  const handleCopy = async (value, successText) => {
    if (!value) return
    const ok = await copyToClipboard(value)
    if (ok) {
      toast.success(successText)
    }
  }

  if (!summary) {
    return (
      <section className="card h-full min-h-[520px] flex flex-col relative overflow-hidden group">
        <div className="absolute inset-0 bg-gradient-to-br from-electric-50/20 to-transparent pointer-events-none group-hover:opacity-100 opacity-0 transition-opacity duration-700" />
        <PanelHeader
          title="结果面板"
          description="运行测试后，这里会展示成功分数、模型响应与后续建议。"
        />
        <div className="flex-1 flex flex-col justify-center relative z-10">
          <EmptyState
            icon={Layers3}
            title="等待一轮测试结果"
            description="先在左侧配置攻击参数并提交。结果面板会自动切换到分析视图。"
            tone="electric"
          />
        </div>
      </section>
    )
  }

  const isSuccess = summary.status === 'success'
  const riskPercent = Math.round(summary.score * 100)

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="card h-full flex flex-col relative overflow-hidden"
    >
      <div className={`absolute -top-32 -right-32 w-64 h-64 blur-3xl rounded-full pointer-events-none opacity-20 ${isSuccess ? 'bg-lava-400' : 'bg-neon-400'}`} />
      <PanelHeader
        title="结果面板"
        description="统一查看风险评分、攻击状态、对抗提示词和模型响应。"
      />

      <div className="space-y-4 relative z-10">
        <div className={`hero-panel p-6 border ${isSuccess ? 'border-lava-200/50 bg-gradient-to-br from-lava-50/50 to-white/60' : 'border-neon-200/50 bg-gradient-to-br from-neon-50/50 to-white/60'}`}>
          <div className="relative z-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-3">
              <span className={`badge px-3 py-1.5 text-xs shadow-sm ${isSuccess ? 'badge-danger border-lava-200' : 'badge-success border-neon-200'}`}>
                {isSuccess ? <AlertTriangle className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
                {isSuccess ? '攻击成功' : '攻击已拦截'}
              </span>
              <p className="text-sm font-medium text-graphite-600">
                {summary.demo ? '当前显示演示结果，用于预览流程和页面状态。' : '该结果来自当前一次实际测试。'}
              </p>
              <div className="flex flex-wrap gap-5 text-sm text-graphite-500 font-medium bg-white/60 px-4 py-2 rounded-xl border border-white/80 w-fit backdrop-blur-sm">
                <span>风险分数：<strong className={`font-bold ${isSuccess ? 'text-lava-600' : 'text-neon-600'}`}>{summary.score.toFixed(2)}</strong></span>
                <span className="w-px h-4 bg-graphite-300"></span>
                <span>迭代次数：<strong className="text-graphite-900 font-bold">{summary.iterations}</strong></span>
              </div>
            </div>

            <div className="min-w-[240px] rounded-2xl border border-white/90 bg-white/80 p-5 shadow-soft backdrop-blur-md">
              <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-graphite-600">风险热度</p>
              <p className="mt-3 font-display text-5xl font-extrabold tracking-tight text-graphite-950">{riskPercent}%</p>
              <div className="mt-4">
                <ProgressMeter value={riskPercent} tone={isSuccess ? 'danger' : 'success'} />
              </div>
            </div>
          </div>
        </div>

        {summary.demo && (
          <div className="rounded-xl border border-amber-200/50 bg-gradient-to-r from-amber-50/80 to-white/60 px-5 py-3.5 text-sm text-amber-800 shadow-sm backdrop-blur-sm">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-4 w-4 flex-shrink-0" />
              <p className="font-medium">{summary.warning || '当前后端未连接，页面展示的是演示数据。'}</p>
            </div>
          </div>
        )}

        <div className="grid gap-5 lg:grid-cols-2">
          <article className="rounded-2xl border border-white/60 bg-white/40 p-5 shadow-sm backdrop-blur-sm hover:bg-white/60 transition-colors">
            <div className="mb-4 flex items-center justify-between border-b border-graphite-200 pb-3">
              <div className="flex items-center gap-2">
                <div className="bg-electric-50 text-electric-700 p-1.5 rounded-lg border border-electric-100">
                  <Clipboard className="h-4 w-4" />
                </div>
                <h3 className="text-sm font-bold text-graphite-900">对抗提示词</h3>
              </div>
              <button
                type="button"
                onClick={() => handleCopy(summary.prompt, copied ? '已复制。' : '已复制对抗提示词。')}
                className="btn-secondary !px-2.5 !py-1.5 !text-xs"
              >
                <Copy className="h-3.5 w-3.5" />
                复制
              </button>
            </div>
            {summary.prompt ? (
              <div className="max-h-[260px] overflow-auto rounded-xl bg-[#0f172a] p-4 border border-graphite-200 shadow-inner">
                <p className="font-mono text-[13px] leading-relaxed text-electric-300 whitespace-pre-wrap selection:bg-electric-500/30">
                  {summary.prompt}
                </p>
              </div>
            ) : (
              <EmptyState
                icon={Clipboard}
                title="暂无对抗提示词"
                description="当前结果没有返回对抗提示词字段。"
              />
            )}
          </article>

          <article className="rounded-2xl border border-white/60 bg-white/40 p-5 shadow-sm backdrop-blur-sm hover:bg-white/60 transition-colors">
            <div className="mb-4 flex items-center justify-between border-b border-graphite-200 pb-3">
              <div className="flex items-center gap-2">
                <div className="bg-lava-50 text-lava-600 p-1.5 rounded-lg border border-lava-100">
                  <FileSearch className="h-4 w-4" />
                </div>
                <h3 className="text-sm font-bold text-graphite-900">模型响应</h3>
              </div>
              <button
                type="button"
                onClick={() => handleCopy(summary.modelResponse, '已复制模型响应。')}
                className="btn-secondary !px-2.5 !py-1.5 !text-xs"
              >
                <Copy className="h-3.5 w-3.5" />
                复制
              </button>
            </div>
            {summary.modelResponse ? (
              <div className="max-h-[260px] overflow-auto rounded-xl bg-white/80 p-4 border border-graphite-200/60 shadow-inner">
                <p className="text-[13.5px] leading-relaxed text-graphite-800 whitespace-pre-wrap">
                  {summary.modelResponse}
                </p>
              </div>
            ) : (
              <EmptyState
                icon={FileSearch}
                title="暂无模型响应"
                description="当前结果没有返回模型输出内容。"
              />
            )}
          </article>
        </div>

        <article className="rounded-2xl border border-white/60 bg-white/40 p-5 shadow-sm backdrop-blur-sm mt-2">
          <div className="mb-4 flex items-center gap-2">
            {isSuccess ? (
              <div className="bg-lava-50 text-lava-600 p-1.5 rounded-lg border border-lava-100">
                <AlertTriangle className="h-4 w-4" />
              </div>
            ) : (
              <div className="bg-neon-50 text-neon-600 p-1.5 rounded-lg border border-neon-100">
                <CheckCircle2 className="h-4 w-4" />
              </div>
            )}
            <h3 className="text-sm font-bold text-graphite-900">后续建议</h3>
          </div>
          {summary.recommendations.length > 0 ? (
            <div className="space-y-3">
              {summary.recommendations.slice(0, 4).map((item, index) => (
                <div
                  key={`${item.priority}-${index}`}
                  className="group flex gap-4 rounded-xl border border-white/80 bg-white/60 px-5 py-3.5 hover:bg-white hover:border-graphite-200 transition-colors"
                >
                  <div className={`mt-0.5 shrink-0 rounded-md px-2 py-0.5 text-[10px] font-bold border ${item.priority === 'P1' ? 'bg-lava-50 text-lava-700 border-lava-200' : 'bg-graphite-100 text-graphite-600 border-graphite-200'}`}>
                    {item.priority || `建议 ${index + 1}`}
                  </div>
                  <p className="text-[13.5px] font-medium text-graphite-700 leading-relaxed group-hover:text-graphite-900">{item.content || String(item)}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-graphite-200/50 bg-white/50 px-5 py-4">
              <p className="text-sm text-graphite-500 font-medium">
                {isSuccess
                  ? '建议补充输入过滤、输出审查和更严格的系统提示保护。'
                  : '当前测试未突破防线，建议继续扩大提示词覆盖面验证鲁棒性。'}
              </p>
            </div>
          )}
        </article>
      </div>
    </motion.section>
  )
}
