import { AnimatePresence, motion } from 'framer-motion'
import {
  BarChart3,
  ChevronDown,
  ChevronUp,
  Clock,
  Database,
  Loader2,
  Plus,
  Settings,
  Target,
  Trash2,
  XCircle,
  Zap,
} from 'lucide-react'
import ModelSelect from '../../components/ui/ModelSelect'
import { DEFAULT_PROMPTS } from './constants'

export default function AttackLoopConfigPanel({
  config,
  setConfig,
  typesLoading,
  attackTypesByCategory,
  modelsLoading,
  quickAddModels,
  pickerModel,
  setPickerModel,
  addPickerModel,
  removeModel,
  toggleAttackType,
  newPrompt,
  setNewPrompt,
  addPrompt,
  removePrompt,
  showAdvanced,
  setShowAdvanced,
  totalTests,
}) {
  return (
    <motion.div
      key="config"
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      className="space-y-6"
    >
      <div className="card p-6">
        <h3 className="mb-4 flex items-center gap-3 text-lg font-bold font-display text-[var(--text-main)]">
          <div className="p-1.5 bg-cyan-500/10 rounded-lg"><Database className="h-5 w-5 text-cyan-500" /></div>
          目标模型池
        </h3>
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {config.models.map((model) => (
              <span key={model} className="badge bg-cyan-500/10 border-cyan-500/20 text-cyan-500 pr-1 py-1 flex items-center gap-1">
                {model}
                <button type="button" onClick={() => removeModel(model)} className="hover:bg-cyan-500/20 rounded-full p-0.5 transition-colors">
                  <XCircle className="h-4 w-4" />
                </button>
              </span>
            ))}
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end max-w-lg">
            <div className="flex-1">
              <label className="mb-1.5 block text-xs font-bold text-[var(--text-muted)]">选择模型</label>
              <ModelSelect value={pickerModel} onChange={setPickerModel} />
            </div>
            <button type="button" onClick={addPickerModel} disabled={!pickerModel.trim()} className="btn-secondary shrink-0 disabled:opacity-50">
              <Plus className="h-4 w-4" /> 添加到池
            </button>
          </div>
          <div className="flex flex-wrap gap-2 pt-2">
            {modelsLoading ? (
              <span className="text-xs font-medium text-[var(--text-muted)] flex items-center gap-1.5">
                <Loader2 className="h-3.5 w-3.5 animate-spin" /> 检测本地模型…
              </span>
            ) : quickAddModels.map((model) => (
              <button
                key={model}
                type="button"
                onClick={() => setConfig((prev) => ({ ...prev, models: [...prev.models, model] }))}
                className="badge badge-neutral hover:border-cyan-500/50 hover:bg-cyan-500/5 transition-colors"
              >
                + {model}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="card p-6">
        <h3 className="mb-4 flex items-center gap-3 text-lg font-bold font-display text-[var(--text-main)]">
          <div className="p-1.5 bg-rose-500/10 rounded-lg"><Zap className="h-5 w-5 text-rose-500" /></div>
          攻击向量矩阵
        </h3>
        {typesLoading ? (
          <div className="text-sm font-medium text-[var(--text-muted)] flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" /> 正在加载攻击载荷库...
          </div>
        ) : (
          <div className="grid lg:grid-cols-2 gap-6">
            {Object.entries(attackTypesByCategory).map(([category, types]) => (
              <div key={category} className="space-y-3">
                <h4 className="text-sm font-bold uppercase tracking-widest text-[var(--text-muted)] border-b border-[var(--border-glass)] pb-2">{category}</h4>
                <div className="flex flex-wrap gap-2">
                  {types.map((type) => (
                    <button
                      key={type.value}
                      type="button"
                      onClick={() => toggleAttackType(type.value)}
                      className={`group relative rounded-lg px-3 py-1.5 text-sm font-medium transition-all duration-200 border ${config.attack_types.includes(type.value) ? 'bg-rose-500 text-white border-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.3)]' : 'bg-[var(--bg-glass-strong)] text-[var(--text-main)] border-[var(--border-glass-strong)] hover:border-rose-500/50'}`}
                    >
                      {type.name || type.label}
                      {type.description && (
                        <span className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-2 w-max -translate-x-1/2 rounded-md bg-[var(--text-main)] px-2.5 py-1.5 text-xs text-[var(--bg-main)] opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
                          {type.description}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h3 className="mb-4 flex items-center gap-3 text-lg font-bold font-display text-[var(--text-main)]">
            <div className="p-1.5 bg-emerald-500/10 rounded-lg"><Target className="h-5 w-5 text-emerald-500" /></div>
            目标行为提示
          </h3>
          <div className="space-y-4">
            <div className="space-y-2">
              {config.prompts.map((prompt, index) => (
                <div key={index} className="flex items-center justify-between rounded-lg border border-[var(--border-glass-strong)] bg-[var(--bg-glass-strong)] px-4 py-2">
                  <span className="text-sm font-medium text-[var(--text-main)]">{prompt}</span>
                  <button type="button" onClick={() => removePrompt(prompt)} className="text-[var(--text-muted)] hover:text-rose-500 transition-colors">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={newPrompt}
                onChange={(e) => setNewPrompt(e.target.value)}
                placeholder="自定义核心敏感词/指令"
                onKeyDown={(e) => e.key === 'Enter' && addPrompt()}
                className="input-field flex-1"
              />
              <button type="button" onClick={addPrompt} className="btn-secondary"><Plus className="h-4 w-4" /></button>
            </div>
            <div className="flex flex-wrap gap-2 pt-2">
              {DEFAULT_PROMPTS.filter((p) => !config.prompts.includes(p)).map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => setConfig((prev) => ({ ...prev, prompts: [...prev.prompts, prompt] }))}
                  className="badge badge-neutral hover:border-emerald-500/50 hover:bg-emerald-500/5 transition-colors"
                >
                  + {prompt}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="mb-4 flex items-center gap-3 text-lg font-bold font-display text-[var(--text-main)]">
            <div className="p-1.5 bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] rounded-lg"><Settings className="h-5 w-5 text-[var(--text-main)]" /></div>
            引擎参数调优
          </h3>
          <div className="grid grid-cols-2 gap-5">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">组合迭代次数</label>
              <input type="number" min="1" max="100" value={config.iterations_per_combo} onChange={(e) => setConfig((prev) => ({ ...prev, iterations_per_combo: parseInt(e.target.value, 10) || 1 }))} className="input-field w-full" />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">并发管道数</label>
              <input type="number" min="1" max="10" value={config.max_concurrency} onChange={(e) => setConfig((prev) => ({ ...prev, max_concurrency: parseInt(e.target.value, 10) || 1 }))} className="input-field w-full" />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">判定阈值</label>
              <input type="number" min="0" max="1" step="0.1" value={config.success_threshold} onChange={(e) => setConfig((prev) => ({ ...prev, success_threshold: parseFloat(e.target.value) || 0.6 }))} className="input-field w-full" />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">对抗深度</label>
              <input type="number" min="1" max="100" value={config.max_iterations} onChange={(e) => setConfig((prev) => ({ ...prev, max_iterations: parseInt(e.target.value, 10) || 5 }))} className="input-field w-full" />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">Agent 模式</label>
              <select value={config.agent_mode} onChange={(e) => setConfig((prev) => ({ ...prev, agent_mode: e.target.value }))} className="input-field w-full">
                <option value="langchain">LangChain 多步循环</option>
                <option value="prompt">单轮 Prompt</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">工具步数</label>
              <input type="number" min="1" max="50" value={config.max_agent_steps} onChange={(e) => setConfig((prev) => ({ ...prev, max_agent_steps: parseInt(e.target.value, 10) || 5 }))} className="input-field w-full" />
            </div>
          </div>

          <div className="mt-5">
            <button type="button" onClick={() => setShowAdvanced((v) => !v)} className="flex items-center gap-2 text-sm font-bold text-[var(--accent-primary)]">
              {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              展开高级选项
            </button>
            <AnimatePresence>
              {showAdvanced && (
                <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="mt-4 space-y-4 overflow-hidden border-t border-[var(--border-glass)] pt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-xs font-bold text-[var(--text-muted)]">OLLAMA ENDPOINT</label>
                      <input type="text" value={config.base_url} onChange={(e) => setConfig((prev) => ({ ...prev, base_url: e.target.value }))} className="input-field w-full text-xs font-mono" />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-bold text-[var(--text-muted)]">OUTPUT DIRECTORY</label>
                      <input type="text" value={config.output_dir} onChange={(e) => setConfig((prev) => ({ ...prev, output_dir: e.target.value }))} className="input-field w-full text-xs font-mono" />
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      <div className="card p-6 bg-[var(--bg-glass-strong)] border-cyan-500/20 shadow-[inset_0_0_20px_rgba(6,182,212,0.05)]">
        <div className="flex items-center justify-between mb-4">
          <h3 className="flex items-center gap-3 text-lg font-bold font-display text-[var(--text-main)]">
            <BarChart3 className="h-5 w-5 text-cyan-500" /> 测试矩阵规模
          </h3>
          <span className="badge badge-info bg-cyan-500/10 text-cyan-500 border-cyan-500/20">
            <Clock className="h-3.5 w-3.5" /> 预计耗时: {Math.ceil(totalTests * (config.delay_between_tests + 10) / config.max_concurrency)} 秒
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-[var(--bg-glass)] border border-[var(--border-glass)] rounded-xl p-4 text-center">
            <div className="text-3xl font-mono font-bold text-[var(--text-main)]">{config.models.length}</div>
            <div className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mt-1">模型靶标</div>
          </div>
          <div className="bg-[var(--bg-glass)] border border-[var(--border-glass)] rounded-xl p-4 text-center">
            <div className="text-3xl font-mono font-bold text-[var(--text-main)]">{config.attack_types.length}</div>
            <div className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mt-1">攻击向量</div>
          </div>
          <div className="bg-[var(--bg-glass)] border border-[var(--border-glass)] rounded-xl p-4 text-center">
            <div className="text-3xl font-mono font-bold text-[var(--text-main)]">{config.prompts.length}</div>
            <div className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mt-1">核心词汇</div>
          </div>
          <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-xl p-4 text-center">
            <div className="text-3xl font-mono font-bold text-cyan-500 shadow-cyan-500/50 drop-shadow-md">{totalTests}</div>
            <div className="text-xs font-bold text-cyan-500 uppercase tracking-wider mt-1">组合总量</div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}