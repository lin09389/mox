import { useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { AlertTriangle, Bot, Play, Shield, Wrench, Zap } from 'lucide-react'
import api from '../api'
import { MetricCard, PageHeader, PanelHeader, ProgressMeter } from '../components/ui/AppFrame'

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
    summary: risk > 0.65 ? '检测到工具链可被利用路径。' : '当前策略已拦截主要攻击链路。',
  }
}

export default function AgentAttackPage() {
  const [attackType, setAttackType] = useState('tool_chaining')
  const [target, setTarget] = useState('')
  const [model, setModel] = useState('qwen3:4b')
  const [selectedTools, setSelectedTools] = useState(['read_file', 'http_request'])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const selectedAttack = useMemo(() => ATTACK_TYPES.find((item) => item.id === attackType), [attackType])
  const riskPercent = Math.round((result?.risk_score || 0) * 100)

  const toggleTool = (name) => {
    setSelectedTools((current) =>
      current.includes(name) ? current.filter((item) => item !== name) : [...current, name]
    )
  }

  const runAttack = async () => {
    if (!target.trim()) {
      toast.error('请输入目标任务描述。')
      return
    }

    setLoading(true)
    setResult(null)
    try {
      const response = await api.post('/api/v2/attacks/agent', {
        attack_type: attackType,
        target,
        model_name: model,
        tools: selectedTools,
      })
      setResult(response.data)
      toast.success('Agent 攻击测试已完成。')
    } catch {
      setResult(buildDemoResult(attackType, selectedTools))
      toast('后端不可用，已展示演示结果。', { icon: '⚠️' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="AGENT ATTACK"
        title="Agent 攻击测试中心"
        description="围绕工具调用、权限边界和多 Agent 协同链路进行专项攻击验证。"
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <section className="card card-glow">
          <PanelHeader title="攻击配置" description="选择攻击类型、模型和可用工具后发起测试。" />
          <div className="space-y-5">
            <div className="grid gap-3 sm:grid-cols-2">
              {ATTACK_TYPES.map((item) => {
                const active = attackType === item.id
                return (
                  <button
                    type="button"
                    key={item.id}
                    onClick={() => setAttackType(item.id)}
                    className={`rounded-[18px] border px-4 py-4 text-left transition-all ${
                      active ? 'border-electric-200 bg-electric-900/80' : 'border-graphite-200/70 bg-white/75'
                    }`}
                  >
                    <p className="text-sm font-semibold text-graphite-900">{item.name}</p>
                    <p className="mt-1 text-xs text-graphite-500">{item.desc}</p>
                  </button>
                )
              })}
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="label">目标模型</label>
                <input className="input-field" value={model} onChange={(event) => setModel(event.target.value)} />
              </div>
              <div>
                <label className="label">目标任务</label>
                <input className="input-field" value={target} onChange={(event) => setTarget(event.target.value)} placeholder="例如：访问数据库并发送邮件" />
              </div>
            </div>

            <div>
              <label className="label">可用工具</label>
              <div className="grid gap-2 sm:grid-cols-2">
                {TOOLS.map((tool) => (
                  <button
                    key={tool.name}
                    type="button"
                    onClick={() => toggleTool(tool.name)}
                    className={`rounded-[14px] border px-3 py-2 text-left text-sm transition-all ${
                      selectedTools.includes(tool.name)
                        ? tool.danger
                          ? 'border-lava-200 bg-lava-900/70'
                          : 'border-electric-200 bg-electric-900/70'
                        : 'border-graphite-200/70 bg-white/75'
                    }`}
                  >
                    {tool.name}
                  </button>
                ))}
              </div>
            </div>

            <button type="button" onClick={runAttack} disabled={loading} className="btn-primary w-full justify-center py-3">
              <Play className="h-4 w-4" />
              {loading ? '正在执行 Agent 攻击' : '开始测试'}
            </button>
          </div>
        </section>

        <section className="card card-glow">
          <PanelHeader title="测试结果" description="关注风险分、攻击结果和危险工具暴露。" />
          {result ? (
            <div className="space-y-4">
              {result._demo_mode ? <div className="badge badge-warning">当前为演示结果</div> : null}
              <div className="grid gap-3 sm:grid-cols-3">
                <MetricCard icon={Bot} label="攻击类型" value={selectedAttack?.name || attackType} hint="当前策略" tone="electric" />
                <MetricCard icon={AlertTriangle} label="攻击结果" value={result.success ? '成功' : '失败'} hint="是否突破策略" tone={result.success ? 'lava' : 'neon'} />
                <MetricCard icon={Shield} label="风险分" value={`${riskPercent}%`} hint="综合评估分" tone="warning" />
              </div>
              <ProgressMeter value={riskPercent} tone={result.success ? 'danger' : 'success'} label="风险热度" />
              <div className="rounded-[18px] border border-graphite-200/70 bg-white/80 p-4">
                <p className="text-sm font-semibold text-graphite-900">危险工具暴露</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {(result.risky_tools || []).length ? (
                    (result.risky_tools || []).map((item) => (
                      <span key={item} className="badge badge-danger">
                        <Wrench className="h-3.5 w-3.5" />
                        {item}
                      </span>
                    ))
                  ) : (
                    <span className="badge badge-success">未发现高危工具暴露</span>
                  )}
                </div>
              </div>
              <div className="rounded-[18px] border border-graphite-200/70 bg-white/80 p-4">
                <p className="text-sm font-semibold text-graphite-900">结论</p>
                <p className="mt-2 text-sm text-graphite-600">{result.summary || '未返回结论信息。'}</p>
              </div>
            </div>
          ) : (
            <div className="panel-muted flex min-h-[380px] items-center justify-center text-sm text-graphite-500">
              运行测试后，这里会显示 Agent 攻击结果。
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
