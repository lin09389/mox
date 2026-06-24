import { useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bot, Play, Shield, Skull, Target } from 'lucide-react'
import toast from 'react-hot-toast'
import { runRedTeam } from '../api/security'
import { useLocalStorage } from '../hooks/useLocalStorage'
import { HubPanelIntro } from '../context/HubContext'
import { MetricCard, PanelHeader, ProgressMeter } from '../components/ui/AppFrame'
import ModelSelect from '../components/ui/ModelSelect'
import RunCompleteBanner from '../components/ui/RunCompleteBanner'
import { PingButton } from '../components/ui/PingButton'
import { AgentExecutionCard } from '../components/attack'
import { WorkspacePageShell, WorkspaceRunButton, WorkspaceTypeCard } from '../components/workspace'
import { itemVariants } from '../utils/animations'

const BASIC_TECHNIQUES = [
  { id: 'prompt_injection', name: '提示词注入', description: '直接覆盖或绕过系统约束。' },
  { id: 'jailbreak', name: '越狱攻击', description: '通过角色扮演突破模型边界。' },
  { id: 'role_play', name: '角色诱导', description: '诱导模型切换高风险角色。' },
  { id: 'encoding', name: '编码绕过', description: '利用编码和混淆规避过滤器。' },
  { id: 'context_injection', name: '上下文注入', description: '通过外部上下文影响响应。' },
  { id: 'chain_of_thought', name: '推理链窃取', description: '尝试提取推理细节与内部逻辑。' },
]

const AGENT_TECHNIQUES = [
  { id: 'tool_abuse', name: '工具滥用', description: '诱导 Agent 调用危险工具。' },
  { id: 'tool_chaining', name: '工具链攻击', description: '串联多步工具调用形成渗透链。' },
  { id: 'indirect_injection', name: '间接工具注入', description: '通过外部文档注入恶意指令。' },
  { id: 'agent_tool_manipulation', name: '工具操纵', description: '误导 Agent 选择不当工具。' },
  { id: 'privilege_escalation', name: '权限提升', description: '诱导 Agent 执行高权限动作。' },
  { id: 'agent_data_exfiltration', name: '数据外传', description: '读取敏感数据并发送到外部端点。' },
  { id: 'tool_confusion', name: '工具混淆', description: '混淆工具描述诱导错误调用。' },
  { id: 'multi_agent', name: '多 Agent 协同', description: '利用多 Agent 链路完成渗透。' },
]

const TECHNIQUES = [...BASIC_TECHNIQUES, ...AGENT_TECHNIQUES]
const AGENT_TECHNIQUE_IDS = new Set(AGENT_TECHNIQUES.map((item) => item.id))

export default function RedTeamPage() {
  const [results, setResults] = useState([])
  const [reportId, setReportId] = useState(null)
  const [running, setRunning] = useState(false)
  const [targetModel, setTargetModel] = useLocalStorage('mox_redteam_model', 'qwen3:4b')
  const [attackerModel, setAttackerModel] = useLocalStorage('mox_redteam_attacker_model', '')
  const [judgeModel, setJudgeModel] = useLocalStorage('mox_redteam_judge_model', '')
  const [selected, setSelected] = useLocalStorage('mox_redteam_techniques', TECHNIQUES.map((item) => item.id))
  const [hybridMode, setHybridMode] = useLocalStorage('mox_redteam_hybrid', true)
  const [agentMode, setAgentMode] = useLocalStorage('mox_redteam_agent_mode', 'langchain')
  const [maxAgentSteps, setMaxAgentSteps] = useLocalStorage('mox_redteam_max_agent_steps', 5)

  const hasAgentTechniques = useMemo(
    () => selected.some((id) => AGENT_TECHNIQUE_IDS.has(id)),
    [selected]
  )

  const successCount = useMemo(() => results.filter((item) => item.success).length, [results])
  const successRate = useMemo(
    () => (results.length ? Math.round((successCount / results.length) * 100) : 0),
    [results.length, successCount]
  )

  const toggle = (id) => {
    setSelected((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id]
    )
  }

  const handleRun = async () => {
    setRunning(true)
    setResults([])
    setReportId(null)
    try {
      const { results: data, reportId: savedReportId } = await runRedTeam(targetModel, selected, {
        attackerModel: attackerModel || undefined,
        judgeModel: judgeModel || undefined,
        judgeMode: hybridMode ? 'hybrid' : 'pattern',
        agentMode: hasAgentTechniques ? agentMode : undefined,
        maxAgentSteps: hasAgentTechniques ? maxAgentSteps : undefined,
      })
      setResults(data)
      setReportId(savedReportId)
      if (data.length > 0) {
        toast.success(savedReportId ? '红队演练已完成，报告已入库。' : '红队演练已完成。')
      }
    } catch {
      toast.error('红队演练失败，请检查后端连接与模型配置。')
    } finally {
      setRunning(false)
    }
  }

  const renderTechniqueGroup = (title, items) => (
    <div className="space-y-3">
      <p className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)]">{title}</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((technique) => {
          const active = selected.includes(technique.id)
          return (
            <WorkspaceTypeCard
              key={technique.id}
              active={active}
              onClick={() => toggle(technique.id)}
              title={technique.name}
              description={technique.description}
            />
          )
        })}
      </div>
    </div>
  )

  return (
    <WorkspacePageShell>
      <HubPanelIntro description="按攻击技术组合进行红队压力测试，支持三模型评判与 LangChain Agent 真实工具循环。" />

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <motion.section variants={itemVariants} className="card p-6 h-fit lg:sticky lg:top-6">
          <PanelHeader title="演练配置" description="选择模型与技术组合，执行一轮红队演练。" />
          <div className="space-y-6">
            <div className="space-y-4">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest block">三模型配置</label>
              <div className="grid gap-4 sm:grid-cols-1">
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest">目标模型</label>
                  <div className="flex items-center gap-2">
                    <div className="flex-1">
                      <ModelSelect value={targetModel} onChange={setTargetModel} />
                    </div>
                    <PingButton targetModel={targetModel} />
                  </div>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest">攻击模型（可选）</label>
                    <ModelSelect value={attackerModel || targetModel} onChange={setAttackerModel} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest">评判模型（可选）</label>
                    <ModelSelect value={judgeModel || targetModel} onChange={setJudgeModel} />
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest flex justify-between">
                <span>攻击技术向量</span>
                <span className="text-cyan-500">{selected.length} / {TECHNIQUES.length} 已选</span>
              </label>
              {renderTechniqueGroup('基础攻击', BASIC_TECHNIQUES)}
              {renderTechniqueGroup('Agent 攻击（LangChain 工具循环）', AGENT_TECHNIQUES)}
            </div>

            <div className="grid gap-5 p-4 rounded-xl border border-[var(--border-glass)] bg-[var(--bg-glass-strong)]">
              <div className="flex flex-col justify-center">
                <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">混合裁判模式</label>
                <div className="mt-3 flex items-center gap-3">
                  <div
                    className={`relative inline-flex h-5 w-9 cursor-pointer items-center rounded-full transition-colors ${hybridMode ? 'bg-cyan-500' : 'bg-[var(--border-glass-strong)]'}`}
                    onClick={() => setHybridMode(!hybridMode)}
                  >
                    <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${hybridMode ? 'translate-x-4.5' : 'translate-x-1'}`} />
                  </div>
                  <span className="text-xs font-bold text-[var(--text-main)]">
                    {hybridMode ? 'hybrid（规则 + LLM 评判）' : 'pattern（仅规则）'}
                  </span>
                </div>
              </div>

              {hasAgentTechniques && (
                <div className="grid gap-4 sm:grid-cols-2 pt-2 border-t border-[var(--border-glass)]">
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest flex items-center gap-1.5">
                      <Bot className="h-3.5 w-3.5" />
                      Agent 模式
                    </label>
                    <select
                      value={agentMode}
                      onChange={(e) => setAgentMode(e.target.value)}
                      className="input-field w-full"
                    >
                      <option value="langchain">langchain（真实工具循环）</option>
                      <option value="prompt">prompt（仅 Prompt 模拟）</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">最大 Agent 步数</label>
                    <input
                      type="number"
                      min="1"
                      max="50"
                      value={maxAgentSteps}
                      onChange={(e) => setMaxAgentSteps(parseInt(e.target.value, 10) || 5)}
                      className="input-field w-full"
                    />
                  </div>
                </div>
              )}
            </div>

            <WorkspaceRunButton
              type="button"
              onClick={handleRun}
              disabled={running || selected.length === 0}
              loading={running}
              icon={Play}
              loadingText="正在执行红队演练..."
            >
              启动演练
            </WorkspaceRunButton>
          </div>
        </motion.section>

        <motion.section variants={itemVariants} className="card p-6 bg-gradient-to-br from-[var(--bg-glass-strong)] to-[var(--bg-glass)] border-[var(--border-glass)]">
          <PanelHeader title="演练结果" description="关注成功率、Agent 工具链与失败场景分布。" />

          <AnimatePresence mode="wait">
            {results.length ? (
              <motion.div
                key="results"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="space-y-6"
              >
                <RunCompleteBanner reportId={reportId} title="演练报告已保存" />

                <div className="grid gap-4 sm:grid-cols-3">
                  <MetricCard icon={Target} label="技术总数" value={results.length} hint="本轮执行项" tone="electric" />
                  <MetricCard icon={Skull} label="攻击成功" value={successCount} hint={`${successRate}%`} tone="lava" />
                  <MetricCard icon={Shield} label="攻击失败" value={results.length - successCount} hint={`${100 - successRate}%`} tone="neon" />
                </div>

                <div className="p-5 rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)]">
                  <ProgressMeter value={successRate} tone={successRate >= 40 ? 'warning' : 'success'} label="攻击成功率 (渗透率)" />
                </div>

                <div className="space-y-4 pt-2">
                  <h4 className="text-sm font-bold font-display text-[var(--text-main)] mb-2 flex items-center gap-2">
                    <Target className="h-4 w-4 text-rose-500" />
                    渗透链路追踪
                  </h4>
                  {results.map((item, index) => (
                    <motion.div
                      key={`${item.technique}-${index}`}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className={`rounded-xl border p-4 transition-all space-y-3 ${item.success ? 'bg-rose-500/5 border-rose-500/20 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-rose-500/10' : 'bg-[var(--bg-glass)] border-[var(--border-glass)] opacity-80'}`}
                    >
                      <div className="flex items-center justify-between">
                        <p className={`text-sm font-bold font-mono ${item.success ? 'text-rose-500' : 'text-[var(--text-main)]'}`}>
                          {item.technique || item.scenario}
                        </p>
                        <span className={`badge border font-bold uppercase tracking-widest text-[10px] ${item.success ? 'bg-rose-500/10 text-rose-500 border-rose-500/20' : 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'}`}>
                          {item.success ? '防线击穿' : '防御成功'}
                        </span>
                      </div>
                      <p className="text-xs font-medium text-[var(--text-muted)] leading-relaxed bg-[var(--bg-main)]/50 p-2 rounded-lg">
                        {item.scenario || item.scenario_name || '未返回场景描述'}
                      </p>
                      {item.agent_execution && (
                        <AgentExecutionCard execution={item.agent_execution} />
                      )}
                    </motion.div>
                  ))}
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
                  {running ? (
                    <div className="w-10 h-10 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
                  ) : (
                    <Target className="h-10 w-10 text-[var(--text-muted)] opacity-60" />
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[var(--text-main)]">{running ? '演练执行中...' : '系统就绪'}</h3>
                  <p className="mt-2 text-sm font-medium text-[var(--text-muted)] max-w-sm">
                    {running
                      ? '正在组装红队攻击向量矩阵对目标模型进行压力渗透测试，请耐心等待。'
                      : '尚未运行红队演练，请配置左侧演练环境并启动。'}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.section>
      </div>
    </WorkspacePageShell>
  )
}