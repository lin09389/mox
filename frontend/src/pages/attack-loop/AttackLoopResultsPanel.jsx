import { motion } from 'framer-motion'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Database,
  Download,
  Shield,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  Cell,
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import RunCompleteBanner from '../../components/ui/RunCompleteBanner'
import { CHART_COLORS, ChartTooltip } from './chartUtils'

export default function AttackLoopResultsPanel({
  results,
  reportId,
  chartMetric,
  setChartMetric,
  modelChartData,
  attackChartData,
  onDownload,
}) {
  return (
    <motion.div
      key="results"
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      className="space-y-6"
    >
      {results ? (
        <>
          <RunCompleteBanner reportId={reportId} title="攻击循环报告已保存" />
          <div className="card p-6">
            <h3 className="mb-5 flex items-center gap-3 text-lg font-bold font-display text-[var(--text-main)]">
              <div className="p-1.5 bg-cyan-500/10 rounded-lg"><BarChart3 className="h-5 w-5 text-cyan-500" /></div>
              全局安全评级
            </h3>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="rounded-2xl bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] p-5 text-center">
                <div className="text-3xl font-mono font-bold text-[var(--text-main)]">{results.total_tests}</div>
                <div className="mt-2 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">测试样本量</div>
              </div>
              <div className="rounded-2xl bg-[var(--bg-glass-strong)] border border-emerald-500/20 p-5 text-center">
                <div className="text-3xl font-mono font-bold text-emerald-500">{results.successful_tests}</div>
                <div className="mt-2 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">防御成功</div>
              </div>
              <div className="rounded-2xl bg-[var(--bg-glass-strong)] border border-rose-500/20 p-5 text-center">
                <div className="text-3xl font-mono font-bold text-rose-500">{results.failed_tests}</div>
                <div className="mt-2 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">防线失守</div>
              </div>
              <div className="rounded-2xl bg-[var(--bg-glass-strong)] border border-cyan-500/20 p-5 text-center shadow-[inset_0_0_20px_rgba(6,182,212,0.05)]">
                <div className="text-3xl font-mono font-bold text-cyan-500">{(results.success_rate * 100).toFixed(1)}%</div>
                <div className="mt-2 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">攻击成功率</div>
              </div>
            </div>
          </div>

          {modelChartData.length > 0 && (
            <div className="card p-6">
              <div className="mb-6 flex items-center justify-between border-b border-[var(--border-glass)] pb-4">
                <h3 className="flex items-center gap-3 text-lg font-bold font-display text-[var(--text-main)]">
                  <Database className="h-5 w-5 text-cyan-500" /> 多模型鲁棒性对比
                </h3>
                <div className="flex rounded-lg bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] p-1">
                  <button type="button" onClick={() => setChartMetric('success_rate')} className={`rounded-md px-4 py-1.5 text-xs font-bold transition-all ${chartMetric === 'success_rate' ? 'bg-cyan-500 text-white shadow-sm' : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'}`}>成功率 %</button>
                  <button type="button" onClick={() => setChartMetric('avg_score')} className={`rounded-md px-4 py-1.5 text-xs font-bold transition-all ${chartMetric === 'avg_score' ? 'bg-cyan-500 text-white shadow-sm' : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'}`}>风险评分</button>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={modelChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 12, fontWeight: 600 }} axisLine={{ stroke: 'var(--border-glass-strong)' }} tickLine={false} />
                  <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={{ stroke: 'var(--border-glass-strong)' }} tickLine={false} domain={[0, 100]} unit="%" />
                  <Tooltip content={<ChartTooltip />} cursor={{ fill: 'var(--bg-glass-strong)' }} />
                  <Legend wrapperStyle={{ fontSize: 12, fontWeight: 600, color: 'var(--text-main)' }} />
                  <Bar dataKey={chartMetric} name={chartMetric === 'success_rate' ? '破防率 (%)' : '威胁评分 (×100)'} radius={[8, 8, 0, 0]} maxBarSize={60}>
                    {modelChartData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {attackChartData.length > 0 && (
            <div className="card p-6">
              <h3 className="mb-6 flex items-center gap-3 text-lg font-bold font-display text-[var(--text-main)] border-b border-[var(--border-glass)] pb-4">
                <Shield className="h-5 w-5 text-rose-500" /> 攻击类型杀伤力雷达图
              </h3>
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={attackChartData} cx="50%" cy="50%" outerRadius="70%">
                  <PolarGrid stroke="var(--border-glass-strong)" />
                  <PolarAngleAxis dataKey="name" tick={{ fill: 'var(--text-main)', fontSize: 12, fontWeight: 600 }} />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Legend wrapperStyle={{ fontSize: 12, fontWeight: 600 }} />
                  <Radar name="成功率 (%)" dataKey="success_rate" stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.3} strokeWidth={2} />
                  <Radar name="风险分 (×100)" dataKey="avg_score" stroke="#0ea5e9" fill="#0ea5e9" fillOpacity={0.2} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}

          {results.agent_execution_summary && (
            <div className="card p-6">
              <h3 className="mb-5 flex items-center gap-3 text-lg font-bold font-display text-[var(--text-main)]">
                <Activity className="h-5 w-5 text-cyan-500" /> Agent 工具执行摘要
              </h3>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
                <div className="rounded-2xl bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] p-5 text-center">
                  <div className="text-3xl font-mono font-bold text-[var(--text-main)]">{results.agent_execution_summary.total_with_tools || 0}</div>
                  <div className="mt-2 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">含工具调用</div>
                </div>
                <div className="rounded-2xl bg-[var(--bg-glass-strong)] border border-rose-500/20 p-5 text-center">
                  <div className="text-3xl font-mono font-bold text-rose-500">{results.agent_execution_summary.policy_bypassed || 0}</div>
                  <div className="mt-2 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">策略绕过</div>
                </div>
                <div className="rounded-2xl bg-[var(--bg-glass-strong)] border border-cyan-500/20 p-5 text-center">
                  <div className="text-3xl font-mono font-bold text-cyan-500">{results.agent_execution_summary.langchain_runs || 0}</div>
                  <div className="mt-2 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">LangChain 运行</div>
                </div>
              </div>
              {results.agent_execution_runs?.length > 0 && (
                <div className="mt-5 space-y-2 max-h-64 overflow-y-auto">
                  {results.agent_execution_runs.slice(0, 12).map((run) => (
                    <div key={run.test_id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] px-4 py-3 text-sm">
                      <span className="font-mono text-[var(--text-main)]">{run.attack_name || run.attack_type}</span>
                      <span className="text-xs text-[var(--text-muted)]">{run.model}</span>
                      <span className="badge border font-mono text-xs bg-cyan-500/10 text-cyan-500 border-cyan-500/20">{run.agent_mode || '-'}</span>
                      <span className="text-xs text-[var(--text-muted)]">{(run.tool_calls || []).join(', ') || '无工具'}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {results.top_dangerous_attacks?.length > 0 && (
            <div className="card p-6 border-rose-500/20 bg-[linear-gradient(135deg,var(--bg-glass)_0%,rgba(244,63,94,0.05)_100%)]">
              <h3 className="mb-5 flex items-center gap-3 text-lg font-bold font-display text-[var(--text-main)]">
                <AlertTriangle className="h-5 w-5 text-rose-500" /> TOP5 最危险攻击载荷
              </h3>
              <div className="space-y-3">
                {results.top_dangerous_attacks.slice(0, 5).map((attack, index) => (
                  <div key={attack.type} className="flex items-center gap-4 rounded-xl border border-rose-500/10 bg-[var(--bg-glass-strong)] p-4 shadow-sm transition-transform hover:-translate-y-0.5">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 text-sm font-bold text-rose-500 font-mono">
                      0{index + 1}
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-bold text-[var(--text-main)] mb-1">{attack.name}</div>
                      <div className="text-xs font-mono text-[var(--text-muted)] bg-[var(--bg-main)] px-2 py-1 rounded inline-block">{attack.type}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-mono font-bold text-rose-500">{attack.success_rate?.toFixed(1)}%</div>
                      <div className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)] mt-1">突破概率</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="card p-6 flex flex-col sm:flex-row items-center justify-between gap-4 bg-cyan-500/5 border-cyan-500/20">
            <h3 className="flex items-center gap-3 text-base font-bold text-[var(--text-main)]">
              <Download className="h-5 w-5 text-cyan-500" /> 导出渗透报告
            </h3>
            <div className="flex flex-wrap gap-3">
              {['json', 'csv', 'html', 'txt'].map((fmt) => (
                <button key={fmt} type="button" onClick={() => onDownload(fmt)} className="btn-secondary px-4 py-2 text-xs font-bold uppercase tracking-wider hover:bg-cyan-500/10 hover:text-cyan-500 hover:border-cyan-500/30">
                  {fmt}
                </button>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="card p-16 flex flex-col items-center text-center opacity-60 border-dashed">
          <BarChart3 className="h-12 w-12 text-[var(--text-muted)] mb-4" />
          <h3 className="text-lg font-bold text-[var(--text-main)]">暂无分析数据</h3>
          <p className="mt-2 text-sm font-medium text-[var(--text-muted)]">编排任务完成后，渗透测试报告将在此呈现。</p>
        </div>
      )}
    </motion.div>
  )
}