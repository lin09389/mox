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
import { EmptyState, PanelHeader } from '../ui/AppFrame'
import { useCopyToClipboard } from '../../hooks/useCommon'
import { AttackRiskGauge, AttackDemoBanner, AttackCodeBlock } from './AttackTheme'

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
      <section className="attack-report-panel card-glow h-full min-h-[520px] flex flex-col">
        <PanelHeader
          title="结果面板"
          description="运行测试后，这里会展示成功分数、模型响应与后续建议。"
        />
        <EmptyState
          icon={Layers3}
          title="等待一轮测试结果"
          description="先在左侧配置攻击参数并提交。结果面板会自动切换到分析视图。"
          tone="electric"
        />
      </section>
    )
  }

  const isSuccess = summary.status === 'success'
  const riskPercent = Math.round(summary.score * 100)

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      className="attack-report-panel card-glow h-full"
    >
      <PanelHeader
        title="结果面板"
        description="统一查看风险评分、攻击状态、对抗提示词和模型响应。"
      />

      <div className="space-y-4">
        <div className="attack-lab-hero hero-panel p-5">
          <div className="relative z-10 flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-2">
              <span className={`badge ${isSuccess ? 'badge-danger' : 'badge-success'}`}>
                {isSuccess ? <AlertTriangle className="h-3.5 w-3.5" /> : <ShieldCheck className="h-3.5 w-3.5" />}
                {isSuccess ? '攻击成功' : '攻击已拦截'}
              </span>
              <p className="text-sm text-[var(--text-muted)]">
                {summary.demo ? '当前显示演示结果，用于预览流程和页面状态。' : '该结果来自当前一次实际测试。'}
              </p>
              <div className="flex flex-wrap gap-4 text-sm text-[var(--text-muted)]">
                <span>
                  风险分数：<strong className="text-[var(--text-main)] font-mono">{summary.score.toFixed(2)}</strong>
                </span>
                <span>
                  迭代次数：<strong className="text-[var(--text-main)] font-mono">{summary.iterations}</strong>
                </span>
              </div>
            </div>

            <div className="min-w-[240px]">
              <AttackRiskGauge value={riskPercent} label="风险热度" breached={isSuccess} />
            </div>
          </div>
        </div>

        {summary.demo && (
          <AttackDemoBanner text={summary.warning || '当前后端未连接，页面展示的是演示数据。'} />
        )}

        <div className="grid gap-4 lg:grid-cols-2">
          <article className="attack-output-card">
            <div className="attack-output-card-header">
              <div className="attack-output-card-title">
                <Clipboard className="h-4 w-4 text-[var(--attack-accent)]" />
                对抗提示词
              </div>
              <button
                type="button"
                onClick={() => handleCopy(summary.prompt, copied ? '已复制。' : '已复制对抗提示词。')}
                className="btn-ghost px-2 py-1"
              >
                <Copy className="h-4 w-4" />
              </button>
            </div>
            {summary.prompt ? (
              <AttackCodeBlock>{summary.prompt}</AttackCodeBlock>
            ) : (
              <EmptyState
                icon={Clipboard}
                title="暂无对抗提示词"
                description="当前结果没有返回对抗提示词字段。"
              />
            )}
          </article>

          <article className="attack-output-card">
            <div className="attack-output-card-header">
              <div className="attack-output-card-title">
                <FileSearch className="h-4 w-4 text-[var(--attack-danger)]" />
                模型响应
              </div>
              <button
                type="button"
                onClick={() => handleCopy(summary.modelResponse, '已复制模型响应。')}
                className="btn-ghost px-2 py-1"
              >
                <Copy className="h-4 w-4" />
              </button>
            </div>
            {summary.modelResponse ? (
              <AttackCodeBlock className="font-sans text-sm">{summary.modelResponse}</AttackCodeBlock>
            ) : (
              <EmptyState
                icon={FileSearch}
                title="暂无模型响应"
                description="当前结果没有返回模型输出内容。"
              />
            )}
          </article>
        </div>

        <article className="attack-output-card">
          <div className="attack-output-card-title mb-3">
            {isSuccess ? (
              <AlertTriangle className="h-4 w-4 text-[var(--attack-danger)]" />
            ) : (
              <CheckCircle2 className="h-4 w-4 text-neon-500" />
            )}
            后续建议
          </div>
          {summary.recommendations.length > 0 ? (
            <div className="space-y-3">
              {summary.recommendations.slice(0, 4).map((item, index) => (
                <div
                  key={`${item.priority}-${index}`}
                  className="rounded-xl border border-[var(--border-glass)] bg-[var(--bg-glass)] px-4 py-3"
                >
                  <p className="text-sm font-bold text-[var(--text-main)]">
                    {item.priority ? `优先级 ${item.priority}` : `建议 ${index + 1}`}
                  </p>
                  <p className="mt-1 text-sm font-medium text-[var(--text-muted)]">{item.content || String(item)}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm font-medium text-[var(--text-muted)]">
              {isSuccess
                ? '建议补充输入过滤、输出审查和更严格的系统提示保护。'
                : '当前测试未突破防线，建议继续扩大提示词覆盖面验证鲁棒性。'}
            </p>
          )}
        </article>
      </div>
    </motion.section>
  )
}