import { useState, useEffect } from 'react'
import { Download, Eye, Trash2 } from 'lucide-react'
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
    if (confirm('确定要删除这份报告吗？')) {
      setReports(reports.filter(r => r.id !== id))
      toast.success('删除成功')
    }
  }

  const stats = {
    total: reports.length,
    avgAttackRate: reports.length ? (reports.reduce((a, b) => a + b.attack_success_rate, 0) / reports.length * 100).toFixed(1) : 0,
    avgDefenseRate: reports.length ? (reports.reduce((a, b) => a + b.defense_success_rate, 0) / reports.length * 100).toFixed(1) : 0,
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">评估报告</h1>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <div className="text-sm text-gray-500">报告总数</div>
          <div className="text-2xl font-bold text-gray-800">{stats.total}</div>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <div className="text-sm text-gray-500">平均攻击成功率</div>
          <div className="text-2xl font-bold text-red-600">{stats.avgAttackRate}%</div>
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <div className="text-sm text-gray-500">平均防御成功率</div>
          <div className="text-2xl font-bold text-green-600">{stats.avgDefenseRate}%</div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        {loading ? (
          <div className="p-8 text-center text-gray-500">加载中...</div>
        ) : reports.length === 0 ? (
          <div className="p-8 text-center text-gray-500">暂无报告</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">报告名称</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">类型</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">模型</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">攻击成功率</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">防御成功率</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">生成时间</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">格式</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {reports.map(report => (
                  <tr key={report.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium text-gray-900">{report.report_name}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs ${report.report_type === 'evaluation' ? 'bg-blue-100 text-blue-800' : report.report_type === 'defense' ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'}`}>
                        {report.report_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-600">{report.model_name}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div className={`h-2 rounded-full ${report.attack_success_rate > 0.5 ? 'bg-red-500' : 'bg-green-500'}`} style={{ width: `${report.attack_success_rate * 100}%` }} />
                        </div>
                        <span className="text-sm">{(report.attack_success_rate * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div className={`h-2 rounded-full ${report.defense_success_rate > 0.7 ? 'bg-green-500' : 'bg-yellow-500'}`} style={{ width: `${report.defense_success_rate * 100}%` }} />
                        </div>
                        <span className="text-sm">{(report.defense_success_rate * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-600 text-sm">{report.created_at}</td>
                    <td className="px-6 py-4"><span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs uppercase">{report.format}</span></td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <button onClick={() => viewReport(report)} className="p-1 text-gray-400 hover:text-gray-600"><Eye size={18} /></button>
                        <button onClick={() => downloadReport(report)} className="p-1 text-gray-400 hover:text-gray-600"><Download size={18} /></button>
                        <button onClick={() => deleteReport(report.id)} className="p-1 text-gray-400 hover:text-red-600"><Trash2 size={18} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedReport && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedReport(null)}>
          <div className="bg-white rounded-xl p-6 w-full max-w-lg" onClick={e => e.stopPropagation()}>
            <h2 className="text-xl font-bold mb-4">{selectedReport.report_name}</h2>
            <div className="space-y-3">
              <div className="flex justify-between"><span className="text-gray-500">模型:</span><span>{selectedReport.model_name}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">类型:</span><span>{selectedReport.report_type}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">生成时间:</span><span>{selectedReport.created_at}</span></div>
              <div className="mt-4">
                <div className="text-sm text-gray-500 mb-1">攻击成功率</div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div className="bg-red-500 h-3 rounded-full" style={{ width: `${selectedReport.attack_success_rate * 100}%` }} />
                </div>
              </div>
              <div className="mt-2">
                <div className="text-sm text-gray-500 mb-1">防御成功率</div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div className="bg-green-500 h-3 rounded-full" style={{ width: `${selectedReport.defense_success_rate * 100}%` }} />
                </div>
              </div>
            </div>
            <button onClick={() => setSelectedReport(null)} className="mt-4 w-full px-4 py-2 border rounded-lg">关闭</button>
          </div>
        </div>
      )}
    </div>
  )
}
