/**
 * 攻击结果组件
 * 显示攻击测试的结果和分析
 */

import { motion, AnimatePresence } from 'framer-motion'
import { Copy, CheckCircle2, AlertTriangle, Layers } from 'lucide-react'
import { useCopyToClipboard } from '../../hooks/useCommon'

export default function AttackResult({ result }) {
  const [copied, copyToClipboard] = useCopyToClipboard()

  if (!result) {
    return (
      <div className="card-premium h-full flex items-center justify-center">
        <div className="text-center text-dark-400">
          <Layers className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p>执行攻击测试后查看结果</p>
        </div>
      </div>
    )
  }

  const isSuccess = result['结果'] === 'success' || result.result === 'success'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="card-premium h-full"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-600 rounded-xl flex items-center justify-center shadow-glow-primary">
          <Layers className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-dark-900">攻击结果</h2>
          <p className="text-sm text-dark-500">查看攻击效果详情</p>
        </div>
      </div>

      {/* Main Result */}
      <AnimatePresence mode="wait">
        <motion.div
          key="result"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="space-y-4"
        >
          {/* Status Card */}
          <div className="flex items-center justify-between p-4 bg-gradient-to-r from-dark-50 to-dark-100/50 rounded-xl">
            <div>
              <p className="text-sm text-dark-500 font-medium">攻击结果</p>
              <p className="text-lg font-bold text-dark-900">
                {isSuccess ? '攻击成功' : '攻击失败'}
              </p>
            </div>
            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-soft ${
              isSuccess
                ? 'bg-danger-100 text-danger-600'
                : 'bg-success-100 text-success-600'
            }`}>
              {isSuccess ? (
                <AlertTriangle className="w-8 h-8" />
              ) : (
                <CheckCircle2 className="w-8 h-8" />
              )}
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-4">
            <StatCard 
              label="成功分数" 
              value={result['成功分数'] || result.success_score?.toFixed(2) || '0.00'} 
              color="primary"
            />
            <StatCard 
              label="迭代次数" 
              value={result['迭代次数'] || result.iterations || 0} 
              color="purple"
            />
          </div>

          {/* Adversarial Prompt */}
          {(result['对抗提示词'] || result.adversarial_prompt) && (
            <div className="p-4 bg-dark-50 rounded-xl">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-dark-600">对抗提示词</span>
                <button
                  onClick={() => copyToClipboard(result['对抗提示词'] || result.adversarial_prompt)}
                  className="text-primary-500 hover:text-primary-600"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
              <p className="text-sm text-dark-700 font-mono break-all">
                {(result['对抗提示词'] || result.adversarial_prompt)?.slice(0, 200)}
                {(result['对抗提示词'] || result.adversarial_prompt)?.length > 200 && '...'}
              </p>
            </div>
          )}

          {/* Model Response */}
          {(result['模型响应'] || result.model_response) && (
            <div className="p-4 bg-dark-50 rounded-xl">
              <span className="text-sm font-medium text-dark-600">模型响应</span>
              <p className="text-sm text-dark-700 mt-2 break-all">
                {(result['模型响应'] || result.model_response)?.slice(0, 300)}
                {(result['模型响应'] || result.model_response)?.length > 300 && '...'}
              </p>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations && result.recommendations.length > 0 && (
            <div className="p-4 bg-warning-50 rounded-xl border border-warning-200">
              <span className="text-sm font-medium text-warning-700">安全建议</span>
              <ul className="mt-2 space-y-1">
                {result.recommendations.slice(0, 3).map((rec, idx) => (
                  <li key={idx} className="text-sm text-warning-600 flex items-start gap-2">
                    <span className="font-medium">[{rec.priority}]</span>
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
    primary: 'bg-primary-50/50 text-primary-600',
    purple: 'bg-purple-50/50 text-purple-600',
    success: 'bg-success-50/50 text-success-600',
    danger: 'bg-danger-50/50 text-danger-600',
  }

  return (
    <div className={`p-4 rounded-xl ${colorClasses[color]}`}>
      <p className="text-sm text-dark-500">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  )
}