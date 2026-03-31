import { useMemo, useState } from 'react'
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
    <div className="page-shell">
      <PageHeader
        eyebrow="REPORT CENTER"
        title="评估报告中心"
        description="集中管理攻防评估结果，支持快速预览与导出。"
      />

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard icon={FileText} label="报告总数" value={stats.total} hint="当前存档数量" tone="electric" />
        <MetricCard icon={TrendingUp} label="平均攻击成功率" value={`${stats.attack}%`} hint="越高风险越大" tone="lava" />
        <MetricCard icon={Shield} label="平均防御成功率" value={`${stats.defense}%`} hint="越高越稳定" tone="neon" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <section className="table-shell">
          <div className="border-b border-graphite-200/70 px-5 py-4">
            <PanelHeader title="报告列表" description="按报告类型与模型查看历史结论。" />
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>报告名称</th>
                  <th>类型</th>
                  <th>模型</th>
                  <th>攻击成功率</th>
                  <th>防御成功率</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((report) => (
                  <tr key={report.id}>
                    <td>{report.report_name}</td>
                    <td><span className="badge badge-neutral">{typeLabel[report.report_type] || report.report_type}</span></td>
                    <td>{report.model_name}</td>
                    <td>{Math.round(report.attack_success_rate * 100)}%</td>
                    <td>{Math.round(report.defense_success_rate * 100)}%</td>
                    <td>
                      <div className="flex gap-2">
                        <button type="button" className="btn-secondary px-3 py-2" onClick={() => setSelected(report)}><Eye className="h-4 w-4" /></button>
                        <button type="button" className="btn-secondary px-3 py-2" onClick={() => toast.success(`开始下载 ${report.report_name}`)}><Download className="h-4 w-4" /></button>
                        <button
                          type="button"
                          className="btn-danger px-3 py-2"
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
        </section>

        <section className="card card-glow">
          <PanelHeader title="报告预览" description="选中左侧任一报告查看关键摘要。" />
          {selected ? (
            <div className="space-y-4">
              <div className="rounded-[18px] border border-graphite-200/70 bg-white/80 p-4">
                <p className="text-sm font-semibold text-graphite-900">{selected.report_name}</p>
                <p className="mt-1 text-xs text-graphite-500">{selected.created_at}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="badge badge-neutral">{typeLabel[selected.report_type] || selected.report_type}</span>
                  <span className="badge badge-neutral">{selected.model_name}</span>
                  <span className="badge badge-neutral">.{selected.format}</span>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <MetricCard icon={TrendingUp} label="攻击成功率" value={`${Math.round(selected.attack_success_rate * 100)}%`} hint="越低越好" tone="lava" />
                <MetricCard icon={Shield} label="防御成功率" value={`${Math.round(selected.defense_success_rate * 100)}%`} hint="越高越好" tone="neon" />
              </div>
            </div>
          ) : (
            <div className="panel-muted flex min-h-[320px] items-center justify-center text-sm text-graphite-500">
              从左侧报告列表选择一项查看详情。
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
