import { useEffect, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock3,
  Download,
  Filter,
  History,
  RefreshCw,
  Search,
  Shield,
  Trash2,
  Zap,
} from 'lucide-react'
import { attackApi, defenseApi } from '../api'
import {
  MetricCard,
  PageHeader,
  PanelHeader,
  TableMobileFallback,
} from '../components/ui/AppFrame'

const TABS = [
  { id: 'attack', label: '攻击记录', icon: Zap },
  { id: 'defense', label: '防御记录', icon: Shield },
]

const ATTACK_LABELS = {
  prompt_injection: '提示词注入',
  jailbreak: '越狱攻击',
  gcg: 'GCG 攻击',
  auto_dan: 'AutoDAN',
}

const DEFENSE_LABELS = {
  input_filter: '输入过滤',
  output_filter: '输出过滤',
}

const badgeForAttackResult = (result) => (result === 'success' ? 'badge-danger' : 'badge-success')
const badgeForDefenseResult = (malicious) => (malicious ? 'badge-danger' : 'badge-success')

function formatDate(dateStr) {
  const date = new Date(dateStr)
  const diff = Date.now() - date.getTime()
  if (diff < 60_000) return '刚刚'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} 小时前`
  return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
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
    } catch {
      if (activeTab === 'attack') {
        setAttackHistory([
          { id: 1, attack_type: 'prompt_injection', model_name: 'gpt-4', result: 'success', success_score: 0.92, created_at: new Date().toISOString() },
          { id: 2, attack_type: 'jailbreak', model_name: 'claude-3', result: 'failure', success_score: 0.15, created_at: new Date(Date.now() - 3_600_000).toISOString() },
          { id: 3, attack_type: 'gcg', model_name: 'gpt-4', result: 'success', success_score: 0.78, created_at: new Date(Date.now() - 7_200_000).toISOString() },
        ])
      } else {
        setDefenseHistory([
          { id: 1, defense_type: 'input_filter', model_name: 'gpt-4', is_malicious: true, confidence: 0.95, created_at: new Date().toISOString() },
          { id: 2, defense_type: 'output_filter', model_name: 'gpt-4', is_malicious: false, confidence: 0.12, created_at: new Date(Date.now() - 3_600_000).toISOString() },
          { id: 3, defense_type: 'input_filter', model_name: 'claude-3', is_malicious: true, confidence: 0.88, created_at: new Date(Date.now() - 7_200_000).toISOString() },
        ])
      }
    } finally {
      setLoading(false)
    }
  }

  const currentRaw = activeTab === 'attack' ? attackHistory : defenseHistory

  const filtered = useMemo(() => {
    const search = searchTerm.trim().toLowerCase()
    const list = currentRaw.filter((item) => {
      const type = activeTab === 'attack' ? item.attack_type : item.defense_type
      return !search || type?.toLowerCase().includes(search) || item.model_name?.toLowerCase().includes(search)
    })

    return [...list].sort((a, b) => {
      if (sortBy === 'oldest') return new Date(a.created_at) - new Date(b.created_at)
      if (sortBy === 'score') return (b.success_score || 0) - (a.success_score || 0)
      if (sortBy === 'confidence') return (b.confidence || 0) - (a.confidence || 0)
      return new Date(b.created_at) - new Date(a.created_at)
    })
  }, [activeTab, currentRaw, searchTerm, sortBy])

  const metrics = useMemo(() => {
    const total = currentRaw.length
    const successCount =
      activeTab === 'attack'
        ? currentRaw.filter((item) => item.result === 'success').length
        : currentRaw.filter((item) => item.is_malicious).length
    const todayCount = currentRaw.filter(
      (item) => new Date(item.created_at).toDateString() === new Date().toDateString()
    ).length

    return {
      total,
      successCount,
      ratio: total ? Math.round((successCount / total) * 100) : 0,
      todayCount,
    }
  }, [activeTab, currentRaw])

  const clearHistory = () => {
    if (activeTab === 'attack') {
      setAttackHistory([])
    } else {
      setDefenseHistory([])
    }
    toast.success('已清空当前页签记录。')
  }

  const exportHistory = () => {
    const data = JSON.stringify(currentRaw, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${activeTab}_history_${new Date().toISOString().slice(0, 10)}.json`
    anchor.click()
    URL.revokeObjectURL(url)
    toast.success('已导出当前记录。')
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="page-shell"
    >
      <motion.div variants={itemVariants}>
        <PageHeader
          eyebrow="HISTORY CENTER"
          title="历史记录中心"
          description="统一查看攻击与防御记录，支持搜索、排序、导出和移动端降级浏览。"
        />
      </motion.div>

      <motion.div variants={itemVariants} className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard icon={BarChart3} label="总记录数" value={metrics.total} hint="当前页签下的所有记录" tone="electric" />
        <MetricCard
          icon={activeTab === 'attack' ? AlertTriangle : Shield}
          label={activeTab === 'attack' ? '攻击成功数' : '检测到威胁'}
          value={metrics.successCount}
          hint={activeTab === 'attack' ? '需要重点复盘的案例' : '被识别出的风险内容'}
          tone={activeTab === 'attack' ? 'lava' : 'amber'}
        />
        <MetricCard
          icon={CheckCircle2}
          label={activeTab === 'attack' ? '成功率' : '识别率'}
          value={`${metrics.ratio}%`}
          hint="帮助快速判断近期趋势"
          tone="neon"
        />
        <MetricCard icon={Clock3} label="今日新增" value={metrics.todayCount} hint="便于快速查看今天的变化" tone="graphite" />
      </motion.div>

      <motion.section variants={itemVariants} className="card relative overflow-hidden group">
        <div className="absolute inset-0 bg-gradient-to-br from-electric-50/20 to-transparent pointer-events-none group-hover:opacity-100 opacity-0 transition-opacity duration-700" />
        <div className="relative z-10">
          <PanelHeader
            title="筛选与操作"
            description="优先把常用动作聚合在一行，减少来回切页。"
          />
          <div className="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex flex-wrap gap-2.5 bg-white/60 p-1.5 rounded-xl border border-white/80 shadow-sm backdrop-blur-md">
              {TABS.map((tab) => {
                const Icon = tab.icon
                const active = tab.id === activeTab
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-5 py-2 text-sm font-bold transition-all duration-300 rounded-lg ${
                      active
                        ? 'bg-white text-electric-700 shadow-sm border border-electric-100'
                        : 'text-graphite-600 hover:text-graphite-900 hover:bg-white/50 border border-transparent'
                    }`}
                  >
                    <Icon className={`h-4 w-4 ${active ? 'text-electric-500' : 'text-graphite-600'}`} />
                    {tab.label}
                  </button>
                )
              })}
            </div>

            <div className="flex flex-col gap-3 md:flex-row md:items-center">
              <label className="relative min-w-[220px]">
                <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-graphite-600" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                  className="input-field pl-11 !bg-white/60 !border-white/80 hover:!bg-white focus:!bg-white shadow-sm"
                  placeholder="搜索类型或模型"
                />
              </label>

              <label className="relative min-w-[180px]">
                <Filter className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-graphite-600" />
                <select 
                  value={sortBy} 
                  onChange={(event) => setSortBy(event.target.value)} 
                  className="input-field pl-11 !bg-white/60 !border-white/80 hover:!bg-white focus:!bg-white shadow-sm cursor-pointer appearance-none font-medium"
                >
                  <option value="newest">最新优先</option>
                  <option value="oldest">最早优先</option>
                  <option value={activeTab === 'attack' ? 'score' : 'confidence'}>
                    {activeTab === 'attack' ? '分数优先' : '置信度优先'}
                  </option>
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-graphite-500">
                  <svg className="h-4 w-4 fill-current" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                    <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                  </svg>
                </div>
              </label>

              <div className="flex gap-2">
                <button type="button" onClick={loadHistory} className="btn-secondary !bg-white/60 hover:!bg-white !border-white/80">
                  <RefreshCw className={`h-4 w-4 text-graphite-500 ${loading ? 'animate-spin text-electric-700' : ''}`} />
                </button>
                <button type="button" onClick={exportHistory} className="btn-secondary !bg-white/60 hover:!bg-white !border-white/80">
                  <Download className="h-4 w-4 text-graphite-500" />
                </button>
                <button type="button" onClick={clearHistory} className="btn-secondary !bg-lava-900/50 hover:!bg-lava-100/50 !border-lava-200/50 !text-lava-600">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </motion.section>

      <motion.section variants={itemVariants} className="card overflow-hidden !p-0">
        <div className="border-b border-graphite-200/50 bg-white/40 backdrop-blur-sm px-6 py-5">
          <h2 className="text-lg font-bold text-graphite-950">{activeTab === 'attack' ? '攻击记录列表' : '防御记录列表'}</h2>
          <p className="mt-1 text-sm font-medium text-graphite-500">
            {loading ? '正在加载数据…' : `当前共 ${filtered.length} 条可见记录。`}
          </p>
        </div>

        {!loading && filtered.length > 0 && (
          <TableMobileFallback
            items={filtered}
            renderTitle={(item) =>
              activeTab === 'attack'
                ? ATTACK_LABELS[item.attack_type] || item.attack_type
                : DEFENSE_LABELS[item.defense_type] || item.defense_type
            }
            renderMeta={(item) => (
              <>
                <p>模型：{item.model_name}</p>
                <p>时间：{formatDate(item.created_at)}</p>
                <p>
                  {activeTab === 'attack'
                    ? `分数：${Math.round((item.success_score || 0) * 100)}%`
                    : `置信度：${Math.round((item.confidence || 0) * 100)}%`}
                </p>
              </>
            )}
            renderRight={(item) => (
              <span className={`badge ${
                activeTab === 'attack'
                  ? badgeForAttackResult(item.result)
                  : badgeForDefenseResult(item.is_malicious)
              }`}>
                {activeTab === 'attack'
                  ? item.result === 'success'
                    ? '攻击成功'
                    : '已拦截'
                  : item.is_malicious
                    ? '检测到威胁'
                    : '内容安全'}
              </span>
            )}
          />
        )}

        <div className="hidden md:block">
          {loading ? (
            <div className="flex min-h-[280px] items-center justify-center bg-white/20 backdrop-blur-sm">
              <div className="spinner-lg" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex min-h-[280px] items-center justify-center px-6 text-center text-sm font-medium text-graphite-500 bg-white/20 backdrop-blur-sm">
              {searchTerm ? '没有找到匹配的记录。' : '当前页签还没有数据。'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-graphite-50/50 text-graphite-500">
                  <tr>
                    <th className="px-6 py-4 font-bold uppercase tracking-wider text-[11px]">时间</th>
                    <th className="px-6 py-4 font-bold uppercase tracking-wider text-[11px]">{activeTab === 'attack' ? '攻击类型' : '防御类型'}</th>
                    <th className="px-6 py-4 font-bold uppercase tracking-wider text-[11px]">目标模型</th>
                    <th className="px-6 py-4 font-bold uppercase tracking-wider text-[11px]">结果</th>
                    <th className="px-6 py-4 font-bold uppercase tracking-wider text-[11px]">{activeTab === 'attack' ? '成功分数' : '置信度'}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-graphite-100 bg-white/30 backdrop-blur-sm">
                  {filtered.map((item) => {
                    const typeLabel =
                      activeTab === 'attack'
                        ? ATTACK_LABELS[item.attack_type] || item.attack_type
                        : DEFENSE_LABELS[item.defense_type] || item.defense_type
                    const score = activeTab === 'attack' ? item.success_score || 0 : item.confidence || 0

                    return (
                      <tr key={item.id} className="transition-colors hover:bg-white/60">
                        <td className="px-6 py-4 font-medium text-graphite-600">{formatDate(item.created_at)}</td>
                        <td className="px-6 py-4">
                          <span className="badge border border-graphite-200 text-graphite-700 bg-white shadow-sm">{typeLabel}</span>
                        </td>
                        <td className="px-6 py-4 font-medium text-graphite-900">{item.model_name}</td>
                        <td className="px-6 py-4">
                          <span
                            className={`badge ${
                              activeTab === 'attack'
                                ? badgeForAttackResult(item.result)
                                : badgeForDefenseResult(item.is_malicious)
                            }`}
                          >
                            {activeTab === 'attack'
                              ? item.result === 'success'
                                ? '攻击成功'
                                : '已拦截'
                              : item.is_malicious
                                ? '检测到威胁'
                                : '内容安全'}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="h-1.5 w-24 overflow-hidden rounded-full bg-graphite-200">
                              <div
                                className={`h-full rounded-full transition-all duration-500 ${
                                  score >= 0.6 ? 'bg-lava-500' : 'bg-neon-500'
                                }`}
                                style={{ width: `${Math.round(score * 100)}%` }}
                              />
                            </div>
                            <span className="text-xs font-bold text-graphite-600">
                              {Math.round(score * 100)}%
                            </span>
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
      </motion.section>
    </motion.div>
  )
}
