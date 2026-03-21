/**
 * 攻击表单组件 - 赛博工匠风格
 * 处理攻击测试的表单输入和提交
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { Layers, RefreshCw, ShieldAlert } from 'lucide-react'
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
    <div className="card card-glow">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-lava-100 rounded-lg flex items-center justify-center border border-lava-200/70">
            <ShieldAlert className="w-5 h-5 text-lava-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-graphite-900">攻击测试</h2>
            <p className="text-xs text-graphite-500">测试模型的安全防护能力</p>
          </div>
        </div>

        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ${
          apiConnected
            ? 'bg-neon-50 text-neon-700 border border-neon-200/70'
            : 'bg-amber-50 text-amber-700 border border-amber-200/70'
        }`}>
          <span className={`w-2 h-2 rounded-full animate-pulse ${apiConnected ? 'bg-neon-500' : 'bg-amber-500'}`} />
          {apiConnected ? '在线' : '演示模式'}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setShowTemplates(!showTemplates)}
          className="btn-secondary flex items-center gap-1.5 text-xs py-1.5 px-3"
        >
          <Layers className="w-3.5 h-3.5" />
          模板
        </button>
        <button
          onClick={resetForm}
          className="btn-secondary flex items-center gap-1.5 text-xs py-1.5 px-3"
        >
          <RefreshCw className="w-3.5 h-3.5" />
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
            className="mb-4 overflow-hidden"
          >
            <div className="p-3 bg-graphite-50/80 rounded-md border border-graphite-200/60">
              <p className="text-xs font-medium text-graphite-600 mb-2.5">选择预设模板</p>
              <div className="grid grid-cols-2 gap-2">
                {templates.slice(0, 6).map((t, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      onLoadTemplate(t)
                      setShowTemplates(false)
                    }}
                    className="p-2.5 text-left bg-white rounded-md border border-graphite-200/60 hover:border-electric-300 hover:bg-electric-50/30 transition-all duration-150 text-xs"
                  >
                    <div className="font-medium text-graphite-900 mb-0.5">{t.name}</div>
                    <div className="text-[11px] text-graphite-400 truncate">
                      {(t.content || t.prompt || '').slice(0, 25)}...
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
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
          className="btn-primary w-full"
        >
          {loading ? (
            <>
              <div className="spinner" />
              <span>攻击中...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
      <div className="grid grid-cols-2 gap-2 max-h-56 overflow-y-auto pr-1">
        {types.map((type) => (
          <button
            key={type.value}
            type="button"
            onClick={() => onChange(type.value)}
            className={`p-2.5 rounded-md border text-left transition-all duration-150 text-xs ${
              selected === type.value
                ? 'border-electric-500 bg-electric-50/50 text-electric-700'
                : 'border-graphite-200/70 hover:border-graphite-300 text-graphite-700'
            }`}
          >
            <div className="flex items-center gap-1.5">
              <span className="text-base">{type.icon}</span>
              <span className="font-medium text-xs">{type.label}</span>
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
      <div className="flex justify-between items-center mb-1.5">
        <label className="label mb-0">攻击提示词</label>
        <span className="text-[11px] text-graphite-400">{value.length} 字符</span>
      </div>
      <textarea
        className="input-field font-mono text-xs"
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
      <div className="flex justify-between items-center mb-1.5">
        <label className="label mb-0">目标行为</label>
        <span className="text-[11px] text-graphite-400">{value.length} 字符</span>
      </div>
      <textarea
        className="input-field text-xs"
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
        最大迭代次数: <span className="text-electric-600 font-semibold">{value}</span>
      </label>
      <input
        type="range"
        min={1}
        max={100}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="w-full accent-electric-500"
      />
    </div>
  )
}

function GradientAttackConfig({ attackType, maxIterations }) {
  return (
    <div className="p-3 bg-lava-50/50 rounded-md border border-lava-200/60">
      <div className="flex items-center gap-2 mb-3">
        <svg className="w-4 h-4 text-lava-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <h3 className="text-xs font-semibold text-lava-900">梯度攻击配置</h3>
      </div>
      <div className="grid grid-cols-3 gap-2 text-[11px]">
        <div className="p-2 bg-white rounded text-center">
          <div className="font-bold text-lava-600">{attackType === 'fgsm' ? 'FGSM' : attackType === 'pgd' ? 'PGD' : 'Suffix'}</div>
          <div className="text-lava-400">方法</div>
        </div>
        <div className="p-2 bg-white rounded text-center">
          <div className="font-bold text-lava-600">{maxIterations}</div>
          <div className="text-lava-400">迭代</div>
        </div>
        <div className="p-2 bg-white rounded text-center">
          <div className="font-bold text-lava-600">{attackType === 'fgsm' ? '单步' : '多步'}</div>
          <div className="text-lava-400">类型</div>
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
    <div className="p-3 bg-electric-50/50 rounded-md border border-electric-200/60">
      <div className="flex items-center gap-2 mb-3">
        <svg className="w-4 h-4 text-electric-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <h3 className="text-xs font-semibold text-electric-900">高级攻击配置</h3>
      </div>
      <div className="grid grid-cols-2 gap-2 text-[11px]">
        <div className="p-2 bg-white rounded text-center">
          <div className="font-bold text-electric-600">{attackNames[attackType] || attackType}</div>
          <div className="text-electric-400">攻击模式</div>
        </div>
        <div className="p-2 bg-white rounded text-center">
          <div className="font-bold text-electric-600">{maxIterations}</div>
          <div className="text-electric-400">迭代</div>
        </div>
      </div>
    </div>
  )
}
