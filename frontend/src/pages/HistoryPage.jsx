import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { attackApi, defenseApi } from '../api'
import {
  History,
  Zap,
  Shield,
  Search,
  Trash2,
  Download,
  RefreshCw,
  Clock,
  Target,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Filter,
  ChevronDown,
  BarChart3,
} from 'lucide-react'

const TABS = [
  {
    id: 'attack',
    label: '攻击记录',
    icon: Zap,
    color: 'lava',
  },
  {
    id: 'defense',
    label: '防御记录',
    icon: Shield,
    color: 'neon',
  },
]

const ATTACK_TYPES = {
  prompt_injection: { label: '提示词注入', bg: 'bg-lava-100', text: 'text-lava-700', border: 'border-lava-200/70' },
  jailbreak: { label: '越狱攻击', bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-200/70' },
  gcg: { label: 'GCG攻击', bg: 'bg-electric-100', text: 'text-electric-700', border: 'border-electric-200/70' },
  auto_dan: { label: 'AutoDAN', bg: 'bg-graphite-100', text: 'text-graphite-700', border: 'border-graphite-200/70' },
}

const DEFENSE_TYPES = {
  input_filter: { label: '输入过滤', bg: 'bg-electric-100', text: 'text-electric-700', border: 'border-electric-200/70' },
  output_filter: { label: '输出过滤', bg: 'bg-neon-100', text: 'text-neon-700', border: 'border-neon-200/70' },
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
}

const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } },
}

export default function HistoryPage() {
  const [activeTab, setActiveTab] = useState('attack')
  const [attackHistory, setAttackHistory] = useState([])
  const [defenseHistory, setDefenseHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState('newest')

  useEffect(() => {
    loadHistory()
  }, [activeTab])

  const loadHistory = async () => {
    setLoading(true)
    try {
      if (activeTab === 'attack') {
        const { data } = await attackApi.getHistory({ limit: 50 })
        setAttackHistory(data)
      } else {
        const { data } = await defenseApi.getHistory({ limit: 50 })
        setDefenseHistory(data)
      }
    } catch (error) {
      if (activeTab === 'attack') {
        setAttackHistory([
          { id: 1, attack_type: 'prompt_injection', model_name: 'gpt-4', result: 'success', success_score: 0.92, created_at: new Date().toISOString() },
          { id: 2, attack_type: 'jailbreak', model_name: 'claude-3', result: 'failure', success_score: 0.15, created_at: new Date(Date.now() - 3600000).toISOString() },
          { id: 3, attack_type: 'gcg', model_name: 'gpt-4', result: 'success', success_score: 0.78, created_at: new Date(Date.now() - 7200000).toISOString() },
          { id: 4, attack_type: 'prompt_injection', model_name: 'abab2.5-chat', result: 'failure', success_score: 0.22, created_at: new Date(Date.now() - 10800000).toISOString() },
          { id: 5, attack_type: 'auto_dan', model_name: 'gpt-3.5-turbo', result: 'success', success_score: 0.85, created_at: new Date(Date.now() - 14400000).toISOString() },
          { id: 6, attack_type: 'jailbreak', model_name: 'gpt-4', result: 'success', success_score: 0.91, created_at: new Date(Date.now() - 18000000).toISOString() },
          { id: 7, attack_type: 'gcg', model_name: 'claude-3', result: 'failure', success_score: 0.33, created_at: new Date(Date.now() - 21600000).toISOString() },
        ])
      } else {
        setDefenseHistory([
          { id: 1, defense_type: 'input_filter', model_name: 'gpt-4', is_malicious: true, confidence: 0.95, created_at: new Date().toISOString() },
          { id: 2, defense_type: 'output_filter', model_name: 'gpt-4', is_malicious: false, confidence: 0.12, created_at: new Date(Date.now() - 3600000).toISOString() },
          { id: 3, defense_type: 'input_filter', model_name: 'claude-3', is_malicious: true, confidence: 0.88, created_at: new Date(Date.now() - 7200000).toISOString() },
          { id: 4, defense_type: 'output_filter', model_name: 'abab2.5-chat', is_malicious: false, confidence: 0.05, created_at: new Date(Date.now() - 10800000).toISOString() },
          { id: 5, defense_type: 'input_filter', model_name: 'gpt-3.5-turbo', is_malicious: true, confidence: 0.76, created_at: new Date(Date.now() - 14400000).toISOString() },
          { id: 6, defense_type: 'output_filter', model_name: 'claude-3', is_malicious: false, confidence: 0.08, created_at: new Date(Date.now() - 18000000).toISOString() },
        ])
      }
    } finally {
      setLoading(false)
    }
  }

  const filteredAttacks = attackHistory.filter(
    (item) =>
      item.attack_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.model_name?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const filteredDefenses = defenseHistory.filter(
    (item) =>
      item.defense_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.model_name?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const sortedAttacks = [...filteredAttacks].sort((a, b) => {
    if (sortBy === 'newest') return new Date(b.created_at) - new Date(a.created_at)
    if (sortBy === 'oldest') return new Date(a.created_at) - new Date(b.created_at)
    if (sortBy === 'score') return b.success_score - a.success_score
    return 0
  })

  const sortedDefenses = [...filteredDefenses].sort((a, b) => {
    if (sortBy === 'newest') return new Date(b.created_at) - new Date(a.created_at)
    if (sortBy === 'oldest') return new Date(a.created_at) - new Date(b.created_at)
    if (sortBy === 'confidence') return b.confidence - a.confidence
    return 0
  })

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now - date

    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
    return date.toLocaleDateString('zh-CN')
  }

  const clearHistory = () => {
    if (activeTab === 'attack') {
      setAttackHistory([])
    } else {
      setDefenseHistory([])
    }
    toast.success('历史记录已清空')
  }

  const exportHistory = () => {
    const data = activeTab === 'attack' ? attackHistory : defenseHistory
    const jsonStr = JSON.stringify(data, null, 2)
    const blob = new Blob([jsonStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${activeTab}_history_${new Date().toISOString().split('T')[0]}.json`
    a.click()
    toast.success('历史记录已导出')
  }

  const currentData = activeTab === 'attack' ? sortedAttacks : sortedDefenses
  const successCount =
    activeTab === 'attack'
      ? attackHistory.filter((i) => i.result === 'success').length
      : defenseHistory.filter((i) => i.is_malicious).length
  const totalCount = activeTab === 'attack' ? attackHistory.length : defenseHistory.length

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      {/* 页面标题 */}
      <motion.div variants={item} className="flex items-center gap-3">
        <div className="w-11 h-11 bg-electric-100 rounded-lg flex items-center justify-center border border-electric-200/70">
          <History className="w-5.5 h-5.5 text-electric-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold font-display text-graphite-900 tracking-tight">
            历史记录
          </h1>
          <p className="text-sm text-graphite-500">查看和管理所有的攻击与防御测试记录</p>
        </div>
      </motion.div>

      {/* 统计概览 */}
      <motion.div variants={item} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 bg-electric-100 rounded-lg flex items-center justify-center border border-electric-200/70">
            <BarChart3 className="w-5 h-5 text-electric-600" />
          </div>
          <div>
            <p className="text-xs text-graphite-500">总记录数</p>
            <p className="text-2xl font-bold font-display text-graphite-900">{totalCount}</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center border ${
            activeTab === 'attack' ? 'bg-lava-100 border-lava-200/70' : 'bg-amber-100 border-amber-200/70'
          }`}>
            {activeTab === 'attack' ? (
              <Zap className="w-5 h-5 text-lava-600" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-amber-600" />
            )}
          </div>
          <div>
            <p className="text-xs text-graphite-500">
              {activeTab === 'attack' ? '成功攻击' : '检测威胁'}
            </p>
            <p className="text-2xl font-bold font-display text-graphite-900">{successCount}</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 bg-electric-100 rounded-lg flex items-center justify-center border border-electric-200/70">
            <Target className="w-5 h-5 text-electric-600" />
          </div>
          <div>
            <p className="text-xs text-graphite-500">
              {activeTab === 'attack' ? '成功率' : '威胁率'}
            </p>
            <p className="text-2xl font-bold font-display text-graphite-900">
              {totalCount > 0 ? `${Math.round((successCount / totalCount) * 100)}%` : '0%'}
            </p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 bg-neon-100 rounded-lg flex items-center justify-center border border-neon-200/70">
            <Clock className="w-5 h-5 text-neon-600" />
          </div>
          <div>
            <p className="text-xs text-graphite-500">今日记录</p>
            <p className="text-2xl font-bold font-display text-graphite-900">
              {currentData.filter(
                (i) => new Date(i.created_at).toDateString() === new Date().toDateString()
              ).length}
            </p>
          </div>
        </div>
      </motion.div>

      {/* 控制区域 */}
      <motion.div variants={item} className="card">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          {/* Tabs */}
          <div className="flex gap-2">
            {TABS.map((tab) => {
              const isActive = activeTab === tab.id
              return (
                <motion.button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? `bg-${tab.color === 'lava' ? 'lava' : tab.color}-600 text-white shadow-soft`
                      : 'bg-white text-graphite-600 hover:bg-graphite-50 border border-graphite-200/60'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{tab.label}</span>
                </motion.button>
              )
            })}
          </div>

          {/* Search & Actions */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-graphite-400" />
              <input
                type="text"
                placeholder="搜索记录..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input-field pl-10 w-full sm:w-64"
              />
            </div>

            {/* Sort Dropdown */}
            <div className="relative">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="select-field appearance-none pr-10"
              >
                <option value="newest">最新优先</option>
                <option value="oldest">最早优先</option>
                {activeTab === 'attack' ? (
                  <option value="score">分数排序</option>
                ) : (
                  <option value="confidence">置信度排序</option>
                )}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-graphite-400 pointer-events-none" />
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <motion.button
                onClick={loadHistory}
                className="p-2.5 rounded-lg bg-white text-graphite-500 hover:text-electric-600 border border-graphite-200/60 hover:border-electric-200 transition-colors"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                title="刷新"
              >
                <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
              </motion.button>
              <motion.button
                onClick={exportHistory}
                className="p-2.5 rounded-lg bg-white text-graphite-500 hover:text-neon-600 border border-graphite-200/60 hover:border-neon-200 transition-colors"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                title="导出"
              >
                <Download className="w-5 h-5" />
              </motion.button>
              <motion.button
                onClick={clearHistory}
                className="p-2.5 rounded-lg bg-white text-graphite-500 hover:text-lava-600 border border-graphite-200/60 hover:border-lava-200 transition-colors"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                title="清空"
              >
                <Trash2 className="w-5 h-5" />
              </motion.button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* 表格 */}
      <motion.div variants={item} className="card p-0 overflow-hidden">
        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="p-16 text-center"
            >
              <div className="spinner mx-auto mb-3" />
              <p className="text-graphite-500">加载中...</p>
            </motion.div>
          ) : currentData.length === 0 ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="p-16 text-center"
            >
              <div className="w-14 h-14 bg-graphite-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <History className="w-7 h-7 text-graphite-400" />
              </div>
              <p className="text-graphite-500">
                {searchTerm ? '没有找到匹配的结果' : '暂无记录'}
              </p>
            </motion.div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>时间</th>
                    <th>{activeTab === 'attack' ? '攻击类型' : '防御类型'}</th>
                    <th>目标模型</th>
                    <th>结果</th>
                    <th>{activeTab === 'attack' ? '分数' : '置信度'}</th>
                  </tr>
                </thead>
                <tbody>
                  {currentData.map((item, index) => (
                    <tr key={item.id}>
                      <td>
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4 text-graphite-400" />
                          <span className="text-graphite-600 text-xs">
                            {formatDate(item.created_at)}
                          </span>
                        </div>
                      </td>
                      <td>
                        {activeTab === 'attack' ? (
                          <span
                            className={`badge ${ATTACK_TYPES[item.attack_type]?.bg || 'bg-graphite-100'} ${
                              ATTACK_TYPES[item.attack_type]?.text || 'text-graphite-700'
                            } ${ATTACK_TYPES[item.attack_type]?.border || 'border-graphite-200/60'}`}
                          >
                            <Zap className="w-3 h-3 mr-1" />
                            {ATTACK_TYPES[item.attack_type]?.label || item.attack_type}
                          </span>
                        ) : (
                          <span
                            className={`badge ${DEFENSE_TYPES[item.defense_type]?.bg || 'bg-graphite-100'} ${
                              DEFENSE_TYPES[item.defense_type]?.text || 'text-graphite-700'
                            } ${DEFENSE_TYPES[item.defense_type]?.border || 'border-graphite-200/60'}`}
                          >
                            <Shield className="w-3 h-3 mr-1" />
                            {DEFENSE_TYPES[item.defense_type]?.label || item.defense_type}
                          </span>
                        )}
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 rounded-full bg-electric-500" />
                          <span className="font-medium text-graphite-800 text-sm">{item.model_name}</span>
                        </div>
                      </td>
                      <td>
                        {activeTab === 'attack' ? (
                          item.result === 'success' ? (
                            <span className="badge bg-lava-100 text-lava-700 border border-lava-200/70">
                              <XCircle className="w-3.5 h-3.5 mr-1" />
                              攻击成功
                            </span>
                          ) : (
                            <span className="badge bg-neon-100 text-neon-700 border border-neon-200/70">
                              <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                              攻击失败
                            </span>
                          )
                        ) : item.is_malicious ? (
                          <span className="badge bg-lava-100 text-lava-700 border border-lava-200/70">
                            <AlertTriangle className="w-3.5 h-3.5 mr-1" />
                            检测到威胁
                          </span>
                        ) : (
                          <span className="badge bg-neon-100 text-neon-700 border border-neon-200/70">
                            <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                            内容安全
                          </span>
                        )}
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-1.5 bg-graphite-200 rounded-full overflow-hidden">
                            <motion.div
                              className={`h-full rounded-full ${
                                activeTab === 'attack'
                                  ? item.result === 'success'
                                    ? 'bg-lava-500'
                                    : 'bg-neon-500'
                                  : item.is_malicious
                                  ? 'bg-lava-500'
                                  : 'bg-neon-500'
                              }`}
                              initial={{ width: 0 }}
                              animate={{
                                width: `${((activeTab === 'attack' ? item.success_score : item.confidence) || 0) * 100}%`,
                              }}
                              transition={{ duration: 0.5, delay: index * 0.05 }}
                            />
                          </div>
                          <span className="text-graphite-500 font-mono text-xs w-10">
                            {Math.round(
                              ((activeTab === 'attack' ? item.success_score : item.confidence) || 0) * 100
                            )}
                            %
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </AnimatePresence>

        {/* Table Footer */}
        {!loading && currentData.length > 0 && (
          <div className="px-5 py-4 border-t border-graphite-200/60 flex items-center justify-between">
            <span className="text-xs text-graphite-500">共 {currentData.length} 条记录</span>
            <div className="flex items-center gap-4 text-xs text-graphite-500">
              {activeTab === 'attack' ? (
                <>
                  <span>
                    <span className="text-lava-600 font-medium">{successCount}</span> 次成功攻击
                  </>
                </>
              ) : (
                <>
                  <span>
                    <span className="text-amber-600 font-medium">{successCount}</span> 次威胁检测
                  </>
                </>
              )}
            </div>
          </div>
        )}
      </motion.div>
    </motion.div>
  )
}
