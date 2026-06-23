const STORAGE_KEY = 'mox_demo_reports'

function readStore() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function writeStore(items) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  } catch {
    // ignore quota errors
  }
}

export function saveDemoReport(report) {
  const entry = {
    ...report,
    _demo_mode: true,
    created_at: report.created_at || new Date().toLocaleString('zh-CN'),
  }
  const items = readStore().filter((item) => item.id !== entry.id)
  writeStore([entry, ...items].slice(0, 20))
  return entry
}

export function getDemoReports() {
  return readStore()
}

export function removeDemoReport(id) {
  writeStore(readStore().filter((item) => item.id !== id))
}

export function mergeWithDemoReports(apiReports = []) {
  const demo = getDemoReports()
  const demoIds = new Set(demo.map((item) => item.id))
  const remote = apiReports.filter((item) => !demoIds.has(item.id))
  return [...demo, ...remote]
}

export function getReportDetailContent(report) {
  if (!report) return null
  if (report.content) {
    if (typeof report.content === 'string') {
      try {
        return JSON.parse(report.content)
      } catch {
        return { raw: report.content }
      }
    }
    return report.content
  }
  if (report.summary) return report.summary
  return {
    report_name: report.report_name,
    report_type: report.report_type,
    model_name: report.model_name,
    attack_success_rate: report.attack_success_rate,
    defense_success_rate: report.defense_success_rate,
    _demo_mode: report._demo_mode,
  }
}

export function downloadDemoReportJson(report) {
  const payload = getReportDetailContent(report)
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${(report.report_name || 'demo-report').replace(/\s+/g, '_')}.json`
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}