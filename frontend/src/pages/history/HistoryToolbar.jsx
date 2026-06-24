import { Download, Filter, RefreshCw, Search, Trash2 } from 'lucide-react'
import { PanelHeader } from '../../components/ui/AppFrame'
import { TABS } from './constants'

export default function HistoryToolbar({
  activeTab,
  isAttack,
  searchTerm,
  sortBy,
  isFetching,
  hasRecords,
  onTabChange,
  onSearchChange,
  onSortChange,
  onRefetch,
  onExport,
  onClear,
}) {
  return (
    <section className="card p-5">
      <PanelHeader
        title="筛选与操作"
        description="优先把常用动作聚合在一行，减少来回切页。"
      />
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex flex-wrap w-fit gap-1 p-1 rounded-xl bg-[var(--bg-glass-strong)] border border-[var(--border-glass-strong)] shadow-sm backdrop-blur-md">
          {TABS.map((tab) => {
            const Icon = tab.icon
            const active = tab.id === activeTab
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => onTabChange(tab.id)}
                className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-bold transition-all duration-300 ${active ? 'bg-cyan-500 text-white shadow-soft' : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-glass)]'}`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            )
          })}
        </div>

        <div className="flex flex-col gap-3 md:flex-row md:items-center">
          <label className="relative min-w-[220px]">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              type="text"
              value={searchTerm}
              onChange={(event) => onSearchChange(event.target.value)}
              className="input-field pl-10"
              placeholder="搜索类型或模型"
            />
          </label>

          <label className="relative min-w-[180px]">
            <Filter className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" />
            <select
              value={sortBy}
              onChange={(event) => onSortChange(event.target.value)}
              className="input-field pl-10 appearance-none bg-no-repeat bg-[right_0.5rem_center] bg-[length:1.5em_1.5em]"
            >
              <option value="newest">最新优先</option>
              <option value="oldest">最早优先</option>
              <option value={isAttack ? 'score' : 'confidence'}>
                {isAttack ? '分数优先' : '置信度优先'}
              </option>
            </select>
          </label>

          <div className="flex gap-2">
            <button type="button" onClick={onRefetch} className="btn-secondary h-[42px]" disabled={isFetching}>
              <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
            </button>
            <button type="button" onClick={onExport} className="btn-secondary h-[42px]" disabled={!hasRecords}>
              <Download className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={onClear}
              className="btn-ghost text-rose-500 hover:text-rose-600 hover:bg-rose-500/10 h-[42px]"
              disabled={!hasRecords}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}