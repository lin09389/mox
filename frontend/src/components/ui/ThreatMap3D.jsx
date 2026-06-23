import { useEffect, useRef, useState, useMemo } from 'react'
import ForceGraph3D from 'react-force-graph-3d'
import { useTheme } from '../../hooks/useTheme'

function TopologyList({ nodes = [], links = [] }) {
  const attacks = nodes.filter((n) => n.group?.startsWith('attack'))
  return (
    <div className="flex h-full min-h-[300px] flex-col gap-3 overflow-y-auto p-4">
      <p className="text-xs text-[var(--text-muted)]">动画已关闭（减少动态效果偏好）</p>
      {attacks.length === 0 ? (
        <p className="text-sm text-[var(--text-muted)]">暂无威胁节点数据</p>
      ) : (
        attacks.map((node) => (
          <div
            key={node.id}
            className="rounded-lg border border-[var(--border-glass)] bg-[var(--bg-glass-strong)] px-3 py-2 text-sm"
          >
            <span className={`mr-2 inline-block h-2 w-2 rounded-full ${node.group === 'attack_active' ? 'bg-red-500' : 'bg-amber-500'}`} />
            {node.name}
          </div>
        ))
      )}
      <p className="text-xs text-[var(--text-muted)]">链路数: {links.length}</p>
    </div>
  )
}

export default function ThreatMap3D({ nodes = [], links = [], isLoading = false }) {
  const fgRef = useRef()
  const containerRef = useRef()
  const { resolvedTheme } = useTheme()
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })
  const [reduceMotion, setReduceMotion] = useState(false)

  const graphData = useMemo(
    () => ({
      nodes: Array.isArray(nodes) ? nodes : [],
      links: (Array.isArray(links) ? links : []).map((link) => ({
        ...link,
        color: link.blocked ? '#f59e0b' : '#ef4444',
        particleSpeed: link.blocked ? 0.01 : 0.03,
      })),
    }),
    [nodes, links]
  )

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const update = () => setReduceMotion(mq.matches)
    update()
    mq.addEventListener('change', update)
    return () => mq.removeEventListener('change', update)
  }, [])

  useEffect(() => {
    if (!containerRef.current) return
    const resizeObserver = new ResizeObserver((entries) => {
      if (!entries || entries.length === 0) return
      const { width, height } = entries[0].contentRect
      setDimensions({ width, height })
    })
    resizeObserver.observe(containerRef.current)
    return () => resizeObserver.disconnect()
  }, [])

  useEffect(() => {
    if (reduceMotion) return undefined
    let angle = 0
    const distance = 300
    const interval = setInterval(() => {
      if (fgRef.current) {
        fgRef.current.cameraPosition({
          x: distance * Math.sin(angle),
          z: distance * Math.cos(angle),
        })
        angle += Math.PI / 800
      }
    }, 20)
    return () => clearInterval(interval)
  }, [reduceMotion])

  const getNodeColor = (node) => {
    switch (node.group) {
      case 'core': return resolvedTheme === 'dark' ? '#c084fc' : '#a855f7'
      case 'defense': return resolvedTheme === 'dark' ? '#22d3ee' : '#06b6d4'
      case 'attack_active': return '#ef4444'
      case 'attack_blocked': return '#f59e0b'
      default: return '#64748b'
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-full min-h-[300px] items-center justify-center text-sm text-[var(--text-muted)]">
        加载威胁拓扑...
      </div>
    )
  }

  if (graphData.nodes.length === 0) {
    return (
      <div className="flex h-full min-h-[300px] flex-col items-center justify-center rounded-xl border border-dashed border-[var(--border-glass-strong)] text-sm text-[var(--text-muted)]">
        暂无拓扑数据，运行攻击测试后将自动生成
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="w-full h-full min-h-[300px] overflow-hidden relative"
      style={{
        background: resolvedTheme === 'dark'
          ? 'radial-gradient(circle at center, rgba(14,165,233,0.05) 0%, rgba(2,6,23,1) 100%)'
          : 'radial-gradient(circle at center, rgba(14,165,233,0.03) 0%, rgba(248,250,252,1) 100%)',
      }}
    >
      <div className="absolute bottom-6 left-6 z-10 flex flex-col gap-2 pointer-events-none bg-[var(--bg-glass-strong)] backdrop-blur-md p-3 rounded-xl border border-[var(--border-glass)] shadow-soft">
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="w-2.5 h-2.5 rounded-full bg-purple-500" />
          <span className="text-[var(--text-main)] font-semibold">核心资产 (LLM)</span>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-500" />
          <span className="text-[var(--text-muted)]">防御节点</span>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
          <span className="text-[var(--text-muted)]">活跃威胁</span>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
          <span className="text-[var(--text-muted)]">已拦截载荷</span>
        </div>
      </div>

      {reduceMotion ? (
        <TopologyList nodes={graphData.nodes} links={graphData.links} />
      ) : (
        dimensions.width > 0 &&
        dimensions.height > 0 && (
          <ForceGraph3D
            ref={fgRef}
            width={dimensions.width}
            height={dimensions.height}
            graphData={graphData}
            nodeLabel="name"
            nodeColor={getNodeColor}
            nodeResolution={16}
            linkDirectionalParticles={2}
            linkDirectionalParticleWidth={1.5}
            linkDirectionalParticleSpeed={(d) => d.particleSpeed || 0.01}
            linkColor={(d) => d.color}
            linkOpacity={0.4}
            backgroundColor="rgba(0,0,0,0)"
            showNavInfo={false}
          />
        )
      )}
    </div>
  )
}