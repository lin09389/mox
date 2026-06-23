import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Database, UploadCloud, Search, Filter, Trash2, Download, Play, FileJson } from 'lucide-react'
import toast from 'react-hot-toast'
import { datasetApi, isDemoModeEnabled } from '../api'
import { HubPanelIntro } from '../context/HubContext'

const MOCK_DATASETS = [
  { id: '1', name: 'AdvBench', type: 'text', size: '1.2 MB', samples: 520, tags: ['safety', 'jailbreak'], date: '2026-06-12' },
  { id: '2', name: 'TruthfulQA', type: 'text', size: '3.4 MB', samples: 817, tags: ['hallucination', 'truth'], date: '2026-06-13' },
  { id: '3', name: 'Toxigen', type: 'text', size: '12.5 MB', samples: 10000, tags: ['toxicity'], date: '2026-06-14' },
]

import { containerVariants, itemVariants } from '../utils/animations'

export default function DatasetPage() {
  const [datasets, setDatasets] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [demoMode, setDemoMode] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function loadDatasets() {
      try {
        const data = await datasetApi.list()
        if (cancelled) return
        const items = data?.datasets || (Array.isArray(data) ? data : [])
        setDemoMode(false)
        setDatasets(items)
      } catch {
        if (cancelled) return
        if (isDemoModeEnabled) {
          const demoItems = MOCK_DATASETS.map((item) => ({ ...item, _demo_mode: true }))
          setDemoMode(true)
          setDatasets(demoItems)
          toast('后端不可用，已展示演示数据集。', { icon: '⚠️' })
        } else {
          toast.error('数据集加载失败，请检查后端连接与登录状态。')
          setDemoMode(false)
          setDatasets([])
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    loadDatasets()
    return () => { cancelled = true }
  }, [])

  const handleUpload = async () => {
    if (demoMode) {
      toast.error('演示模式下无法上传，请连接后端后重试。')
      return
    }
    try {
      await datasetApi.upload(new FormData())
    } catch (error) {
      const detail = error?.response?.data?.detail || error?.response?.data?.message
      toast.error(detail || '上传功能尚未实现。', { id: 'upload-wip' })
    }
  }

  const handleDelete = async (dataset) => {
    if (dataset._demo_mode) {
      setDatasets((prev) => prev.filter((d) => d.id !== dataset.id))
      toast.success('演示数据集已移除。')
      return
    }
    try {
      await datasetApi.delete(dataset.id)
      setDatasets((prev) => prev.filter((d) => d.id !== dataset.id))
      toast.success('数据集已移除')
    } catch (error) {
      const detail = error?.response?.data?.detail || error?.response?.data?.message
      toast.error(detail || '无法删除该数据集。')
    }
  }

  const filteredDatasets = datasets.filter((d) => d.name.toLowerCase().includes(searchQuery.toLowerCase()))

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="page-shell">
      <HubPanelIntro
        description={
          demoMode
            ? '当前展示演示数据集。连接后端后将显示 AdvBench、HarmBench 等内置样本库。'
            : '统一管理系统所有红队样本库，支持文件加载、多维度过滤与抽样配置。'
        }
        badge={
          demoMode ? (
            <span className="badge badge-info bg-amber-500/10 border-amber-500/30 text-amber-500 text-xs">
              演示数据
            </span>
          ) : null
        }
        action={
          <button
            type="button"
            onClick={handleUpload}
            disabled={demoMode}
            className="btn-primary py-2.5 px-5 bg-cyan-500 hover:bg-cyan-600 border-cyan-500 text-white shadow-[0_0_15px_rgba(6,182,212,0.3)] font-bold disabled:opacity-50"
          >
            <UploadCloud className="h-4 w-4 mr-2" />
            上传数据集
          </button>
        }
      />

      <motion.div variants={itemVariants} className="card p-6 bg-[var(--bg-glass-strong)] border-[var(--border-glass)] overflow-hidden">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
          <div className="relative w-full sm:max-w-md">
            <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)] pointer-events-none" />
            <input
              type="text"
              placeholder="搜索数据集名称或标签..."
              className="input-field pl-11 w-full font-mono text-sm"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <button className="btn-secondary h-[42px] px-6">
            <Filter className="h-4 w-4 text-[var(--text-muted)]" />
            条件筛选
          </button>
        </div>

        {loading && (
          <p className="mb-4 text-sm font-medium text-[var(--text-muted)]">正在从后端加载数据集列表…</p>
        )}

        <div className="overflow-x-auto rounded-xl border border-[var(--border-glass)] bg-[var(--bg-glass)]">
          <table className="w-full text-left text-sm text-[var(--text-main)]">
            <thead className="border-b border-[var(--border-glass)] bg-[var(--bg-glass-strong)] text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)]">
              <tr>
                <th className="px-5 py-4">数据集标识</th>
                <th className="px-5 py-4">样本容量</th>
                <th className="px-5 py-4">存储大小</th>
                <th className="px-5 py-4">分类标签</th>
                <th className="px-5 py-4">入库时间</th>
                <th className="px-5 py-4 text-right">管理操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-glass)]">
              <AnimatePresence>
                {filteredDatasets.map((dataset) => (
                  <motion.tr
                    layout
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
                    key={dataset.id}
                    className="hover:bg-[var(--bg-glass-strong)] transition-colors group"
                  >
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-500">
                          <Database className="h-4 w-4" />
                        </div>
                        <span className="font-bold text-[var(--text-main)] font-display tracking-wide">{dataset.name}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 font-mono font-bold text-[var(--text-main)]">{dataset.samples}</td>
                    <td className="px-5 py-4 font-mono font-medium text-[var(--text-muted)]">{dataset.size}</td>
                    <td className="px-5 py-4">
                      <div className="flex flex-wrap gap-2">
                        {(dataset.tags || []).map((tag) => (
                          <span
                            key={tag}
                            className="badge border text-[10px] uppercase font-bold tracking-widest px-2 py-1 bg-[var(--bg-main)]/50 border-[var(--border-glass-strong)] text-[var(--text-muted)] group-hover:border-cyan-500/30 group-hover:text-cyan-500 transition-colors"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-5 py-4 font-mono font-medium text-[var(--text-muted)]">{dataset.date}</td>
                    <td className="px-5 py-4">
                      <div className="flex items-center justify-end gap-1">
                        <button className="btn-ghost p-2 text-[var(--text-muted)] hover:text-cyan-500 hover:bg-cyan-500/10 rounded-lg transition-colors" title="数据预览">
                          <Play className="h-4 w-4" />
                        </button>
                        <button className="btn-ghost p-2 text-[var(--text-muted)] hover:text-emerald-500 hover:bg-emerald-500/10 rounded-lg transition-colors" title="导出副本">
                          <Download className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(dataset)}
                          className="btn-ghost p-2 text-[var(--text-muted)] hover:text-rose-500 hover:bg-rose-500/10 rounded-lg transition-colors"
                          title="销毁"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>

              {filteredDatasets.length === 0 && !loading && (
                <tr>
                  <td colSpan={6} className="px-5 py-24">
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex flex-col items-center justify-center text-center space-y-4"
                    >
                      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--bg-glass)] border border-[var(--border-glass-strong)]">
                        <FileJson className="h-8 w-8 text-[var(--text-muted)] opacity-60" />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-[var(--text-main)]">未找到匹配的数据集</p>
                        <p className="text-sm font-medium text-[var(--text-muted)] mt-1">请尝试调整搜索条件或上传新的数据集资源。</p>
                      </div>
                    </motion.div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </motion.div>
    </motion.div>
  )
}
