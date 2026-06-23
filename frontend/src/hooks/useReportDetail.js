import { useEffect, useMemo, useState } from 'react'
import { reportApi } from '../api'
import { getReportDetailContent } from '../utils/demoReports'

export function useReportDetail(selected) {
  const isStaticDetail = Boolean(selected?._demo_mode || selected?.content)
  const staticContent = useMemo(
    () => (selected && isStaticDetail ? getReportDetailContent(selected) : null),
    [selected, isStaticDetail],
  )
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailContent, setDetailContent] = useState(null)

  useEffect(() => {
    if (!selected || isStaticDetail) return

    let cancelled = false
    const preview = getReportDetailContent(selected)

    queueMicrotask(() => {
      if (cancelled) return
      setDetailLoading(true)
      setDetailContent(preview)
    })

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
  }, [selected, isStaticDetail])

  if (!selected) {
    return { detailLoading: false, detailContent: null }
  }
  if (isStaticDetail) {
    return { detailLoading: false, detailContent: staticContent }
  }
  return { detailLoading, detailContent }
}