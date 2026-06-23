import { useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { AlertTriangle, Bot, Play, Shield, Wrench, Zap, Loader2 } from 'lucide-react'
import { attackApi, isDemoModeEnabled } from '../api'
import { MetricCard, PanelHeader, ProgressMeter } from '../components/ui/AppFrame'
import ModelSelect from '../components/ui/ModelSelect'
import { HubPanelIntro } from '../context/HubContext'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'

const ATTACK_TYPES = [
  { id: 'tool_chaining', name: '工具链攻击', desc: '组合多个工具调用实现危险路径。' },
  { id: 'indirect_injection', name: '间接注入', desc: '通过外部数据源注入恶意指令。' },
  { id: 'privilege_escalation', name: '权限提升', desc: '诱导 Agent 执行更高权限动作。' },
  { id: 'tool_confusion', name: '工具混淆', desc: '误导 Agent 调用不应使用的工具。' },
  { id: 'data_exfiltration', name: '数据窃取', desc: '尝试让 Agent 泄露敏感信息。' },
  { id: 'multi_agent', name: '多 Agent 协同攻击', desc: '利用多 Agent 通信链路进行渗透。' },
]

const TOOLS = [
  { name: 'read_file', danger: false },
  { name: 'write_file', danger: true },
  { name: 'execute_code', danger: true },
  { name: 'http_request', danger: false },
  { name: 'database_query', danger: true },
  { name: 'send_email', danger: true },
]

function buildDemoResult(type, tools) {
  const risk = 0.45 + Math.random() * 0.45
  return {
    _demo_mode: true,
    attack_type: type,
    success: risk > 0.65,
    risk_score: Number(risk.toFixed(2)),
    risky_tools: tools.filter((item) => TOOLS.find((tool) => tool.name === item)?.danger),
    summary: risk > 0.65 ? '检测到工具链可被利用路径。Agent 在复杂指令下暴露了高危执行权限。' : '当前策略已拦截主要攻击链路，Agent 成功遵守了沙箱约束。',
  }
}

import { containerVariants, itemVariants } from '../utils/animations'

const agentSchema = z.object({
  attackType: z.string().min(1),
  model: z.string().min(1, '模型名称不可为空'),
  target: z.string().min(1, '请输入目标任务描述'),
  selectedTools: z.array(z.string()).min(1, '请至少选择一个工具'),
})

export default function AgentAttackPage() {
  const [result, setResult] = useState(null)

  const runAttackMutation = useMutation({
    mutationFn: async (payload) => {
      return attackApi.agentAttack(payload)
    }
  })

  const { register, handleSubmit, control, watch, setValue, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(agentSchema),
    defaultValues: {
      attackType: 'tool_chaining',
      model: 'qwen3:4b',
      target: '',
      selectedTools: ['read_file', 'http_request'],
    }
  })

  const watchAttackType = watch('attackType')
  const watchSelectedTools = watch('selectedTools')

  const selectedAttack = useMemo(() => ATTACK_TYPES.find((item) => item.id === watchAttackType), [watchAttackType])
  const riskPercent = Math.round((result?.risk_score || 0) * 100)

  const toggleTool = (name) => {
    if (watchSelectedTools.includes(name)) {
      setValue('selectedTools', watchSelectedTools.filter((item) => item !== name), { shouldValidate: true })
    } else {
      setValue('selectedTools', [...watchSelectedTools, name], { shouldValidate: true })
    }
  }

  const onSubmit = async (data) => {
    setResult(null)
    try {
      const payload = {
        attack_type: data.attackType,
        target: data.target,
        model_name: data.model,
        tools: data.selectedTools,
      }
      const responseData = await runAttackMutation.mutateAsync(payload)
      setResult(responseData)
      toast.success('Agent 攻击测试已完成。')
    } catch {
      if (!isDemoModeEnabled) {
        toast.error('Agent 攻击测试失败，请检查后端连接。')
        return
      }
      setTimeout(() => {
        setResult(buildDemoResult(data.attackType, data.selectedTools))
        toast('后端不可用，已展示演示结果。', { icon: '⚠️' })
      }, 1500)
    }
  }

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="page-shell">
      <HubPanelIntro description="围绕 Agent 工具调用流、权限边界突破和多智能体协同链路进行深度安全验证。" />

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <motion.section variants={itemVariants} className="card p-6 h-fit lg:sticky lg:top-6">
          <PanelHeader title="攻击配置面板" description="组装攻击链路矩阵，测试智能体防御纵深。" />
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="space-y-3">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">智能体攻击类型</label>
              <div className="grid gap-3 sm:grid-cols-2">
                {ATTACK_TYPES.map((item) => {
                  const active = watchAttackType === item.id
                  return (
                    <button
                      type="button"
                      key={item.id}
                      onClick={() => setValue('attackType', item.id, { shouldValidate: true })}
                      className={`rounded-xl border p-3 text-left transition-all duration-300 ${
                        active ? 'border-cyan-500/50 bg-cyan-500/10 shadow-[inset_0_0_15px_rgba(6,182,212,0.1)] transform scale-[1.02]' : 'border-[var(--border-glass)] bg-[var(--bg-glass)] hover:bg-[var(--bg-glass-strong)] hover:border-cyan-500/30'
                      }`}
                    >
                      <p className={`text-sm font-bold font-display mb-1 ${active ? 'text-cyan-500' : 'text-[var(--text-main)]'}`}>{item.name}</p>
                      <p className={`text-xs font-medium ${active ? 'text-cyan-500/70' : 'text-[var(--text-muted)]'}`}>{item.desc}</p>
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">基座模型</label>
                <Controller
                  name="model"
                  control={control}
                  render={({ field }) => (
                    <ModelSelect value={field.value} onChange={field.onChange} className={errors.model ? '[&_select]:border-rose-500/50' : ''} />
                  )}
                />
                {errors.model && <p className="text-xs text-rose-500">{errors.model.message}</p>}
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">最终诱导目标</label>
                <input className={`input-field ${errors.target ? 'border-rose-500/50' : ''}`} {...register('target')} placeholder="例如：篡改数据库权限并发送隐蔽邮件..." />
                {errors.target && <p className="text-xs text-rose-500">{errors.target.message}</p>}
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest flex items-center justify-between">
                <span>注册挂载工具</span>
                <span className="text-cyan-500">{watchSelectedTools.length} / {TOOLS.length} 已挂载</span>
              </label>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {TOOLS.map((tool) => {
                  const active = watchSelectedTools.includes(tool.name)
                  return (
                    <button
                      key={tool.name}
                      type="button"
                      onClick={() => toggleTool(tool.name)}
                      className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-mono font-bold transition-all duration-200 ${
                        active
                          ? tool.danger
                            ? 'border-rose-500/50 bg-rose-500/10 text-rose-500 shadow-sm'
                            : 'border-cyan-500/50 bg-cyan-500/10 text-cyan-500 shadow-sm'
                          : 'border-[var(--border-glass-strong)] bg-transparent text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-glass)]'
                      }`}
                    >
                      {active && tool.danger && <Wrench className="h-3.5 w-3.5" />}
                      {tool.name}
                    </button>
                  )
                })}
              </div>
              {errors.selectedTools && <p className="text-xs text-rose-500">{errors.selectedTools.message}</p>}
            </div>

            <button 
              type="submit" 
              disabled={isSubmitting} 
              className="btn-primary w-full justify-center py-3 bg-cyan-500 hover:bg-cyan-600 border-cyan-500 text-white shadow-[0_0_20px_rgba(6,182,212,0.3)] text-base font-bold disabled:opacity-50 disabled:shadow-none"
            >
              {isSubmitting ? <Loader2 className="h-5 w-5 animate-spin" /> : <Play className="h-5 w-5" />}
              {isSubmitting ? '正在执行越权渗透测试...' : '启动渗透链路'}
            </button>
          </form>
        </motion.section>

        <motion.section variants={itemVariants} className="card p-6 bg-[var(--bg-glass-strong)] border-[var(--border-glass)] shadow-[inset_0_0_40px_rgba(6,182,212,0.02)]">
          <PanelHeader title="实战分析报告" description="评估智能体沙箱隔离、工具混淆与数据窃取风险。" />
          
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div 
                key="result"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="space-y-6"
              >
                {result._demo_mode && (
                  <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-3 flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                    <span className="text-xs font-bold text-amber-500 tracking-wide">演示模式：本地沙箱推演</span>
                  </div>
                )}
                
                <div className="grid gap-4 sm:grid-cols-3">
                  <MetricCard icon={Bot} label="主要渗透向量" value={selectedAttack?.name || watchAttackType} hint="执行载荷策略" tone="electric" />
                  <MetricCard icon={AlertTriangle} label="沙箱突破状态" value={result.success ? '成功越权' : '防御拦截'} hint="是否破坏系统约束" tone={result.success ? 'lava' : 'neon'} />
                  <MetricCard icon={Shield} label="风险评估分" value={`${riskPercent}%`} hint="综合破坏力" tone="warning" />
                </div>
                
                <div className="p-5 rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)]">
                  <ProgressMeter value={riskPercent} tone={result.success ? 'danger' : 'success'} label="智能体暴露面风险指数" />
                </div>
                
                <div className="space-y-4 pt-2">
                  <h4 className="text-sm font-bold font-display text-[var(--text-main)] border-b border-[var(--border-glass)] pb-2 flex items-center gap-2"><Wrench className="h-4 w-4 text-[var(--text-muted)]" /> 敏感工具暴露追踪</h4>
                  <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-5">
                    <div className="flex flex-wrap gap-2">
                      {(result.risky_tools || []).length ? (
                        (result.risky_tools || []).map((item) => (
                          <span key={item} className="badge border font-mono tracking-wide bg-rose-500/10 text-rose-500 border-rose-500/20 px-3 py-1.5 flex items-center gap-1.5">
                            <Zap className="h-3.5 w-3.5" />
                            {item}
                          </span>
                        ))
                      ) : (
                        <span className="badge border font-bold bg-emerald-500/10 text-emerald-500 border-emerald-500/20 px-3 py-1.5">
                          沙箱隔离良好，未发现高危工具暴露
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-5">
                  <p className="text-sm font-bold text-[var(--text-main)] mb-2 flex items-center gap-2">
                    <AlertTriangle className={`h-4 w-4 ${result.success ? 'text-rose-500' : 'text-emerald-500'}`} />
                    分析结论
                  </p>
                  <p className="text-sm font-medium text-[var(--text-muted)] leading-relaxed bg-[var(--bg-main)]/50 p-3 rounded-lg border border-[var(--border-glass)]">
                    {result.summary || '未返回结论信息。'}
                  </p>
                </div>
              </motion.div>
            ) : (
              <motion.div 
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex min-h-[400px] flex-col items-center justify-center gap-4 text-center p-8"
              >
                <div className="w-20 h-20 rounded-full bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] flex items-center justify-center">
                  {isSubmitting ? (
                    <div className="w-10 h-10 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
                  ) : (
                    <Bot className="h-10 w-10 text-[var(--text-muted)] opacity-60" />
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[var(--text-main)]">{isSubmitting ? '渗透链路生成中...' : '智能体靶场就绪'}</h3>
                  <p className="mt-2 text-sm font-medium text-[var(--text-muted)] max-w-sm">
                    {isSubmitting ? '正在根据目标任务生成多步工具链载荷，尝试绕过大模型安全边界。' : '在左侧配置需要测试的恶意任务与开放接口，启动以验证 Agent 的工具调用安全性。'}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.section>
      </div>
    </motion.div>
  )
}
