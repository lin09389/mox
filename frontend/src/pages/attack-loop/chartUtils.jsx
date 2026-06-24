import { CHART_COLORS } from './constants'

export function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass-strong)] px-4 py-3 shadow-soft backdrop-blur-md">
      <p className="mb-2 text-xs font-bold text-[var(--text-main)]">{label}</p>
      {payload.map((entry) => (
        <p key={entry.name} className="text-xs font-mono" style={{ color: entry.color }}>
          {entry.name}: {entry.value}
        </p>
      ))}
    </div>
  )
}

export function buildModelChartData(results) {
  if (!results?.model_stats) return []
  return Object.entries(results.model_stats).map(([model, stats]) => ({
    name: model,
    success_rate: Number((stats.success_rate ?? 0).toFixed(1)),
    avg_score: Number(((stats.avg_score ?? 0) * 100).toFixed(1)),
    successful: stats.successful ?? 0,
    total: stats.total ?? 0,
  }))
}

export function buildAttackChartData(results) {
  if (!results?.attack_stats) return []
  return Object.entries(results.attack_stats).map(([type, stats]) => ({
    name: stats.name || type,
    success_rate: Number((stats.success_rate ?? 0).toFixed(1)),
    avg_score: Number(((stats.avg_score ?? 0) * 100).toFixed(1)),
    successful: stats.successful ?? 0,
    total: stats.total ?? 0,
  }))
}

export { CHART_COLORS }