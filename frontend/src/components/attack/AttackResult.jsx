/**
 * 攻击结果组件 - 赛博工匠风格
 * 显示攻击测试的结果和分析
 */

import { motion, AnimatePresence } from 'framer-motion'
import { Copy, CheckCircle2, AlertTriangle, Layers } from 'lucide-react'
import { useCopyToClipboard } from '../../hooks/useCommon'

export default function AttackResult({ result }) {
  const [copied, copyToClipboard] = useCopyToClipboard()

  if (!result) {
    return (
      <div className="card h-full flex items-center justify-center min-h-[320px]">
        <div className="text-center">
          <div className="w-14 h-14 mx-auto mb-3 rounded-lg bg-graphite-100 flex items-center justify-center">
            <Layers className="w-7 h-7 text-graphite-400" />
          </div>
          <p className="text-sm text-graphite-500">执行攻击测试后查看结果</p>
        </div>
      </div>
    )
  }

  const isSuccess = result['结果'] === 'success' || result.result === 'success'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="card h-full"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-5">
        <div className="w-10 h-10 bg-electric-100 rounded-lg flex items-center justify-center border border-electric-200/70">
          <Layers className="w-5 h-5 text-electric-600" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-graphite-900">攻击结果</h2>
          <p className="text-xs text-graphite-500">查看攻击效果详情</p>
        </div>
      </div>

      {/* Main Result */}
      <AnimatePresence mode="wait">
        <motion.div
          key="result"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.25 }}
          className="space-y-4"
        >
          {/* Status Card */}
          <div className="flex items-center justify-between p-4 bg-graphite-50/80 rounded-lg border border-graphite-200/60">
            <div>
              <p className="text-xs text-graphite-500 font-medium">攻击结果</p>
              <p className="text-base font-bold text-graphite-900">
                {isSuccess ? '攻击成功' : '攻击失败'}
              </p>
            </div>
            <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
              isSuccess
                ? 'bg-lava-100 text-lava-600'
                : 'bg-neon-100 text-neon-600'
            }`}>
              {isSuccess ? (
                <AlertTriangle className="w-6 h-6" />
              ) : (
                <CheckCircle2 className="w-6 h-6" />
              )}
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-3">
            <StatCard
              label="成功分数"
              value={result['成功分数'] || result.success_score?.toFixed(2) || '0.00'}
              color="electric"
            />
            <StatCard
              label="迭代次数"
              value={result['迭代次数'] || result.iterations || 0}
              color="lave"
            />
          </div>

          {/* Demo Mode Warning */}
          {result._demo_mode && (
            <div className="p-3.5 bg-amber-50/50 rounded-lg border border-amber-200/60">
              <span className="text-xs font-semibold text-amber-700 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                演示模式 - 数据仅供参考
              </span>
              <p className="text-xs text-amber-600 mt-1">
                {result._warning || '这是演示数据，因为API未连接。请确保后端服务正在运行。'}
              </p>
            </div>
          )}

          {/* Adversarial Prompt */}
          {(result['对抗提示词'] || result.adversarial_prompt) && (
            <div className="p-3.5 bg-graphite-50/80 rounded-lg border border-graphite-200/60">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-medium text-graphite-600">对抗提示词</span>
                <button
                  onClick={() => copyToClipboard(result['对抗提示词'] || result.adversarial_prompt)}
                  className="text-graphite-400 hover:text-electric-600 transition-colors p-1"
                >
                  <Copy className="w-3.5 h-3.5" />
                </button>
              </div>
              <p className="text-xs text-graphite-700 font-mono break-all leading-relaxed">
                {(result['对抗提示词'] || result.adversarial_prompt)?.slice(0, 200)}
                {(result['对抗提示词'] || result.adversarial_prompt)?.length > 200 && '...'}
              </p>
            </div>
          )}

          {/* Model Response */}
          {(result['模型响应'] || result.model_response) && (
            <div className="p-3.5 bg-graphite-50/80 rounded-lg border border-graphite-200/60">
              <span className="text-xs font-medium text-graphite-600">模型响应</span>
              <p className="text-xs text-graphite-700 mt-2 break-all leading-relaxed">
                {(result['模型响应'] || result.model_response)?.slice(0, 300)}
                {(result['模型响应'] || result.model_response)?.length > 300 && '...'}
              </p>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations && result.recommendations.length > 0 && (
            <div className="p-3.5 bg-amber-50/50 rounded-lg border border-amber-200/60">
              <span className="text-xs font-semibold text-amber-700">安全建议</span>
              <ul className="mt-2 space-y-1.5">
                {result.recommendations.slice(0, 3).map((rec, idx) => (
                  <li key={idx} className="text-xs text-amber-700 flex items-start gap-2">
                    <span className="font-semibold">[{rec.priority}]</span>
                    <span>{rec.content}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      </AnimatePresence>
    </motion.div>
  )
}

// ============ 子组件 ============

function StatCard({ label, value, color }) {
  const colorClasses = {
    electric: 'bg-electric-50/50 text-electric-700',
    lave: 'bg-lava-50/50 text-lava-700',
    neon: 'bg-neon-50/50 text-neon-700',
    amber: 'bg-amber-50/50 text-amber-700',
  }

  return (
    <div className={`p-3.5 rounded-lg ${colorClasses[color]}`}>
      <p className="text-[11px] text-graphite-500">{label}</p>
      <p className="text-xl font-bold text-graphite-900 mt-0.5">{value}</p>
    </div>
  )
}
