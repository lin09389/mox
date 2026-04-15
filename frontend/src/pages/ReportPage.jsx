import { useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { Download, Eye, FileText, Shield, TrendingUp, Trash2 } from 'lucide-react'
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

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] } }
}

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
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="page-shell"
    >
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

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr] mt-2">
        <motion.section variants={itemVariants} className="card overflow-hidden !p-0">
          <div className="border-b border-graphite-200/50 bg-white/40 backdrop-blur-sm px-6 py-5">
            <PanelHeader title="报告列表" description="按报告类型与模型查看历史结论。" />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-graphite-50/50 text-graphite-500">
                <tr>
                  <th className="px-6 py-4 font-bold uppercase tracking-wider text-[11px]">报告名称</th>
                  <th className="px-6 py-4 font-bold uppercase tracking-wider text-[11px]">类型</th>
                  <th className="px-6 py-4 font-bold uppercase tracking-wider text-[11px]">模型</th>
                  <th className="px-6 py-4 font-bold uppercase tracking-wider text-[11px]">攻击成功率</th>
                  <th className="px-6 py-4 font-bold uppercase tracking-wider text-[11px]">防御成功率</th>
                  <th className="px-6 py-4 font-bold uppercase tracking-wider text-[11px]">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-graphite-100 bg-white/30 backdrop-blur-sm">
                {reports.map((report) => (
                  <tr key={report.id} className="transition-colors hover:bg-white/60">
                    <td className="px-6 py-4 font-bold text-graphite-900">{report.report_name}</td>
                    <td className="px-6 py-4"><span className="badge border border-graphite-200 text-graphite-700 bg-white shadow-sm">{typeLabel[report.report_type] || report.report_type}</span></td>
                    <td className="px-6 py-4 font-medium text-graphite-600">{report.model_name}</td>
                    <td className="px-6 py-4 font-bold text-lava-600">{Math.round(report.attack_success_rate * 100)}%</td>
                    <td className="px-6 py-4 font-bold text-neon-600">{Math.round(report.defense_success_rate * 100)}%</td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button type="button" className="btn-secondary !px-2.5 !py-2" onClick={() => setSelected(report)}><Eye className="h-4 w-4" /></button>
                        <button type="button" className="btn-secondary !px-2.5 !py-2" onClick={() => toast.success(`开始下载 ${report.report_name}`)}><Download className="h-4 w-4" /></button>
                        <button
                          type="button"
                          className="btn-danger !px-2.5 !py-2"
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
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.section>

        <motion.section variants={itemVariants} className="card relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-electric-50/20 to-transparent pointer-events-none group-hover:opacity-100 opacity-0 transition-opacity duration-700" />
          <div className="relative z-10">
            <PanelHeader title="报告预览" description="选中左侧任一报告查看关键摘要。" />
            {selected ? (
              <div className="space-y-5">
                <div className="rounded-2xl border border-white/80 bg-white/60 p-5 shadow-sm backdrop-blur-md">
                  <p className="text-base font-bold text-graphite-950">{selected.report_name}</p>
                  <p className="mt-1 text-xs font-medium text-graphite-500">{selected.created_at}</p>
                  <div className="mt-4 flex flex-wrap gap-2.5">
                    <span className="badge border border-graphite-200 text-graphite-700 bg-white shadow-sm">{typeLabel[selected.report_type] || selected.report_type}</span>
                    <span className="badge border border-electric-200 text-electric-700 bg-electric-900/50 shadow-sm">{selected.model_name}</span>
                    <span className="badge border border-graphite-200 text-graphite-500 bg-graphite-50 shadow-sm uppercase tracking-widest">{selected.format}</span>
                  </div>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <MetricCard icon={TrendingUp} label="攻击成功率" value={`${Math.round(selected.attack_success_rate * 100)}%`} hint="越低越好" tone="lava" />
                  <MetricCard icon={Shield} label="防御成功率" value={`${Math.round(selected.defense_success_rate * 100)}%`} hint="越高越好" tone="neon" />
                </div>
              </div>
            ) : (
              <div className="flex min-h-[320px] items-center justify-center text-sm font-medium text-graphite-500 rounded-2xl border border-dashed border-white/60 bg-white/40 backdrop-blur-sm">
                从左侧报告列表选择一项查看详情。
              </div>
            )}
          </div>
        </motion.section>
      </div>
    </motion.div>
  )
}
