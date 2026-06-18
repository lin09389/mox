import { useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { Clock3, Download, Eye, FileText, Shield, TrendingUp, Trash2 } from 'lucide-react'
import { MetricCard, PageHeader, PanelHeader } from '../components/ui/AppFrame'

const seedReports = [
  { id: 1, report_name: 'GPT-4 安全评估报告', report_type: 'evaluation', model_name: 'gpt-4', attack_success_rate: 0.32, defense_success_rate: 0.85, created_at: '2026-03-31 10:30:00', format: 'html' },
  { id: 2, report_name: 'Claude 防御专项报告', report_type: 'defense', model_name: 'claude-3-opus', attack_success_rate: 0.15, defense_success_rate: 0.92, created_at: '2026-03-30 15:20:00', format: 'json' },
  { id: 3, report_name: '多模型基准报告', report_type: 'benchmark', model_name: 'abab2.5-chat', attack_success_rate: 0.45, defense_success_rate: 0.78, created_at: '2026-03-29 09:15:00', format: 'md' },
]

const typeLabel = {
  evaluation: '综合评估',
  defense: '防御专项',
  benchmark: '基准评测',
}

import { containerVariants, itemVariants } from '../utils/animations'

export default function ReportPage() {
  const [reports, setReports] = useState(seedReports)
  const [selected, setSelected] = useState(null)

  const stats = useMemo(() => {
    const total = reports.length
    const attack = total ? Math.round((reports.reduce((sum, item) => sum + item.attack_success_rate, 0) / total) * 100) : 0
    const defense = total ? Math.round((reports.reduce((sum, item) => sum + item.defense_success_rate, 0) / total) * 100) : 0
    return { total, attack, defense }
  }, [reports])

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="page-shell">
      <motion.div variants={itemVariants}>
        <PageHeader
          eyebrow="REPORT CENTER"
          title="评估报告中心"
          description="集中管理攻防评估结果，支持快速预览与导出。"
        />
      </motion.div>

      <motion.div variants={itemVariants} className="grid gap-4 md:grid-cols-3">
        <MetricCard icon={FileText} label="报告总数" value={stats.total} hint="当前存档数量" tone="electric" />
        <MetricCard icon={TrendingUp} label="平均攻击成功率" value={`${stats.attack}%`} hint="越高风险越大" tone="lava" />
        <MetricCard icon={Shield} label="平均防御成功率" value={`${stats.defense}%`} hint="越高越稳定" tone="neon" />
      </motion.div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <motion.section variants={itemVariants} className="card overflow-hidden">
          <div className="border-b border-[var(--border-glass)] bg-[var(--bg-glass-strong)] px-5 py-4">
            <h2 className="text-lg font-bold font-display text-[var(--text-main)]">报告列表</h2>
            <p className="mt-1 text-sm font-medium text-[var(--text-muted)]">按报告类型与模型查看历史结论。</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-[var(--text-main)]">
              <thead className="bg-[var(--bg-glass-strong)] text-[var(--text-muted)] font-bold uppercase tracking-wider text-xs border-b border-[var(--border-glass)]">
                <tr>
                  <th className="px-6 py-4">报告名称</th>
                  <th className="px-6 py-4">类型</th>
                  <th className="px-6 py-4">模型</th>
                  <th className="px-6 py-4 text-center">风险指标</th>
                  <th className="px-6 py-4">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-glass)]">
                {reports.map((report) => (
                  <motion.tr 
                    key={report.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className={`hover:bg-[var(--bg-glass)] transition-colors ${selected?.id === report.id ? 'bg-[var(--bg-glass-strong)] border-l-2 border-l-cyan-500' : ''}`}
                    onClick={() => setSelected(report)}
                  >
                    <td className="px-6 py-4 font-medium">{report.report_name}</td>
                    <td className="px-6 py-4">
                      <span className="badge badge-neutral bg-[var(--bg-glass-strong)] border-[var(--border-glass)]">{typeLabel[report.report_type] || report.report_type}</span>
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-[var(--text-muted)]">{report.model_name}</td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <span className="text-rose-500 font-mono font-bold" title="攻击成功率">{Math.round(report.attack_success_rate * 100)}%</span>
                        <span className="text-[var(--text-muted)]">/</span>
                        <span className="text-emerald-500 font-mono font-bold" title="防御成功率">{Math.round(report.defense_success_rate * 100)}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4" onClick={e => e.stopPropagation()}>
                      <div className="flex gap-2">
                        <button type="button" className="btn-secondary px-2.5 py-1.5 hover:text-cyan-500 hover:border-cyan-500/50" onClick={() => setSelected(report)}><Eye className="h-4 w-4" /></button>
                        <button type="button" className="btn-secondary px-2.5 py-1.5" onClick={() => toast.success(`开始下载 ${report.report_name}`)}><Download className="h-4 w-4" /></button>
                        <button
                          type="button"
                          className="btn-ghost px-2.5 py-1.5 text-rose-500 hover:bg-rose-500/10"
                          onClick={() => {
                            setReports((current) => current.filter((item) => item.id !== report.id))
                            setSelected((current) => (current?.id === report.id ? null : current))
                            toast.success('报告已删除。')
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
                {reports.length === 0 && (
                   <tr><td colSpan="5" className="p-8 text-center text-[var(--text-muted)] font-bold">暂无报告</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </motion.section>

        <motion.section variants={itemVariants} className="card bg-[var(--bg-glass-strong)] border-cyan-500/10 shadow-[inset_0_0_40px_rgba(6,182,212,0.03)] h-fit sticky top-6">
          <div className="border-b border-[var(--border-glass)] px-5 py-4">
             <h2 className="text-lg font-bold font-display text-[var(--text-main)] flex items-center gap-2"><Eye className="h-5 w-5 text-cyan-500" /> 报告预览</h2>
             <p className="mt-1 text-sm font-medium text-[var(--text-muted)]">选中左侧任一报告查看关键摘要。</p>
          </div>
          
          <AnimatePresence mode="wait">
            {selected ? (
              <motion.div 
                key={selected.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="p-5 space-y-5"
              >
                <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-5 shadow-sm">
                  <h3 className="text-base font-bold text-[var(--text-main)] mb-1">{selected.report_name}</h3>
                  <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-muted)] mb-4">
                    <Clock3 className="h-3.5 w-3.5" /> {selected.created_at}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <span className="badge badge-info bg-cyan-500/10 text-cyan-500 border-cyan-500/20">{typeLabel[selected.report_type] || selected.report_type}</span>
                    <span className="badge badge-neutral bg-[var(--bg-glass-strong)] border-[var(--border-glass)] font-mono">{selected.model_name}</span>
                    <span className="badge badge-neutral bg-amber-500/10 text-amber-500 border-amber-500/20 uppercase tracking-widest text-[10px]">{selected.format}</span>
                  </div>
                </div>
                
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 text-center">
                    <TrendingUp className="h-6 w-6 text-rose-500 mx-auto mb-2" />
                    <div className="text-2xl font-mono font-bold text-rose-500">{Math.round(selected.attack_success_rate * 100)}%</div>
                    <div className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)] mt-1">攻击成功率</div>
                  </div>
                  <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 text-center">
                    <Shield className="h-6 w-6 text-emerald-500 mx-auto mb-2" />
                    <div className="text-2xl font-mono font-bold text-emerald-500">{Math.round(selected.defense_success_rate * 100)}%</div>
                    <div className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)] mt-1">防御成功率</div>
                  </div>
                </div>

                <button onClick={() => toast.success(`开始下载 ${selected.report_name}`)} className="btn-primary w-full bg-cyan-500 hover:bg-cyan-600 border-cyan-500 text-white shadow-[0_0_15px_rgba(6,182,212,0.3)]">
                   <Download className="h-4 w-4" /> 完整导出报告
                </button>
              </motion.div>
            ) : (
              <motion.div 
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col min-h-[300px] items-center justify-center p-8 text-center"
              >
                <div className="w-16 h-16 rounded-2xl bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] flex items-center justify-center mb-4">
                  <FileText className="h-8 w-8 text-[var(--text-muted)] opacity-50" />
                </div>
                <p className="text-sm font-bold text-[var(--text-muted)] opacity-80">
                  从左侧报告列表选择一项查看详情。
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.section>
      </div>
    </motion.div>
  )
}
