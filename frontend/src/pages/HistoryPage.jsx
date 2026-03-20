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
  BarChart3
} from 'lucide-react'

const TABS = [
  { 
    id: 'attack', 
    label: '攻击记录', 
    icon: Zap,
    color: 'from-rose-500 to-red-500',
    bgColor: 'bg-rose-500/10',
    borderColor: 'border-rose-500/30',
    textColor: 'text-rose-400'
  },
  { 
    id: 'defense', 
    label: '防御记录', 
    icon: Shield,
    color: 'from-emerald-500 to-teal-500',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/30',
    textColor: 'text-emerald-400'
  },
]

const ATTACK_TYPES = {
  prompt_injection: { label: '提示词注入', color: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
  jailbreak: { label: '越狱攻击', color: 'bg-rose-500/20 text-rose-400 border-rose-500/30' },
  gcg: { label: 'GCG攻击', color: 'bg-purple-500/20 text-purple-400 border-purple-500/30' },
  auto_dan: { label: 'AutoDAN', color: 'bg-orange-500/20 text-orange-400 border-orange-500/30' },
}

const DEFENSE_TYPES = {
  input_filter: { label: '输入过滤', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  output_filter: { label: '输出过滤', color: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30' },
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: { 
    opacity: 1, 
    transition: { 
      staggerChildren: 0.05,
      delayChildren: 0.1
    } 
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { 
    opacity: 1, 
    y: 0,
    transition: {
      type: 'spring',
      stiffness: 100,
      damping: 15
    }
  }
}

const tableRowVariants = {
  hidden: { opacity: 0, x: -20 },
  show: { 
    opacity: 1, 
    x: 0,
    transition: {
      type: 'spring',
      stiffness: 100,
      damping: 15
    }
  }
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
      // Mock data with more entries
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

  const filteredAttacks = attackHistory.filter(item => 
    item.attack_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.model_name?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const filteredDefenses = defenseHistory.filter(item =>
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
  const successCount = activeTab === 'attack' 
    ? attackHistory.filter(i => i.result === 'success').length 
    : defenseHistory.filter(i => i.is_malicious).length
  const totalCount = activeTab === 'attack' ? attackHistory.length : defenseHistory.length

  return (
    <motion.div 
      className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950"
      initial="hidden"
      animate="show"
      variants={containerVariants}
    >
      {/* Header Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-indigo-500/10 to-violet-500/10" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl" />
        
        <motion.div 
          className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12"
          variants={itemVariants}
        >
          <div className="text-center">
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: 'spring', stiffness: 200, damping: 20 }}
              className="inline-flex items-center justify-center w-20 h-20 mb-6 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-2xl shadow-blue-500/30"
            >
              <History className="w-10 h-10 text-white" />
            </motion.div>
            
            <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent mb-4">
              历史记录
            </h1>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto">
              查看和管理所有的攻击与防御测试记录
            </p>
          </div>
        </motion.div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        {/* Stats Overview */}
        <motion.div 
          className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
          variants={containerVariants}
        >
          {[
            { 
              label: '总记录数', 
              value: totalCount,
              icon: BarChart3,
              color: 'from-blue-500 to-indigo-500'
            },
            { 
              label: activeTab === 'attack' ? '成功攻击' : '检测威胁', 
              value: successCount,
              icon: activeTab === 'attack' ? Zap : AlertTriangle,
              color: activeTab === 'attack' ? 'from-rose-500 to-red-500' : 'from-amber-500 to-orange-500'
            },
            { 
              label: activeTab === 'attack' ? '成功率' : '威胁率', 
              value: totalCount > 0 ? `${Math.round((successCount / totalCount) * 100)}%` : '0%',
              icon: Target,
              color: 'from-violet-500 to-purple-500'
            },
            { 
              label: '今日记录', 
              value: currentData.filter(i => new Date(i.created_at).toDateString() === new Date().toDateString()).length,
              icon: Clock,
              color: 'from-emerald-500 to-teal-500'
            },
          ].map((stat) => (
            <motion.div
              key={stat.label}
              variants={itemVariants}
              className="relative p-5 rounded-2xl bg-slate-800/30 border border-slate-700/50 backdrop-blur-sm overflow-hidden group"
              whileHover={{ scale: 1.02, y: -2 }}
            >
              <div className={`absolute top-0 right-0 w-20 h-20 bg-gradient-to-br ${stat.color} opacity-10 rounded-full blur-2xl group-hover:opacity-20 transition-opacity`} />
              <div className="relative flex items-center gap-4">
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center`}>
                  <stat.icon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <div className="text-sm text-slate-400">{stat.label}</div>
                  <div className="text-2xl font-bold text-white">{stat.value}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Controls Card */}
        <motion.div 
          className="p-6 rounded-2xl bg-slate-800/30 border border-slate-700/50 backdrop-blur-sm mb-6"
          variants={itemVariants}
        >
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            {/* Tabs */}
            <div className="flex p-1 rounded-xl bg-slate-900/50">
              {TABS.map((tab) => (
                <motion.button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium transition-all duration-300 ${
                    activeTab === tab.id
                      ? `bg-gradient-to-r ${tab.color} text-white shadow-lg`
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <tab.icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{tab.label}</span>
                </motion.button>
              ))}
            </div>

            {/* Search & Actions */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
              {/* Search */}
              <div className="relative">
                <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="text"
                  placeholder="搜索记录..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full sm:w-64 pl-10 pr-4 py-2.5 rounded-xl bg-slate-900/50 border border-slate-700/50 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all"
                />
              </div>

              {/* Sort Dropdown */}
              <div className="relative">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="appearance-none w-full sm:w-40 pl-4 pr-10 py-2.5 rounded-xl bg-slate-900/50 border border-slate-700/50 text-slate-200 focus:outline-none focus:border-blue-500/50 cursor-pointer"
                >
                  <option value="newest">最新优先</option>
                  <option value="oldest">最早优先</option>
                  {activeTab === 'attack' ? (
                    <option value="score">分数排序</option>
                  ) : (
                    <option value="confidence">置信度排序</option>
                  )}
                </select>
                <ChevronDown className="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2">
                <motion.button
                  onClick={loadHistory}
                  className="p-2.5 rounded-xl bg-slate-900/50 text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 border border-slate-700/50 transition-colors"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  title="刷新"
                >
                  <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                </motion.button>
                <motion.button
                  onClick={exportHistory}
                  className="p-2.5 rounded-xl bg-slate-900/50 text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 border border-slate-700/50 transition-colors"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  title="导出"
                >
                  <Download className="w-5 h-5" />
                </motion.button>
                <motion.button
                  onClick={clearHistory}
                  className="p-2.5 rounded-xl bg-slate-900/50 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-slate-700/50 transition-colors"
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

        {/* Table */}
        <motion.div 
          className="rounded-2xl bg-slate-800/30 border border-slate-700/50 backdrop-blur-sm overflow-hidden"
          variants={itemVariants}
        >
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-slate-900/50 border-b border-slate-700/50">
                  <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      时间
                    </div>
                  </th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">
                    <div className="flex items-center gap-2">
                      <Filter className="w-4 h-4" />
                      {activeTab === 'attack' ? '攻击类型' : '防御类型'}
                    </div>
                  </th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">目标模型</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">结果</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">
                    {activeTab === 'attack' ? '分数' : '置信度'}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                <AnimatePresence mode="wait">
                  {loading ? (
                    <motion.tr
                      key="loading"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                    >
                      <td colSpan={5} className="text-center py-16">
                        <div className="flex flex-col items-center gap-3">
                          <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
                            <RefreshCw className="w-5 h-5 text-blue-400 animate-spin" />
                          </div>
                          <span className="text-slate-400">加载中...</span>
                        </div>
                      </td>
                    </motion.tr>
                  ) : currentData.length === 0 ? (
                    <motion.tr
                      key="empty"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                    >
                      <td colSpan={5} className="text-center py-16">
                        <div className="flex flex-col items-center gap-3">
                          <div className="w-16 h-16 rounded-2xl bg-slate-800/50 flex items-center justify-center">
                            <History className="w-8 h-8 text-slate-600" />
                          </div>
                          <p className="text-slate-500">
                            {searchTerm ? '没有找到匹配的结果' : '暂无记录'}
                          </p>
                        </div>
                      </td>
                    </motion.tr>
                  ) : (
                    currentData.map((item, index) => (
                      <motion.tr
                        key={item.id}
                        variants={tableRowVariants}
                        initial="hidden"
                        animate="show"
                        transition={{ delay: index * 0.05 }}
                        className="hover:bg-slate-800/30 transition-colors group"
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center">
                              <Clock className="w-4 h-4 text-slate-500" />
                            </div>
                            <span className="text-slate-300">{formatDate(item.created_at)}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          {activeTab === 'attack' ? (
                            <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border ${
                              ATTACK_TYPES[item.attack_type]?.color || 'bg-slate-700/50 text-slate-400 border-slate-600/30'
                            }`}>
                              <Zap className="w-3.5 h-3.5" />
                              {ATTACK_TYPES[item.attack_type]?.label || item.attack_type}
                            </span>
                          ) : (
                            <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border ${
                              DEFENSE_TYPES[item.defense_type]?.color || 'bg-slate-700/50 text-slate-400 border-slate-600/30'
                            }`}>
                              <Shield className="w-3.5 h-3.5" />
                              {DEFENSE_TYPES[item.defense_type]?.label || item.defense_type}
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-blue-400" />
                            <span className="font-medium text-slate-200">{item.model_name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          {activeTab === 'attack' ? (
                            item.result === 'success' ? (
                              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/20 text-rose-400 text-sm font-medium border border-rose-500/30">
                                <XCircle className="w-4 h-4" />
                                攻击成功
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 text-sm font-medium border border-emerald-500/30">
                                <CheckCircle2 className="w-4 h-4" />
                                攻击失败
                              </span>
                            )
                          ) : (
                            item.is_malicious ? (
                              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-500/20 text-rose-400 text-sm font-medium border border-rose-500/30">
                                <AlertTriangle className="w-4 h-4" />
                                检测到威胁
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 text-sm font-medium border border-emerald-500/30">
                                <CheckCircle2 className="w-4 h-4" />
                                内容安全
                              </span>
                            )
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-20 h-2 rounded-full bg-slate-700 overflow-hidden">
                              <motion.div
                                className={`h-full rounded-full ${
                                  activeTab === 'attack'
                                    ? item.result === 'success' ? 'bg-rose-500' : 'bg-emerald-500'
                                    : item.is_malicious ? 'bg-rose-500' : 'bg-emerald-500'
                                }`}
                                initial={{ width: 0 }}
                                animate={{ width: `${((activeTab === 'attack' ? item.success_score : item.confidence) || 0) * 100}%` }}
                                transition={{ duration: 0.5, delay: index * 0.05 }}
                              />
                            </div>
                            <span className="text-slate-400 font-mono text-sm w-12">
                              {Math.round(((activeTab === 'attack' ? item.success_score : item.confidence) || 0) * 100)}%
                            </span>
                          </div>
                        </td>
                      </motion.tr>
                    ))
                  )}
                </AnimatePresence>
              </tbody>
            </table>
          </div>

          {/* Table Footer */}
          <div className="px-6 py-4 border-t border-slate-700/50 flex items-center justify-between">
            <span className="text-sm text-slate-500">
              共 {currentData.length} 条记录
            </span>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-500">
                {activeTab === 'attack' ? (
                  <>
                    <span className="text-rose-400 font-medium">{successCount}</span> 次成功攻击
                  </>
                ) : (
                  <>
                    <span className="text-amber-400 font-medium">{successCount}</span> 次威胁检测
                  </>
                )}
              </span>
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  )
}
