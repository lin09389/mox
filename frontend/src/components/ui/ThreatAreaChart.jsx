import { useMemo } from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts'
import { useTheme } from '../../hooks/useTheme'

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] px-3 py-2 rounded-lg shadow-soft backdrop-blur-md text-xs min-w-[120px]">
        <p className="font-bold text-[var(--text-main)] mb-2 border-b border-[var(--border-glass)] pb-1">{label}</p>
        <div className="flex justify-between text-rose-500 font-mono mb-1">
          <span>攻击载荷:</span>
          <span className="font-bold">{payload[0]?.value ?? 0}</span>
        </div>
        <div className="flex justify-between text-cyan-500 font-mono">
          <span>成功拦截:</span>
          <span className="font-bold">{payload[1]?.value ?? 0}</span>
        </div>
      </div>
    )
  }
  return null
}

export default function ThreatAreaChart({ series = [], isLoading = false }) {
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === 'dark'
  const data = useMemo(() => (Array.isArray(series) ? series : []), [series])

  if (isLoading) {
    return (
      <div className="flex h-full min-h-[250px] items-center justify-center text-sm text-[var(--text-muted)]">
        加载趋势数据...
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="flex h-full min-h-[250px] flex-col items-center justify-center rounded-xl border border-dashed border-[var(--border-glass-strong)] text-sm text-[var(--text-muted)]">
        暂无足够历史数据
      </div>
    )
  }

  return (
    <div className="w-full h-full min-h-[250px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
        >
          <defs>
            <linearGradient id="colorAttack" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorBlocked" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'} />
          <XAxis
            dataKey="time"
            axisLine={false}
            tickLine={false}
            tick={{ fill: isDark ? '#64748b' : '#94a3b8', fontSize: 10 }}
            dy={10}
            interval="preserveStartEnd"
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: isDark ? '#64748b' : '#94a3b8', fontSize: 10 }}
            allowDecimals={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="attack"
            stroke="#f43f5e"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorAttack)"
          />
          <Area
            type="monotone"
            dataKey="blocked"
            stroke="#06b6d4"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorBlocked)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}