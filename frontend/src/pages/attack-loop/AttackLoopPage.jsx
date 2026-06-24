import { AnimatePresence, motion } from 'framer-motion'
import { Activity, AlertTriangle, BarChart3, Settings } from 'lucide-react'
import { HubPanelIntro } from '../../context/HubContext'
import { WorkspacePageShell } from '../../components/workspace'
import { itemVariants } from '../../utils/animations'
import AttackLoopConfigPanel from './AttackLoopConfigPanel'
import AttackLoopProgressPanel from './AttackLoopProgressPanel'
import AttackLoopResultsPanel from './AttackLoopResultsPanel'
import AttackLoopToolbar from './AttackLoopToolbar'
import { useAttackLoopTask } from './useAttackLoopTask'
import { useAttackLoopTypes } from './useAttackLoopTypes'

const TAB_ICONS = {
  config: Settings,
  progress: Activity,
  results: BarChart3,
}

const TABS = [
  { id: 'config', label: '任务配置' },
  { id: 'progress', label: '实时监控' },
  { id: 'results', label: '分析报告' },
]

export default function AttackLoopPage() {
  const { attackTypesByCategory, typesLoading } = useAttackLoopTypes()
  const task = useAttackLoopTask()

  return (
    <WorkspacePageShell>
      <HubPanelIntro
        description="配置并发测试任务，组合模型、攻击类型与诱导提示词，实现无人值守的安全漏洞挖掘。"
        action={(
          <AttackLoopToolbar
            isRunning={task.isRunning}
            isPaused={task.isPaused}
            connectionMode={task.connectionMode}
            canStart={task.canStart}
            onStart={task.handleStart}
            onPause={task.handlePause}
            onResume={task.handleResume}
            onStop={task.handleStop}
          />
        )}
      />

      <motion.div variants={itemVariants} className="flex flex-wrap w-fit gap-2 p-1.5 rounded-2xl bg-[var(--bg-glass-strong)] border border-[var(--border-glass-strong)] shadow-sm backdrop-blur-md">
        {TABS.map((tab) => {
          const Icon = TAB_ICONS[tab.id]
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => task.setActiveTab(tab.id)}
              className={`flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-bold transition-all duration-300 ${task.activeTab === tab.id ? 'bg-cyan-500 text-white shadow-soft' : 'text-[var(--text-muted)] hover:bg-[var(--bg-glass)] hover:text-[var(--text-main)]'}`}
            >
              <Icon className="h-4.5 w-4.5" /> {tab.label}
            </button>
          )
        })}
      </motion.div>

      <AnimatePresence mode="wait">
        {task.activeTab === 'config' && (
          <AttackLoopConfigPanel
            config={task.config}
            setConfig={task.setConfig}
            typesLoading={typesLoading}
            attackTypesByCategory={attackTypesByCategory}
            modelsLoading={task.modelsLoading}
            quickAddModels={task.quickAddModels}
            pickerModel={task.pickerModel}
            setPickerModel={task.setPickerModel}
            addPickerModel={task.addPickerModel}
            removeModel={task.removeModel}
            toggleAttackType={task.toggleAttackType}
            newPrompt={task.newPrompt}
            setNewPrompt={task.setNewPrompt}
            addPrompt={task.addPrompt}
            removePrompt={task.removePrompt}
            showAdvanced={task.showAdvanced}
            setShowAdvanced={task.setShowAdvanced}
            totalTests={task.totalTests}
          />
        )}
        {task.activeTab === 'progress' && (
          <AttackLoopProgressPanel progress={task.progress} />
        )}
        {task.activeTab === 'results' && (
          <AttackLoopResultsPanel
            results={task.results}
            reportId={task.reportId}
            chartMetric={task.chartMetric}
            setChartMetric={task.setChartMetric}
            modelChartData={task.modelChartData}
            attackChartData={task.attackChartData}
            onDownload={task.handleDownload}
          />
        )}
      </AnimatePresence>

      {task.error && (
        <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-5 mt-6 backdrop-blur-md">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-rose-500/20 rounded-lg"><AlertTriangle className="h-5 w-5 text-rose-500" /></div>
            <div>
              <h4 className="font-bold text-rose-500 mb-1">系统故障 / 异常拦截</h4>
              <p className="text-sm font-medium text-rose-500/80 leading-relaxed">{task.error}</p>
            </div>
          </div>
        </motion.div>
      )}
    </WorkspacePageShell>
  )
}