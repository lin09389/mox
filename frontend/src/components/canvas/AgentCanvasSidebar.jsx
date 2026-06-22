import { Cpu, Server, Database, GripVertical } from 'lucide-react'

export default function AgentCanvasSidebar() {
  const onDragStart = (event, nodeType, data) => {
    event.dataTransfer.setData('application/reactflow', nodeType)
    event.dataTransfer.setData('application/reactflow/data', JSON.stringify(data))
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <aside className="w-64 border-r border-[var(--border-glass)] bg-[var(--bg-glass)] h-full flex flex-col backdrop-blur-xl shrink-0">
      <div className="p-4 border-b border-[var(--border-glass)]">
        <h3 className="font-bold text-[var(--text-main)]">组件库</h3>
        <p className="text-xs text-[var(--text-muted)] mt-1">拖拽组件至右侧画布中</p>
      </div>
      
      <div className="p-4 flex-1 overflow-y-auto space-y-6">
        
        {/* Section: Agents */}
        <div>
          <h4 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-3">智能体</h4>
          <div className="space-y-2">
            <div 
              className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg cursor-grab active:cursor-grabbing hover:bg-rose-500/20 transition-colors group flex items-center"
              onDragStart={(e) => onDragStart(e, 'agent', { label: '红队攻击者', strategy: 'DAN Jailbreak' })}
              draggable
            >
              <GripVertical className="w-4 h-4 text-rose-500/50 mr-2 group-hover:text-rose-500 transition-colors" />
              <Cpu className="w-4 h-4 text-rose-500 mr-2" />
              <span className="text-sm font-medium text-rose-500">攻击智能体</span>
            </div>
          </div>
        </div>

        {/* Section: Targets */}
        <div>
          <h4 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-3">靶机</h4>
          <div className="space-y-2">
            <div 
              className="p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg cursor-grab active:cursor-grabbing hover:bg-purple-500/20 transition-colors group flex items-center"
              onDragStart={(e) => onDragStart(e, 'target', { label: '生产大模型', endpoint: 'api.production.local' })}
              draggable
            >
              <GripVertical className="w-4 h-4 text-purple-500/50 mr-2 group-hover:text-purple-500 transition-colors" />
              <Server className="w-4 h-4 text-purple-500 mr-2" />
              <span className="text-sm font-medium text-purple-500">靶机节点</span>
            </div>
          </div>
        </div>

        {/* Section: Data */}
        <div>
          <h4 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-3">数据源</h4>
          <div className="space-y-2">
            <div 
              className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg cursor-grab active:cursor-grabbing hover:bg-blue-500/20 transition-colors group flex items-center"
              onDragStart={(e) => onDragStart(e, 'dataset', { label: 'OWASP Top 10' })}
              draggable
            >
              <GripVertical className="w-4 h-4 text-blue-500/50 mr-2 group-hover:text-blue-500 transition-colors" />
              <Database className="w-4 h-4 text-blue-500 mr-2" />
              <span className="text-sm font-medium text-blue-500">评测数据集</span>
            </div>
          </div>
        </div>

      </div>
    </aside>
  )
}
