import { useEffect, useMemo, useState } from 'react'
import { attackLoopApi } from '../../api'
import { FALLBACK_ATTACK_TYPES } from './constants'

function normalizeAttackTypes(data) {
  if (data?.attack_types && Array.isArray(data.attack_types)) {
    return data.attack_types.map((t) => ({
      value: t.value || t.key,
      name: t.name,
      category: t.category,
      description: t.description,
    }))
  }
  if (Array.isArray(data)) {
    return data.map((t) => ({
      value: t.value || t.key,
      name: t.name,
      category: t.category,
      description: t.description,
    }))
  }
  if (data && typeof data === 'object') {
    const flat = Object.values(data).flat()
    if (flat.length > 0) {
      return flat.map((t) => ({
        value: t.value || t.key,
        name: t.name,
        category: t.category,
        description: t.description,
      }))
    }
  }
  return null
}

export function useAttackLoopTypes() {
  const [attackTypes, setAttackTypes] = useState(FALLBACK_ATTACK_TYPES)
  const [typesLoading, setTypesLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function fetchTypes() {
      try {
        const data = await attackLoopApi.getTypes()
        if (cancelled) return
        const normalized = normalizeAttackTypes(data)
        if (normalized?.length) setAttackTypes(normalized)
      } catch {
        // keep fallback list
      } finally {
        if (!cancelled) setTypesLoading(false)
      }
    }
    fetchTypes()
    return () => { cancelled = true }
  }, [])

  const attackTypesByCategory = useMemo(() => {
    const groups = {}
    for (const t of attackTypes) {
      const cat = t.category || '其它'
      if (!groups[cat]) groups[cat] = []
      groups[cat].push(t)
    }
    return groups
  }, [attackTypes])

  return { attackTypes, attackTypesByCategory, typesLoading }
}