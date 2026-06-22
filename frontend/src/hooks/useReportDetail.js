import { useEffect, useState } from 'react'
import { reportApi } from '../api'
import { getReportDetailContent } from '../utils/demoReports'

export function useReportDetail(selected) {
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailContent, setDetailContent] = useState(null)

  useEffect(() => {
    if (!selected) {
      setDetailContent(null)
      setDetailLoading(false)
      return
    }

    if (selected._demo_mode || selected.content) {
      setDetailContent(getReportDetailContent(selected))
      setDetailLoading(false)
      return
    }

    let cancelled = false
    setDetailLoading(true)
    setDetailContent(getReportDetailContent(selected))

    reportApi.get(selected.id)
      .then((full) => {
        if (cancelled) return
        setDetailContent(getReportDetailContent(full))
      })
      .catch(() => {
        if (cancelled) return
        setDetailContent(getReportDetailContent(selected))
      })
      .finally(() => {
        if (!cancelled) setDetailLoading(false)
      })

    return () => { cancelled = true }
  }, [selected])

  return { detailLoading, detailContent }
}