import { useState } from 'react'
import { motion } from 'framer-motion'
import { Database, UploadCloud, Search, Filter, MoreHorizontal, Trash2, Download, Play, FileJson } from 'lucide-react'
import toast from 'react-hot-toast'
import { datasetApi } from '../api'

const MOCK_DATASETS = [
  { id: '1', name: 'AdvBench', type: 'text', size: '1.2 MB', samples: 520, tags: ['safety', 'jailbreak'], date: '2026-06-12' },
  { id: '2', name: 'TruthfulQA', type: 'text', size: '3.4 MB', samples: 817, tags: ['hallucination', 'truth'], date: '2026-06-13' },
  { id: '3', name: 'Toxigen', type: 'text', size: '12.5 MB', samples: 10000, tags: ['toxicity'], date: '2026-06-14' },
]

export default function DatasetPage() {
  const [datasets, setDatasets] = useState(MOCK_DATASETS)
  const [searchQuery, setSearchQuery] = useState('')

  const handleUpload = () => {
    toast.error('上传功能正在开发中', { id: 'upload-wip' })
  }

  const handleDelete = (id) => {
    setDatasets((prev) => prev.filter((d) => d.id !== id))
    toast.success('数据集已删除')
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-display font-bold text-graphite-950">数据集管理</h1>
          <p className="mt-1 text-sm text-graphite-500">统一管理评测数据、支持文件加载、过滤与抽样配置</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={handleUpload} className="btn-primary">
            <UploadCloud className="h-4 w-4" />
            上传数据集
          </button>
        </div>
      </header>

      <div className="card p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
          <div className="relative w-full sm:max-w-xs">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-graphite-400" />
            <input
              type="text"
              placeholder="搜索数据集名称..."
              className="input-field pl-9 w-full"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <button className="btn-secondary w-full sm:w-auto">
            <Filter className="h-4 w-4" />
            高级筛选
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-graphite-700">
            <thead className="border-b border-graphite-200/60 bg-graphite-50/50 text-xs uppercase tracking-wider text-graphite-500">
              <tr>
                <th className="px-4 py-3 font-medium rounded-tl-xl">数据集名称</th>
                <th className="px-4 py-3 font-medium">样本数量</th>
                <th className="px-4 py-3 font-medium">大小</th>
                <th className="px-4 py-3 font-medium">标签</th>
                <th className="px-4 py-3 font-medium">更新时间</th>
                <th className="px-4 py-3 font-medium rounded-tr-xl text-right">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-graphite-200/50">
              {datasets
                .filter((d) => d.name.toLowerCase().includes(searchQuery.toLowerCase()))
                .map((dataset) => (
                  <motion.tr
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    key={dataset.id}
                    className="hover:bg-graphite-50/50 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-electric-100 to-electric-50 text-electric-600 shadow-sm border border-electric-100/50">
                          <Database className="h-5 w-5" />
                        </div>
                        <span className="font-semibold text-graphite-900 group-hover:text-electric-700 transition-colors">{dataset.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-medium">{dataset.samples}</td>
                    <td className="px-4 py-3 text-graphite-500">{dataset.size}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1.5">
                        {dataset.tags.map((tag) => (
                          <span
                            key={tag}
                            className="inline-flex items-center rounded-md bg-white/80 border border-graphite-200 px-2 py-0.5 text-xs font-medium text-graphite-600"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-graphite-500">{dataset.date}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button className="btn-ghost p-1.5 text-graphite-500 hover:text-electric-600" title="采样预览">
                          <Play className="h-4 w-4" />
                        </button>
                        <button className="btn-ghost p-1.5 text-graphite-500 hover:text-electric-600" title="导出">
                          <Download className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(dataset.id)}
                          className="btn-ghost p-1.5 text-graphite-500 hover:text-red-600"
                          title="删除"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              {datasets.filter((d) => d.name.toLowerCase().includes(searchQuery.toLowerCase())).length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-16">
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="flex flex-col items-center justify-center text-center space-y-3"
                    >
                      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-graphite-50 border border-graphite-100">
                        <FileJson className="h-8 w-8 text-graphite-400" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-graphite-800">未找到匹配的数据集</p>
                        <p className="text-xs text-graphite-500 mt-1">尝试使用其他关键词搜索或上传新数据集。</p>
                      </div>
                    </motion.div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
