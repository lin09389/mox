import { useCallback, useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { attackLoopApi } from '../../api'
import { useAttackLoopStream } from '../../hooks/useAttackLoopStream'
import { useModels } from '../../hooks/queries'
import { useTaskStore } from '../../store/useTaskStore'
import { buildAttackChartData, buildModelChartData } from './chartUtils'
import { DEFAULT_LOOP_CONFIG } from './constants'

export function useAttackLoopTask() {
  const { data: apiModels = [], isLoading: modelsLoading } = useModels()
  const registerLocalTask = useTaskStore((state) => state.registerLocalTask)
  const updateLocalTask = useTaskStore((state) => state.updateLocalTask)
  const finishLocalTask = useTaskStore((state) => state.finishLocalTask)
  const removeLocalTask = useTaskStore((state) => state.removeLocalTask)

  const [config, setConfig] = useState(DEFAULT_LOOP_CONFIG)
  const [isRunning, setIsRunning] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [taskId, setTaskId] = useState(null)
  const [progress, setProgress] = useState(null)
  const [results, setResults] = useState(null)
  const [reportId, setReportId] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('config')
  const [chartMetric, setChartMetric] = useState('success_rate')
  const [pickerModel, setPickerModel] = useState('llama3')
  const [newPrompt, setNewPrompt] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleWsProgress = useCallback((data) => {
    setProgress(data)
    if (data?.report_id) setReportId(data.report_id)
  }, [])

  const handleWsCompleted = useCallback((payload) => {
    const resultData = payload?.results ?? payload
    const savedReportId = payload?.report_id ?? null
    setIsRunning(false)
    setResults(resultData)
    if (savedReportId) setReportId(savedReportId)
    setActiveTab('results')
    if (taskId) {
      finishLocalTask(taskId, {
        progress: 100,
        status: 'completed',
        report_id: savedReportId,
      })
    }
    if (!savedReportId && taskId) {
      attackLoopApi.getProgress(taskId).then((data) => {
        if (data?.report_id) {
          setReportId(data.report_id)
          finishLocalTask(taskId, { progress: 100, status: 'completed', report_id: data.report_id })
        }
      }).catch(() => {})
    }
    toast.success(savedReportId ? '攻击循环完成，报告已入库。' : '攻击循环测试完成！')
  }, [taskId, finishLocalTask])

  const handleWsFailed = useCallback((errMsg) => {
    setIsRunning(false)
    setError(errMsg)
    if (taskId) removeLocalTask(taskId)
    toast.error('攻击循环测试失败')
  }, [taskId, removeLocalTask])

  useEffect(() => {
    if (!taskId || !progress) return
    const pct = progress.total
      ? Math.round((Number(progress.completed || 0) / Number(progress.total)) * 100)
      : Number(progress.progress ?? 0)
    updateLocalTask(taskId, { progress: Number.isFinite(pct) ? pct : 0 })
  }, [taskId, progress, updateLocalTask])

  const { connectionMode } = useAttackLoopStream(taskId, {
    enabled: isRunning && !isPaused,
    onProgress: handleWsProgress,
    onCompleted: handleWsCompleted,
    onFailed: handleWsFailed,
  })

  const handleStart = useCallback(async () => {
    try {
      setError(null)
      setResults(null)
      setProgress(null)
      setReportId(null)
      const data = await attackLoopApi.start(config)
      setTaskId(data.task_id)
      setIsRunning(true)
      setIsPaused(false)
      setActiveTab('progress')
      registerLocalTask({
        id: data.task_id,
        name: `攻击循环 (${data.task_id})`,
        source: 'attack_loop',
      })
      toast.success('攻击循环测试已启动')
    } catch (err) {
      setError(err.message)
      toast.error(`启动失败: ${err.message}`)
    }
  }, [config, registerLocalTask])

  const handlePause = useCallback(async () => {
    if (!taskId) return
    try {
      await attackLoopApi.pause(taskId)
      setIsPaused(true)
      toast.success('测试已暂停')
    } catch (err) {
      toast.error(`暂停失败: ${err.message}`)
    }
  }, [taskId])

  const handleResume = useCallback(async () => {
    if (!taskId) return
    try {
      await attackLoopApi.resume(taskId)
      setIsPaused(false)
      toast.success('测试已恢复')
    } catch (err) {
      toast.error(`恢复失败: ${err.message}`)
    }
  }, [taskId])

  const handleStop = useCallback(async () => {
    if (!taskId) return
    try {
      await attackLoopApi.stop(taskId)
      setIsRunning(false)
      setIsPaused(false)
      removeLocalTask(taskId)
      toast.success('测试已停止')
    } catch (err) {
      toast.error(`停止失败: ${err.message}`)
    }
  }, [taskId, removeLocalTask])

  const handleDownload = useCallback(async (format) => {
    if (!taskId) return
    try {
      const blob = await attackLoopApi.download(taskId, format)
      const url = window.URL.createObjectURL(new Blob([blob]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `attack_loop_${taskId}.${format}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      toast.success(`已下载 ${format.toUpperCase()} 文件`)
    } catch (err) {
      toast.error(`下载失败: ${err.message}`)
    }
  }, [taskId])

  const addPickerModel = useCallback(() => {
    const model = pickerModel.trim()
    if (model && !config.models.includes(model)) {
      setConfig((prev) => ({ ...prev, models: [...prev.models, model] }))
    }
  }, [pickerModel, config.models])

  const removeModel = useCallback((model) => {
    setConfig((prev) => ({ ...prev, models: prev.models.filter((m) => m !== model) }))
  }, [])

  const quickAddModels = useMemo(() => {
    const merged = [...new Set([...apiModels, pickerModel, 'llama3', 'qwen3:4b', 'gemma3:4b'].filter(Boolean))]
    return merged.filter((m) => !config.models.includes(m)).sort((a, b) => a.localeCompare(b))
  }, [apiModels, pickerModel, config.models])

  const toggleAttackType = useCallback((type) => {
    setConfig((prev) => ({
      ...prev,
      attack_types: prev.attack_types.includes(type)
        ? prev.attack_types.filter((t) => t !== type)
        : [...prev.attack_types, type],
    }))
  }, [])

  const addPrompt = useCallback(() => {
    if (newPrompt && !config.prompts.includes(newPrompt)) {
      setConfig((prev) => ({ ...prev, prompts: [...prev.prompts, newPrompt] }))
      setNewPrompt('')
    }
  }, [newPrompt, config.prompts])

  const removePrompt = useCallback((prompt) => {
    setConfig((prev) => ({ ...prev, prompts: prev.prompts.filter((p) => p !== prompt) }))
  }, [])

  const totalTests = config.models.length * config.attack_types.length * config.prompts.length * config.iterations_per_combo
  const canStart = config.models.length > 0 && config.attack_types.length > 0 && config.prompts.length > 0

  const modelChartData = useMemo(() => buildModelChartData(results), [results])
  const attackChartData = useMemo(() => buildAttackChartData(results), [results])

  return {
    config,
    setConfig,
    isRunning,
    isPaused,
    progress,
    results,
    reportId,
    error,
    activeTab,
    setActiveTab,
    chartMetric,
    setChartMetric,
    pickerModel,
    setPickerModel,
    newPrompt,
    setNewPrompt,
    showAdvanced,
    setShowAdvanced,
    modelsLoading,
    quickAddModels,
    totalTests,
    canStart,
    modelChartData,
    attackChartData,
    connectionMode,
    handleStart,
    handlePause,
    handleResume,
    handleStop,
    handleDownload,
    addPickerModel,
    removeModel,
    toggleAttackType,
    addPrompt,
    removePrompt,
  }
}