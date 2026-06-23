import React, { useCallback, useEffect, useRef, useState } from 'react'
import {
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap
} from '@xyflow/react'
import toast from 'react-hot-toast'
import { Play, RefreshCw } from 'lucide-react'

import { nodeTypes } from '../components/canvas/nodes'
import AgentCanvasSidebar from '../components/canvas/AgentCanvasSidebar'
import { useTheme } from '../hooks/useTheme'
import { canvasApi } from '../api'

const initialNodes = [
  {
    id: 'dataset-1',
    type: 'dataset',
    position: { x: 50, y: 150 },
    data: { label: 'OWASP 评测库', source: 'OWASP Top 10 (2024)', size: '1,024 records' },
  },
  {
    id: 'agent-1',
    type: 'agent',
    position: { x: 400, y: 100 },
    data: { label: '红队攻击者 (主)', strategy: 'DAN Jailbreak', model: 'gpt-4-turbo' },
  },
  {
    id: 'agent-2',
    type: 'agent',
    position: { x: 400, y: 300 },
    data: { label: '红队辅助 (副)', strategy: '多模态注入', model: 'claude-3-opus' },
  },
  {
    id: 'target-1',
    type: 'target',
    position: { x: 800, y: 200 },
    data: { label: '生产核心大模型', endpoint: 'api.production.local/v1' },
  },
]

const initialEdges = [
  { id: 'e-data-ag1', source: 'dataset-1', target: 'agent-1', animated: true, style: { stroke: '#3b82f6', strokeWidth: 2 } },
  { id: 'e-data-ag2', source: 'dataset-1', target: 'agent-2', animated: true, style: { stroke: '#3b82f6', strokeWidth: 2 } },
  { id: 'e-ag1-target', source: 'agent-1', target: 'target-1', animated: true, style: { stroke: '#f43f5e', strokeWidth: 2 } },
  { id: 'e-ag2-target', source: 'agent-2', target: 'target-1', animated: true, style: { stroke: '#f43f5e', strokeWidth: 2 } },
]

let id = 0
const getId = () => `dndnode_${id++}`

function CanvasFlow() {
  const reactFlowWrapper = useRef(null)
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [reactFlowInstance, setReactFlowInstance] = useState(null)
  const { resolvedTheme } = useTheme()

  const onConnect = useCallback((params) => {
    // Add custom animated edge styling
    const animatedEdge = {
      ...params,
      animated: true,
      style: { stroke: '#f43f5e', strokeWidth: 2 } // rose-500
    }
    setEdges((eds) => addEdge(animatedEdge, eds))
  }, [setEdges])

  const onDragOver = useCallback((event) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback(
    (event) => {
      event.preventDefault()

      const type = event.dataTransfer.getData('application/reactflow')
      const rawData = event.dataTransfer.getData('application/reactflow/data')

      if (typeof type === 'undefined' || !type) {
        return
      }

      const parsedData = rawData ? JSON.parse(rawData) : {}

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      })
      
      const newNode = {
        id: getId(),
        type,
        position,
        data: parsedData,
      }

      setNodes((nds) => nds.concat(newNode))
    },
    [reactFlowInstance, setNodes]
  )

  const [isDeploying, setIsDeploying] = useState(false)
  const [runState, setRunState] = useState(null)
  const pollRef = useRef(null)

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  const handleRun = async () => {
    try {
      setIsDeploying(true)
      setRunState(null)
      const data = await canvasApi.deploy({ nodes, edges })
      setRunState({ run_id: data.run_id, status: 'running', progress: 0, logs: [] })

      if (pollRef.current) clearInterval(pollRef.current)
      pollRef.current = setInterval(async () => {
        try {
          const state = await canvasApi.getRun(data.run_id)
          setRunState(state)
          if (state.status === 'completed' || state.status === 'failed') {
            clearInterval(pollRef.current)
            pollRef.current = null
          }
        } catch {
          // keep polling
        }
      }, 2000)
    } catch (err) {
      toast.error(`部署失败: ${err.message}`)
    } finally {
      setIsDeploying(false)
    }
  }

  return (
    <div className="flex h-full w-full bg-[var(--bg-main)] rounded-2xl overflow-hidden border border-[var(--border-glass)] relative">
      <AgentCanvasSidebar />
      <div className="flex-1 h-full relative" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onInit={setReactFlowInstance}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          colorMode={resolvedTheme}
          fitView
        >
          <Background color={resolvedTheme === 'dark' ? '#334155' : '#cbd5e1'} gap={16} />
          <Controls className="!bg-[var(--bg-glass-strong)] !border-[var(--border-glass)] !fill-[var(--text-main)]" />
          <MiniMap 
            nodeColor={(node) => {
              switch (node.type) {
                case 'agent': return '#f43f5e'
                case 'target': return '#a855f7'
                case 'dataset': return '#3b82f6'
                default: return '#64748b'
              }
            }}
            maskColor={resolvedTheme === 'dark' ? 'rgba(15,23,42,0.7)' : 'rgba(248,250,252,0.7)'}
            className="!bg-[var(--bg-glass-strong)] !border-[var(--border-glass)]"
          />
        </ReactFlow>

        {/* Floating Action Bar */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-10">
          <div className="bg-[var(--bg-glass-strong)]/90 backdrop-blur-2xl border border-[var(--border-glass)] p-2 rounded-2xl shadow-[0_0_30px_rgba(6,182,212,0.12)] flex items-center gap-2 sm:gap-4">
            <div className="text-xs font-mono text-[var(--text-muted)] px-2 sm:px-3">
              节点 <span className="text-cyan-500 font-bold ml-1">{nodes.length}</span>
            </div>
            <div className="text-xs font-mono text-[var(--text-muted)] px-2 sm:px-3 border-l border-[var(--border-glass)]">
              连线 <span className="text-cyan-500 font-bold ml-1">{edges.length}</span>
            </div>
            <button
              type="button"
              onClick={handleRun}
              disabled={isDeploying}
              className={`btn-primary rounded-xl px-6 sm:px-8 py-2.5 flex items-center gap-2 ${
                isDeploying ? 'opacity-60 cursor-not-allowed' : ''
              }`}
            >
              {isDeploying ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  部署中…
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 fill-current" />
                  部署运行
                </>
              )}
            </button>
          </div>
        </div>

        {runState && (
          <div className="absolute top-4 right-4 z-10 w-80 rounded-xl border border-[var(--border-glass)] bg-[var(--bg-glass-strong)]/95 backdrop-blur-xl p-4 text-xs text-[var(--text-main)] shadow-lg">
            <p className="font-bold text-cyan-500 mb-2">任务 #{runState.run_id}</p>
            <p>状态：<span className="font-mono">{runState.status}</span></p>
            <p className="mt-1 text-[var(--text-muted)]">
              进度 {runState.progress ?? 0}%（{runState.completed_nodes ?? 0}/{runState.total_nodes ?? '?'}）
            </p>
            {runState.logs?.length > 0 && (
              <div className="mt-2 max-h-24 overflow-y-auto font-mono text-[10px] text-[var(--text-muted)] space-y-1">
                {runState.logs.slice(-5).map((log, i) => <p key={i}>{log}</p>)}
              </div>
            )}
            {runState.status === 'completed' && (
              <p className="mt-2 text-emerald-500">
                完成：{runState.attack_results?.length ?? 0} 次攻击，{runState.evaluations?.length ?? 0} 次评估
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default function AgentCanvasPage() {
  return (
    <div className="h-[calc(100vh-160px)] min-h-[600px]">
      <ReactFlowProvider>
        <CanvasFlow />
      </ReactFlowProvider>
    </div>
  )
}
