import { motion } from 'framer-motion'
import { FileText, Shield, TrendingUp } from 'lucide-react'
import { MetricCard } from '../../components/ui/AppFrame'
import { HubPanelIntro } from '../../context/HubContext'
import { WorkspacePageShell } from '../../components/workspace'
import { itemVariants } from '../../utils/animations'
import ReportHighlightBanner from './ReportHighlightBanner'
import ReportList from './ReportList'
import ReportPreviewPanel from './ReportPreviewPanel'
import { useReportsPage } from './useReportsPage'

export default function ReportPage() {
  const page = useReportsPage()

  return (
    <WorkspacePageShell>
      <HubPanelIntro
        description={
          page.demoMode
            ? '当前展示演示报告。完成评测后，真实报告将自动写入报告中心。'
            : '集中管理攻防评估结果，支持快速预览与导出。'
        }
        badge={
          page.demoMode ? (
            <span className="badge badge-info bg-amber-500/10 border-amber-500/30 text-amber-500 text-xs">
              演示数据
            </span>
          ) : null
        }
      />

      {page.highlightId && page.selected?.id === page.highlightId && (
        <ReportHighlightBanner highlightId={page.highlightId} onDismiss={page.dismissHighlight} />
      )}

      <motion.div variants={itemVariants} className="grid gap-4 md:grid-cols-3">
        <MetricCard icon={FileText} label="报告总数" value={page.stats.total} hint="当前存档数量" tone="electric" />
        <MetricCard icon={TrendingUp} label="平均攻击成功率" value={`${page.stats.attack}%`} hint="越高风险越大" tone="lava" />
        <MetricCard icon={Shield} label="平均防御成功率" value={`${page.stats.defense}%`} hint="越高越稳定" tone="neon" />
      </motion.div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <motion.div variants={itemVariants}>
          <ReportList
            reports={page.reports}
            loading={page.loading}
            selected={page.selected}
            highlightId={page.highlightId}
            onSelect={page.setSelected}
            onDownload={page.handleDownload}
            onDelete={page.handleDelete}
          />
        </motion.div>

        <motion.div variants={itemVariants}>
          <ReportPreviewPanel
            selected={page.selected}
            detailLoading={page.detailLoading}
            detailContent={page.detailContent}
            onDownload={page.handleDownload}
          />
        </motion.div>
      </div>
    </WorkspacePageShell>
  )
}