import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { isDemoModeEnabled, reportApi } from '../../api'
import { useReportDetail } from '../../hooks/useReportDetail'
import { downloadDemoReportJson, mergeWithDemoReports, removeDemoReport } from '../../utils/demoReports'
import { SEED_REPORTS } from './constants'

export function useReportsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [reports, setReports] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)
  const [demoMode, setDemoMode] = useState(false)
  const highlightApplied = useRef(false)

  const highlightId = useMemo(() => {
    const raw = searchParams.get('highlight')
    if (!raw) return null
    const parsed = Number.parseInt(raw, 10)
    return Number.isFinite(parsed) ? parsed : null
  }, [searchParams])

  const dismissHighlight = useCallback(() => {
    const next = new URLSearchParams(searchParams)
    next.delete('highlight')
    setSearchParams(next, { replace: true })
    highlightApplied.current = false
  }, [searchParams, setSearchParams])

  useEffect(() => {
    let cancelled = false
    async function loadReports() {
      try {
        const data = await reportApi.list()
        if (cancelled) return
        const items = mergeWithDemoReports(data?.reports || (Array.isArray(data) ? data : []))
        setDemoMode(false)
        setReports(items)
        if (highlightId) {
          const match = items.find((item) => item.id === highlightId)
          if (match) {
            setSelected(match)
            highlightApplied.current = true
            requestAnimationFrame(() => {
              document.getElementById(`report-row-${highlightId}`)?.scrollIntoView({
                behavior: 'smooth',
                block: 'center',
              })
            })
          } else {
            toast.error(`未找到报告 #${highlightId}`)
            dismissHighlight()
            setSelected(items[0] || null)
          }
        } else {
          setSelected(items[0] || null)
        }
      } catch {
        if (cancelled) return
        if (isDemoModeEnabled) {
          const demoItems = mergeWithDemoReports(SEED_REPORTS.map((item) => ({ ...item, _demo_mode: true })))
          setDemoMode(true)
          setReports(demoItems)
          setSelected(demoItems[0] || null)
          toast('后端不可用，已展示演示报告。', { icon: '⚠️' })
        } else {
          toast.error('报告加载失败，请检查后端连接与登录状态。')
          setDemoMode(false)
          setReports([])
          setSelected(null)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    loadReports()
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    if (!highlightId || !reports.length || highlightApplied.current || loading) return
    const match = reports.find((item) => item.id === highlightId)
    if (!match) {
      toast.error(`未找到报告 #${highlightId}`)
      dismissHighlight()
      return
    }
    highlightApplied.current = true
    requestAnimationFrame(() => {
      setSelected(match)
      document.getElementById(`report-row-${highlightId}`)?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      })
    })
  }, [highlightId, reports, loading, dismissHighlight])

  const { detailLoading, detailContent } = useReportDetail(selected)

  const handleDelete = async (report) => {
    if (report._demo_mode) {
      removeDemoReport(report.id)
      setReports((current) => current.filter((item) => item.id !== report.id))
      setSelected((current) => (current?.id === report.id ? null : current))
      toast.success('演示报告已移除。')
      return
    }
    try {
      await reportApi.delete(report.id)
      setReports((current) => current.filter((item) => item.id !== report.id))
      setSelected((current) => (current?.id === report.id ? null : current))
      toast.success('报告已删除。可在审计日志筛选「报告删除」查看记录。')
    } catch (error) {
      const detail = error?.response?.data?.message || error?.response?.data?.detail
      toast.error(detail || '删除报告失败。')
    }
  }

  const handleDownload = async (report) => {
    if (report._demo_mode) {
      downloadDemoReportJson(report)
      toast.success('演示报告 JSON 已导出。')
      return
    }
    try {
      const filename = `${(report.report_name || 'report').replace(/\s+/g, '_')}.${report.format || 'json'}`
      await reportApi.download(report.id, filename)
      toast.success(`已下载 ${report.report_name}`)
    } catch {
      toast.error('报告下载失败，请确认已登录且具有访问权限。')
    }
  }

  const stats = useMemo(() => {
    const total = reports.length
    const attack = total ? Math.round((reports.reduce((sum, item) => sum + item.attack_success_rate, 0) / total) * 100) : 0
    const defense = total ? Math.round((reports.reduce((sum, item) => sum + item.defense_success_rate, 0) / total) * 100) : 0
    return { total, attack, defense }
  }, [reports])

  return {
    reports,
    selected,
    setSelected,
    loading,
    demoMode,
    highlightId,
    dismissHighlight,
    detailLoading,
    detailContent,
    handleDelete,
    handleDownload,
    stats,
  }
}