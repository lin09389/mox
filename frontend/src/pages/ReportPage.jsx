import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Download, Eye, Trash2, FileText, TrendingUp, Shield } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '../api'

export default function ReportPage() {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedReport, setSelectedReport] = useState(null)

  useEffect(() => {
    fetchReports()
  }, [])

  const fetchReports = async () => {
    setLoading(true)
    try {
      const res = await api.get('/api/reports')
      setReports(res.data)
    } catch (error) {
      setReports(getDefaultReports())
    } finally {
      setLoading(false)
    }
  }

  const getDefaultReports = () => [
    { id: 1, report_name: 'GPT-4安全评估报告', report_type: 'evaluation', model_name: 'gpt-4', attack_success_rate: 0.32, defense_success_rate: 0.85, created_at: '2024-03-01 10:30:00', format: 'html' },
    { id: 2, report_name: 'Claude3防御测试', report_type: 'defense', model_name: 'claude-3-opus', attack_success_rate: 0.15, defense_success_rate: 0.92, created_at: '2024-02-28 15:20:00', format: 'json' },
    { id: 3, report_name: 'MiniMax批量评估', report_type: 'benchmark', model_name: 'abab2.5-chat', attack_success_rate: 0.45, defense_success_rate: 0.78, created_at: '2024-02-25 09:15:00', format: 'md' },
  ]

  const viewReport = (report) => {
    setSelectedReport(report)
  }

  const downloadReport = (report) => {
    toast.success(`下载 ${report.report_name}`)
  }

  const deleteReport = (id) => {
    setReports(reports.filter(r => r.id !== id))
    toast.success('删除成功')
  }

  const stats = {
    total: reports.length,
    avgAttackRate: reports.length ? (reports.reduce((a, b) => a + b.attack_success_rate, 0) / reports.length * 100).toFixed(1) : 0,
    avgDefenseRate: reports.length ? (reports.reduce((a, b) => a + b.defense_success_rate, 0) / reports.length * 100).toFixed(1) : 0,
  }

  const reportTypeConfig = {
    evaluation: { label: '评估', bg: 'bg-electric-50', text: 'text-electric-700', border: 'border-electric-200/70' },
    defense: { label: '防御', bg: 'bg-neon-50', text: 'text-neon-700', border: 'border-neon-200/70' },
    benchmark: { label: '基准', bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200/70' },
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-neon-100 rounded-lg flex items-center justify-center border border-neon-200/70">
            <FileText className="w-6 h-6 text-neon-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold font-display text-graphite-900 tracking-tight">
              评估报告
            </h1>
            <p className="text-sm text-graphite-500 mt-0.5">查看和管理安全评估报告</p>
          </div>
        </div>
      </motion.div>

      {/* 统计卡片 */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
      >
        <div className="card text-center">
          <p className="text-3xl font-bold font-display text-graphite-900">{stats.total}</p>
          <p className="text-xs text-graphite-500 mt-1">报告总数</p>
        </div>
        <div className="card text-center">
          <div className="w-10 h-10 mx-auto mb-2 rounded-lg bg-lava-100 flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-lava-600" />
          </div>
          <p className="text-3xl font-bold font-display text-lava-600">{stats.avgAttackRate}%</p>
          <p className="text-xs text-graphite-500 mt-1">平均攻击成功率</p>
        </div>
        <div className="card text-center">
          <div className="w-10 h-10 mx-auto mb-2 rounded-lg bg-neon-100 flex items-center justify-center">
            <Shield className="w-5 h-5 text-neon-600" />
          </div>
          <p className="text-3xl font-bold font-display text-neon-600">{stats.avgDefenseRate}%</p>
          <p className="text-xs text-graphite-500 mt-1">平均防御成功率</p>
        </div>
      </motion.div>

      {/* 报告表格 */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-graphite-500">加载中...</div>
        ) : reports.length === 0 ? (
          <div className="p-8 text-center text-graphite-500">暂无报告</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th className="text-left">报告名称</th>
                  <th className="text-left">类型</th>
                  <th className="text-left">模型</th>
                  <th className="text-left">攻击成功率</th>
                  <th className="text-left">防御成功率</th>
                  <th className="text-left">生成时间</th>
                  <th className="text-left">格式</th>
                  <th className="text-left">操作</th>
                </tr>
              </thead>
              <tbody>
                {reports.map(report => {
                  const typeConfig = reportTypeConfig[report.report_type] || reportTypeConfig.evaluation
                  return (
                    <tr key={report.id}>
                      <td className="font-medium text-graphite-900">{report.report_name}</td>
                      <td>
                        <span className={`px-2.5 py-1 rounded text-xs font-medium border ${typeConfig.bg} ${typeConfig.text} ${typeConfig.border}`}>
                          {typeConfig.label}
                        </span>
                      </td>
                      <td className="text-graphite-600">{report.model_name}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-graphite-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${report.attack_success_rate > 0.5 ? 'bg-lava-500' : 'bg-neon-500'}`}
                              style={{ width: `${report.attack_success_rate * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-graphite-600">{(report.attack_success_rate * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-graphite-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${report.defense_success_rate > 0.7 ? 'bg-neon-500' : 'bg-amber-500'}`}
                              style={{ width: `${report.defense_success_rate * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-graphite-600">{(report.defense_success_rate * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="text-graphite-600 text-sm">{report.created_at}</td>
                      <td>
                        <span className="badge bg-graphite-100 text-graphite-700 border border-graphite-200/60">
                          {report.format}
                        </span>
                      </td>
                      <td>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => viewReport(report)}
                            className="p-1.5 text-graphite-400 hover:text-electric-600 transition-colors"
                          >
                            <Eye size={16} />
                          </button>
                          <button
                            onClick={() => downloadReport(report)}
                            className="p-1.5 text-graphite-400 hover:text-electric-600 transition-colors"
                          >
                            <Download size={16} />
                          </button>
                          <button
                            onClick={() => deleteReport(report.id)}
                            className="p-1.5 text-graphite-400 hover:text-lava-600 transition-colors"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 报告详情模态框 */}
      {selectedReport && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 bg-graphite-900/30 backdrop-blur-sm flex items-center justify-center z-50"
          onClick={() => setSelectedReport(null)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            className="bg-white rounded-lg p-6 w-full max-w-md shadow-modal"
            onClick={e => e.stopPropagation()}
          >
            <h2 className="text-lg font-semibold text-graphite-900 mb-4">
              {selectedReport.report_name}
            </h2>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-graphite-500">模型:</span>
                <span className="text-graphite-900 font-medium">{selectedReport.model_name}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-graphite-500">类型:</span>
                <span className="text-graphite-900">{selectedReport.report_type}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-graphite-500">生成时间:</span>
                <span className="text-graphite-900">{selectedReport.created_at}</span>
              </div>
              <div className="mt-4">
                <div className="text-xs text-graphite-500 mb-1.5">攻击成功率</div>
                <div className="w-full h-2 bg-graphite-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-lava-500 rounded-full"
                    style={{ width: `${selectedReport.attack_success_rate * 100}%` }}
                  />
                </div>
                <span className="text-xs text-lava-600 mt-1">{(selectedReport.attack_success_rate * 100).toFixed(1)}%</span>
              </div>
              <div className="mt-3">
                <div className="text-xs text-graphite-500 mb-1.5">防御成功率</div>
                <div className="w-full h-2 bg-graphite-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-neon-500 rounded-full"
                    style={{ width: `${selectedReport.defense_success_rate * 100}%` }}
                  />
                </div>
                <span className="text-xs text-neon-600 mt-1">{(selectedReport.defense_success_rate * 100).toFixed(1)}%</span>
              </div>
            </div>
            <button
              onClick={() => setSelectedReport(null)}
              className="btn-secondary w-full mt-5"
            >
              关闭
            </button>
          </motion.div>
        </motion.div>
      )}
    </div>
  )
}
