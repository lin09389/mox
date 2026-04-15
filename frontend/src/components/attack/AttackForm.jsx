import { AnimatePresence, motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { BookText, RefreshCw, ShieldAlert, Sparkles, Wand2 } from 'lucide-react'
import { ADVANCED_ATTACK_TYPES, ATTACK_TYPES, DEFAULT_MODELS, GRADIENT_ATTACK_TYPES } from './constants'
import { PanelHeader, StatusPill } from '../ui/AppFrame'

export default function AttackForm({
  form,
  setForm,
  onSubmit,
  loading,
  apiConnected,
  templates = [],
  onLoadTemplate,
  modelOptions = DEFAULT_MODELS,
}) {
  const showGradientConfig = GRADIENT_ATTACK_TYPES.includes(form.attack_type)
  const showAdvancedConfig = ADVANCED_ATTACK_TYPES.includes(form.attack_type)

  const handleSubmit = (event) => {
    event.preventDefault()

    if (!form.prompt.trim()) {
      toast.error('请先输入攻击提示词。')
      return
    }

    if (!form.target_behavior.trim()) {
      toast.error('请描述目标行为。')
      return
    }

    onSubmit(form)
  }

  const resetForm = () => {
    setForm((current) => ({
      ...current,
      prompt: '',
      target_behavior: '',
      max_iterations: 10,
    }))
    toast.success('已重置当前表单。')
  }

  return (
    <section className="card h-full flex flex-col">
      <PanelHeader
        title="攻击参数配置"
        description="选择攻击策略与目标模型，设定攻击提示词与预期目标。"
        action={<StatusPill online={apiConnected} />}
      />

      <div className="mb-6 flex flex-wrap gap-2">
        <button type="button" onClick={resetForm} className="btn-secondary !px-3 !py-1.5 text-xs">
          <RefreshCw className="h-3.5 w-3.5" />
          重置参数
        </button>
      </div>

      {templates.length > 0 && (
        <div className="mb-6 rounded-2xl border border-white/60 bg-white/40 p-5 backdrop-blur-sm shadow-sm transition-all hover:bg-white/60">
          <div className="mb-4 flex items-center gap-2">
            <BookText className="h-4 w-4 text-electric-700" />
            <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-graphite-600">预设模板</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            {templates.slice(0, 4).map((template) => (
              <button
                key={template.name}
                type="button"
                onClick={() => onLoadTemplate(template)}
                className="group rounded-xl border border-white/80 bg-white/60 p-4 text-left transition-all duration-300 hover:border-electric-200 hover:bg-white hover:shadow-soft hover:-translate-y-0.5"
              >
                <p className="text-sm font-bold text-graphite-900 group-hover:text-electric-700 transition-colors">{template.name}</p>
                <p className="mt-1.5 line-clamp-2 text-xs font-medium text-graphite-500 leading-relaxed">
                  {template.description || template.target || template.prompt || template.content}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6 flex-1 flex flex-col">
        <div>
          <div className="mb-3 flex items-center justify-between">
            <label className="text-sm font-bold text-graphite-900">攻击策略</label>
            <span className="text-[10px] font-bold uppercase tracking-wider text-graphite-500 bg-white/80 border border-graphite-200/60 px-2 py-0.5 rounded-full shadow-sm">共 {ATTACK_TYPES.length} 种</span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {ATTACK_TYPES.map((type) => {
              const active = form.attack_type === type.value
              return (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => setForm((current) => ({ ...current, attack_type: type.value }))}
                  className={`relative overflow-hidden rounded-xl border p-4 text-left transition-all duration-300 ${
                    active
                      ? 'border-electric-400 bg-gradient-to-br from-electric-50 to-white shadow-electric-500/10'
                      : 'border-white/60 bg-white/40 hover:border-graphite-300 hover:bg-white hover:shadow-soft backdrop-blur-sm'
                  }`}
                >
                  {active && (
                    <div className="absolute top-0 left-0 w-1.5 h-full bg-electric-500 shadow-[0_0_10px_rgba(14,165,233,0.5)]" />
                  )}
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className={`text-sm font-bold transition-colors ${active ? 'text-electric-900' : 'text-graphite-800'}`}>{type.label}</p>
                      <p className="mt-1 text-xs font-medium text-graphite-500 leading-relaxed">{type.desc}</p>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        <div className="grid gap-5 lg:grid-cols-2">
          <div>
            <label className="text-sm font-bold text-graphite-900 mb-2 block">目标模型</label>
            <div className="relative">
              <select
                className="input-field cursor-pointer appearance-none bg-white/70 backdrop-blur-md shadow-sm border-white/80 hover:border-graphite-300 focus:ring-electric-500/20 focus:border-electric-400 font-medium"
                value={form.model}
                onChange={(event) => setForm((current) => ({ ...current, model: event.target.value }))}
              >
                {modelOptions.map((model) => (
                  <option key={model.value} value={model.value}>
                    {model.label} · {model.provider}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-graphite-500">
                <svg className="h-4 w-4 fill-current" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                  <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                </svg>
              </div>
            </div>
          </div>

          <div>
            <label className="text-sm font-bold text-graphite-900 mb-2 block">迭代深度</label>
            <div className="rounded-xl border border-white/80 bg-white/50 px-5 py-3 shadow-sm backdrop-blur-md">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-graphite-500">测试轮数</span>
                <span className="text-sm font-extrabold text-electric-700 bg-electric-50 px-2 py-0.5 rounded-md border border-electric-100">{form.max_iterations}</span>
              </div>
              <input
                type="range"
                min={1}
                max={100}
                value={form.max_iterations}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    max_iterations: Number.parseInt(event.target.value, 10),
                  }))
                }
                className="w-full accent-electric-500 cursor-pointer h-1.5 bg-graphite-200 rounded-lg appearance-none"
              />
            </div>
          </div>
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <label className="text-sm font-bold text-graphite-900">攻击提示词</label>
            <span className="text-xs font-medium text-graphite-600 bg-white px-2 py-0.5 rounded-full shadow-sm border border-graphite-200">{form.prompt.length} 字符</span>
          </div>
          <textarea
            rows={5}
            value={form.prompt}
            onChange={(event) => setForm((current) => ({ ...current, prompt: event.target.value }))}
            className="input-field resize-y font-mono text-[13px] leading-relaxed bg-white/70 backdrop-blur-md shadow-sm border-white/80 hover:border-graphite-300 focus:ring-electric-500/20 focus:border-electric-400 transition-all duration-300"
            placeholder="输入您要测试的 Prompt..."
          />
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <label className="text-sm font-bold text-graphite-900">预期目标行为</label>
            <span className="text-xs font-medium text-graphite-600 bg-white px-2 py-0.5 rounded-full shadow-sm border border-graphite-200">{form.target_behavior.length} 字符</span>
          </div>
          <textarea
            rows={3}
            value={form.target_behavior}
            onChange={(event) =>
              setForm((current) => ({ ...current, target_behavior: event.target.value }))
            }
            className="input-field resize-y text-sm bg-white/70 backdrop-blur-md shadow-sm border-white/80 hover:border-graphite-300 focus:ring-electric-500/20 focus:border-electric-400 transition-all duration-300"
            placeholder="描述您期望模型在被攻击后产生的具体行为..."
          />
        </div>

        <AnimatePresence mode="popLayout">
          {showGradientConfig && (
            <motion.div
              initial={{ opacity: 0, height: 0, overflow: 'hidden' }}
              animate={{ opacity: 1, height: 'auto', overflow: 'visible' }}
              exit={{ opacity: 0, height: 0, overflow: 'hidden' }}
              transition={{ duration: 0.3 }}
            >
              <div className="rounded-xl border border-lava-200/60 bg-gradient-to-br from-lava-50/80 to-white/60 p-5 mt-2 backdrop-blur-md shadow-lava-500/5">
                <div className="mb-2 flex items-center gap-2">
                  <div className="bg-white p-1.5 rounded-md shadow-sm border border-lava-100">
                    <Wand2 className="h-4 w-4 text-lava-600" />
                  </div>
                  <p className="text-sm font-bold text-lava-900">梯度下降策略已激活</p>
                </div>
                <p className="text-xs font-medium text-lava-700/80 leading-relaxed pl-9">
                  当前策略将通过计算梯度来寻找最优的对抗扰动。此过程需要大量的计算资源与较长的执行时间。建议先使用较小的迭代深度进行试探。
                </p>
              </div>
            </motion.div>
          )}

          {showAdvancedConfig && (
            <motion.div
              initial={{ opacity: 0, height: 0, overflow: 'hidden' }}
              animate={{ opacity: 1, height: 'auto', overflow: 'visible' }}
              exit={{ opacity: 0, height: 0, overflow: 'hidden' }}
              transition={{ duration: 0.3 }}
            >
              <div className="rounded-xl border border-electric-200/60 bg-gradient-to-br from-electric-50/80 to-white/60 p-5 mt-2 backdrop-blur-md shadow-electric-500/5">
                <div className="mb-2 flex items-center gap-2">
                  <div className="bg-white p-1.5 rounded-md shadow-sm border border-electric-100">
                    <Sparkles className="h-4 w-4 text-electric-700" />
                  </div>
                  <p className="text-sm font-bold text-electric-900">高级策略模式</p>
                </div>
                <p className="text-xs font-medium text-electric-700/80 leading-relaxed pl-9">
                  高级策略包含多轮角色扮演与复杂的上下文构建。此模式下，目标模型更容易产生幻觉与策略漂移。
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="mt-auto pt-6 border-t border-graphite-200">
          <button type="submit" disabled={loading} className="btn-primary w-full !py-3.5 text-base">
            {loading ? (
              <>
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                正在执行...
              </>
            ) : (
              <>
                <ShieldAlert className="h-5 w-5" />
                立即执行测试
              </>
            )}
          </button>
        </div>
      </form>
    </section>
  )
}
