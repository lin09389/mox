import { useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { useQueryClient } from '@tanstack/react-query'
import { useAttackHistory, useDefenseHistory } from '../../hooks/queries'
import { extractReportId, normalizeHistoryResponse } from '../../utils/historyRecords'

export function useHistoryRecords() {
  const [activeTab, setActiveTab] = useState('attack')
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState('newest')
  const [selectedRecord, setSelectedRecord] = useState(null)

  const queryClient = useQueryClient()
  const attackQuery = useAttackHistory({ limit: 50 })
  const defenseQuery = useDefenseHistory({ limit: 50 })

  const isAttack = activeTab === 'attack'
  const loading = isAttack ? attackQuery.isLoading : defenseQuery.isLoading
  const isFetching = isAttack ? attackQuery.isFetching : defenseQuery.isFetching

  const currentRaw = useMemo(() => {
    const response = isAttack ? attackQuery.data : defenseQuery.data
    return normalizeHistoryResponse(response, isAttack ? 'attack' : 'defense')
  }, [isAttack, attackQuery.data, defenseQuery.data])

  const linkedReportId = useMemo(
    () => (selectedRecord ? extractReportId(selectedRecord) : null),
    [selectedRecord]
  )

  const filtered = useMemo(() => {
    const search = searchTerm.trim().toLowerCase()
    const list = currentRaw.filter((item) => {
      const type = isAttack ? item.attack_type : item.defense_type
      return !search || type?.toLowerCase().includes(search) || item.model_name?.toLowerCase().includes(search)
    })

    return [...list].sort((a, b) => {
      if (sortBy === 'oldest') return new Date(a.created_at) - new Date(b.created_at)
      if (sortBy === 'score') return (b.success_score || 0) - (a.success_score || 0)
      if (sortBy === 'confidence') return (b.confidence || 0) - (a.confidence || 0)
      return new Date(b.created_at) - new Date(a.created_at)
    })
  }, [isAttack, currentRaw, searchTerm, sortBy])

  const metrics = useMemo(() => {
    const total = currentRaw.length
    const successCount = isAttack
      ? currentRaw.filter((item) => item.result === 'success').length
      : currentRaw.filter((item) => item.is_malicious).length
    const todayCount = currentRaw.filter(
      (item) => new Date(item.created_at).toDateString() === new Date().toDateString()
    ).length

    return {
      total,
      successCount,
      ratio: total ? Math.round((successCount / total) * 100) : 0,
      todayCount,
    }
  }, [isAttack, currentRaw])

  const clearHistory = () => {
    if (isAttack) {
      queryClient.setQueryData(['attack', 'history', { limit: 50 }], { records: [] })
    } else {
      queryClient.setQueryData(['defense', 'history', { limit: 50 }], { records: [] })
    }
    toast.success('已清空当前页签记录。')
  }

  const exportHistory = () => {
    const data = JSON.stringify(currentRaw, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${activeTab}_history_${new Date().toISOString().slice(0, 10)}.json`
    anchor.click()
    URL.revokeObjectURL(url)
    toast.success('已导出当前记录。')
  }

  const refetch = () => {
    if (isAttack) attackQuery.refetch()
    else defenseQuery.refetch()
  }

  const switchTab = (tabId) => {
    setActiveTab(tabId)
    setSelectedRecord(null)
  }

  return {
    activeTab,
    isAttack,
    loading,
    isFetching,
    searchTerm,
    setSearchTerm,
    sortBy,
    setSortBy,
    selectedRecord,
    setSelectedRecord,
    filtered,
    metrics,
    linkedReportId,
    currentRaw,
    clearHistory,
    exportHistory,
    refetch,
    switchTab,
  }
}