import { motion } from 'framer-motion'
import { AlertTriangle, BarChart3, CheckCircle2, Clock3, Shield } from 'lucide-react'
import { MetricCard, MetricCardSkeleton } from '../../components/ui/AppFrame'
import { HubPanelIntro } from '../../context/HubContext'
import { WorkspacePageShell } from '../../components/workspace'
import { itemVariants } from '../../utils/animations'
import HistoryRecordDetail from './HistoryRecordDetail'
import HistoryRecordList from './HistoryRecordList'
import HistoryToolbar from './HistoryToolbar'
import { useHistoryRecords } from './useHistoryRecords'

export default function HistoryPage() {
  const history = useHistoryRecords()

  return (
    <WorkspacePageShell>
      <HubPanelIntro description="统一查看攻击与防御记录，支持搜索、排序、导出和移动端浏览。" />

      <motion.div variants={itemVariants} className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {history.loading ? (
          Array.from({ length: 4 }).map((_, i) => <MetricCardSkeleton key={i} />)
        ) : (
          <>
            <MetricCard icon={BarChart3} label="总记录数" value={history.metrics.total} hint="当前页签下的所有记录" tone="electric" />
            <MetricCard
              icon={history.isAttack ? AlertTriangle : Shield}
              label={history.isAttack ? '攻击成功数' : '检测到威胁'}
              value={history.metrics.successCount}
              hint={history.isAttack ? '需要重点复盘的案例' : '被识别出的风险内容'}
              tone={history.isAttack ? 'lava' : 'amber'}
            />
            <MetricCard
              icon={CheckCircle2}
              label={history.isAttack ? '成功率' : '识别率'}
              value={`${history.metrics.ratio}%`}
              hint="帮助快速判断近期趋势"
              tone="neon"
            />
            <MetricCard icon={Clock3} label="今日新增" value={history.metrics.todayCount} hint="便于快速查看今天的变化" tone="graphite" />
          </>
        )}
      </motion.div>

      <motion.div variants={itemVariants}>
        <HistoryToolbar
          activeTab={history.activeTab}
          isAttack={history.isAttack}
          searchTerm={history.searchTerm}
          sortBy={history.sortBy}
          isFetching={history.isFetching}
          hasRecords={history.currentRaw.length > 0}
          onTabChange={history.switchTab}
          onSearchChange={history.setSearchTerm}
          onSortChange={history.setSortBy}
          onRefetch={history.refetch}
          onExport={history.exportHistory}
          onClear={history.clearHistory}
        />
      </motion.div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <motion.div variants={itemVariants}>
          <HistoryRecordList
            isAttack={history.isAttack}
            loading={history.loading}
            filtered={history.filtered}
            searchTerm={history.searchTerm}
            selectedRecord={history.selectedRecord}
            onSelect={history.setSelectedRecord}
          />
        </motion.div>

        <motion.div variants={itemVariants}>
          <HistoryRecordDetail
            isAttack={history.isAttack}
            selectedRecord={history.selectedRecord}
            linkedReportId={history.linkedReportId}
          />
        </motion.div>
      </div>
    </WorkspacePageShell>
  )
}