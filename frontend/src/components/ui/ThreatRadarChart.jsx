import { useMemo } from 'react'
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip
} from 'recharts'
import { useTheme } from '../../hooks/useTheme'

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] px-3 py-2 rounded-lg shadow-soft backdrop-blur-md text-xs">
        <p className="font-bold text-[var(--text-main)] mb-1">{payload[0].payload.subject}</p>
        <p className="text-rose-500 font-mono">风险指数: {payload[0].value}/100</p>
      </div>
    )
  }
  return null
}

export default function ThreatRadarChart({ items = [], isLoading = false }) {
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === 'dark'

  const data = useMemo(
    () =>
      (Array.isArray(items) ? items : []).map((item) => ({
        subject: item.subject,
        A: item.value ?? 0,
        fullMark: 100,
      })),
    [items]
  )

  if (isLoading) {
    return (
      <div className="flex h-full min-h-[250px] items-center justify-center text-sm text-[var(--text-muted)]">
        加载暴露面数据...
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="flex h-full min-h-[250px] flex-col items-center justify-center rounded-xl border border-dashed border-[var(--border-glass-strong)] text-sm text-[var(--text-muted)]">
        暂无攻击类型分布数据
      </div>
    )
  }

  return (
    <div className="w-full h-full min-h-[250px]">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke={isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'} />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: isDark ? '#94a3b8' : '#64748b', fontSize: 11, fontWeight: 600 }}
          />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Radar
            name="Risk"
            dataKey="A"
            stroke="#f43f5e"
            strokeWidth={2}
            fill="#f43f5e"
            fillOpacity={0.3}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}