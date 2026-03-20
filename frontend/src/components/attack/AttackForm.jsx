/**
 * 攻击表单组件
 * 处理攻击测试的表单输入和提交
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { Layers, RefreshCw } from 'lucide-react'
import { ATTACK_TYPES, DEFAULT_MODELS, GRADIENT_ATTACK_TYPES, ADVANCED_ATTACK_TYPES } from './constants'

export default function AttackForm({ 
  form, 
  setForm, 
  onSubmit, 
  loading, 
  apiConnected,
  templates = [],
  onLoadTemplate 
}) {
  const [showTemplates, setShowTemplates] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!form.prompt.trim()) {
      toast.error('请输入攻击提示词')
      return
    }
    if (!form.target_behavior.trim()) {
      toast.error('请输入目标行为')
      return
    }
    onSubmit(form)
  }

  const resetForm = () => {
    setForm({
      ...form,
      prompt: '',
      target_behavior: '',
    })
    toast.success('已重置表单')
  }

  const isFormValid = form.prompt.trim() && form.target_behavior.trim()
  const isGradientAttack = GRADIENT_ATTACK_TYPES.includes(form.attack_type)
  const isAdvancedAttack = ADVANCED_ATTACK_TYPES.includes(form.attack_type)

  return (
    <div className="card-premium glow">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 bg-gradient-to-br from-danger-500 to-warning-500 rounded-2xl flex items-center justify-center shadow-glow-primary">
            <ShieldAlert className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-dark-900">攻击测试</h2>
            <p className="text-sm text-dark-500">测试模型的安全防护能力</p>
          </div>
        </div>

        <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold transition-all duration-300 ${
          apiConnected
            ? 'bg-success-100 text-success-700 border border-success-200/70'
            : 'bg-warning-100 text-warning-700 border border-warning-200/70'
        }`}>
          <div className={`w-2.5 h-2.5 rounded-full animate-pulse ${apiConnected ? 'bg-success-500' : 'bg-warning-500'}`} />
          {apiConnected ? '在线' : '演示模式'}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 mb-5">
        <button
          onClick={() => setShowTemplates(!showTemplates)}
          className="btn-secondary flex items-center gap-2 text-sm"
        >
          <Layers className="w-4 h-4" />
          模板
        </button>
        <button
          onClick={resetForm}
          className="btn-secondary flex items-center gap-2 text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          重置
        </button>
      </div>

      {/* Templates Dropdown */}
      <AnimatePresence>
        {showTemplates && templates.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-5 overflow-hidden"
          >
            <div className="p-4 bg-dark-50/50 rounded-xl border border-dark-200/60">
              <p className="text-sm font-medium text-dark-600 mb-3">选择预设模板</p>
              <div className="grid grid-cols-2 gap-2">
                {templates.slice(0, 6).map((t, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      onLoadTemplate(t)
                      setShowTemplates(false)
                    }}
                    className="p-2 text-left text-sm bg-white rounded-lg border border-dark-200/60 hover:border-primary-300 hover:bg-primary-50/30 transition-all"
                  >
                    <div className="font-medium text-dark-900">{t.name}</div>
                    <div className="text-xs text-dark-500 truncate">
                      {(t.content || t.prompt || '').slice(0, 30)}...
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Attack Type Selection */}
        <AttackTypeSelector 
          types={ATTACK_TYPES} 
          selected={form.attack_type}
          onChange={(value) => setForm({ ...form, attack_type: value })}
        />

        {/* Model Selection */}
        <ModelSelector 
          models={DEFAULT_MODELS}
          selected={form.model}
          onChange={(value) => setForm({ ...form, model: value })}
        />

        {/* Prompt Input */}
        <PromptInput 
          value={form.prompt}
          onChange={(value) => setForm({ ...form, prompt: value })}
        />

        {/* Target Behavior Input */}
        <TargetBehaviorInput 
          value={form.target_behavior}
          onChange={(value) => setForm({ ...form, target_behavior: value })}
        />

        {/* Iterations Slider */}
        <IterationsSlider 
          value={form.max_iterations}
          onChange={(value) => setForm({ ...form, max_iterations: value })}
        />

        {/* Gradient Attack Config */}
        {isGradientAttack && (
          <GradientAttackConfig attackType={form.attack_type} maxIterations={form.max_iterations} />
        )}

        {/* Advanced Attack Config */}
        {isAdvancedAttack && (
          <AdvancedAttackConfig attackType={form.attack_type} maxIterations={form.max_iterations} />
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading || !isFormValid}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="spinner" />
              <span>攻击中...</span>
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>发起攻击</span>
            </>
          )}
        </button>
      </form>
    </div>
  )
}

// ============ 子组件 ============

function AttackTypeSelector({ types, selected, onChange }) {
  return (
    <div>
      <label className="label">攻击类型</label>
      <div className="grid grid-cols-2 gap-3 max-h-64 overflow-y-auto">
        {types.map((type) => (
          <button
            key={type.value}
            type="button"
            onClick={() => onChange(type.value)}
            className={`p-3 rounded-xl border-2 text-left transition-all duration-200 ${
              selected === type.value
                ? 'border-primary-500 bg-primary-50/50'
                : 'border-dark-200/60 hover:border-dark-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <span className="text-lg">{type.icon}</span>
              <span className="font-medium text-dark-900 text-sm">{type.label}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

function ModelSelector({ models, selected, onChange }) {
  return (
    <div>
      <label className="label">目标模型</label>
      <select
        className="select-field"
        value={selected}
        onChange={(e) => onChange(e.target.value)}
      >
        {models.map((model) => (
          <option key={model.value} value={model.value}>
            {model.label} ({model.provider})
          </option>
        ))}
      </select>
    </div>
  )
}

function PromptInput({ value, onChange }) {
  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <label className="label mb-0">攻击提示词</label>
        <span className="text-xs text-dark-400">{value.length} 字符</span>
      </div>
      <textarea
        className="input-field font-mono text-sm"
        rows={4}
        placeholder="输入要测试的攻击提示..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  )
}

function TargetBehaviorInput({ value, onChange }) {
  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <label className="label mb-0">目标行为</label>
        <span className="text-xs text-dark-400">{value.length} 字符</span>
      </div>
      <textarea
        className="input-field"
        rows={2}
        placeholder="期望模型输出的目标行为..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  )
}

function IterationsSlider({ value, onChange }) {
  return (
    <div>
      <label className="label">
        最大迭代次数: <span className="text-primary-600 font-semibold">{value}</span>
      </label>
      <input
        type="range"
        min={1}
        max={100}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="w-full accent-primary-500"
      />
    </div>
  )
}

function GradientAttackConfig({ attackType, maxIterations }) {
  return (
    <div className="p-4 bg-gradient-to-r from-orange-50 to-red-50 rounded-xl border border-orange-200">
      <div className="flex items-center gap-2 mb-4">
        <svg className="w-5 h-5 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <h3 className="font-semibold text-orange-900">梯度攻击配置</h3>
      </div>
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div className="p-2 bg-white rounded text-center">
          <div className="font-bold text-orange-600">{attackType === 'fgsm' ? 'FGSM' : attackType === 'pgd' ? 'PGD' : 'Suffix'}</div>
          <div className="text-orange-400">方法</div>
        </div>
        <div className="p-2 bg-white rounded text-center">
          <div className="font-bold text-orange-600">{maxIterations}</div>
          <div className="text-orange-400">迭代</div>
        </div>
        <div className="p-2 bg-white rounded text-center">
          <div className="font-bold text-orange-600">{attackType === 'fgsm' ? '单步' : '多步'}</div>
          <div className="text-orange-400">类型</div>
        </div>
      </div>
    </div>
  )
}

function AdvancedAttackConfig({ attackType, maxIterations }) {
  const attackNames = {
    multimodal_adversarial: '多模态对抗性攻击',
    zero_shot_adversarial: '零成本对抗提示',
    hallucination_induction: '注入式幻觉诱导',
    collaborative_attack: '协同攻击',
    knowledge_distillation: '知识蒸馏攻击',
    evasion_attack: '逃逸攻击',
    meta_adversarial: '元对抗攻击 (对抗三元组)',
  }

  return (
    <div className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border border-purple-200">
      <div className="flex items-center gap-2 mb-4">
        <svg className="w-5 h-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <h3 className="font-semibold text-purple-900">高级攻击配置</h3>
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="p-2 bg-white rounded text-center">
          <div className="font-bold text-purple-600">{attackNames[attackType] || attackType}</div>
          <div className="text-purple-400">攻击模式</div>
        </div>
        <div className="p-2 bg-white rounded text-center">
          <div className="font-bold text-purple-600">{maxIterations}</div>
          <div className="text-purple-400">迭代</div>
        </div>
      </div>
    </div>
  )
}