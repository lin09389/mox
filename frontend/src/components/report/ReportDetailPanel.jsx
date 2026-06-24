import { detectReportViewType, parseReportContent } from '../../utils/reportDetail'
import RedTeamReportDetail from './RedTeamReportDetail'
import AttackLoopReportDetail from './AttackLoopReportDetail'
import AutoRedTeamReportDetail from './AutoRedTeamReportDetail'
import RawJsonReportDetail from './RawJsonReportDetail'

const VIEW_LABELS = {
  redteam: '红队演练详情',
  attack_loop: '攻击循环详情',
  auto_redteam: '自动红队详情',
  owasp: 'OWASP 测试详情',
  raw: '报告数据',
}

export default function ReportDetailPanel({ report, content, isDemo = false }) {
  const parsed = parseReportContent(content)
  if (!parsed) return null

  const viewType = detectReportViewType(report?.report_type, parsed)

  return (
    <div className="space-y-4">
      <p className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">
        {VIEW_LABELS[viewType] || VIEW_LABELS.raw}
      </p>

      {viewType === 'redteam' && <RedTeamReportDetail content={parsed} />}
      {viewType === 'attack_loop' && <AttackLoopReportDetail content={parsed} />}
      {viewType === 'auto_redteam' && <AutoRedTeamReportDetail content={parsed} />}
      {viewType === 'owasp' && (
        <div className="space-y-2">
          {parsed.results?.map((item, index) => (
            <div key={`${item.category}-${index}`} className="flex items-center justify-between rounded-lg border border-[var(--border-glass)] bg-[var(--bg-glass)] px-3 py-2 text-xs">
              <span className="font-bold">{item.test || item.category}</span>
              <span className={item.vulnerable || item.passed === false ? 'text-rose-500' : 'text-emerald-500'}>
                {item.vulnerable || item.passed === false ? '存在风险' : '通过'}
              </span>
            </div>
          ))}
        </div>
      )}
      {viewType === 'raw' ? (
        <RawJsonReportDetail content={parsed} isDemo={isDemo} defaultExpanded />
      ) : (
        <RawJsonReportDetail content={parsed} isDemo={isDemo} />
      )}
    </div>
  )
}