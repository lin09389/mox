import { buildGovernanceReportLink } from '../api'

const SOURCE_ROUTES = {
  attack_loop: '/testing?tab=loop',
  auto_redteam: '/testing?tab=auto-redteam',
  benchmark: '/evaluation?tab=benchmark',
  queue: '/tasks',
}

export function getTaskHref(task) {
  if (task?.href) return task.href
  const reportId = task?.report_id ?? task?.reportId
  const status = String(task?.status || '')
  if (reportId != null && reportId !== '' && status === 'completed') {
    return buildGovernanceReportLink(reportId)
  }
  const source = task?.source
  if (source && SOURCE_ROUTES[source]) return SOURCE_ROUTES[source]
  return '/tasks'
}

export function normalizeRemoteTask(raw) {
  const id = raw?.id || raw?.task_id || 'unknown'
  const source = raw?.source || 'queue'
  let name = raw?.name
  if (!name) {
    if (source === 'auto_redteam') {
      name = `自动红队 (${raw?.target_model || id})`
    } else if (source === 'attack_loop') {
      name = `攻击循环 (${id})`
    } else {
      name = `任务 ${id}`
    }
  }

  let progress = Number(raw?.progress ?? 0)
  if (!progress && raw?.total) {
    progress = Math.round((Number(raw?.completed || 0) / Number(raw.total)) * 100)
  }

  let status = raw?.status || 'unknown'
  if (String(status).startsWith('completed')) status = 'completed'

  const reportId = raw?.report_id ?? raw?.reportId ?? null

  return {
    id,
    name,
    status,
    progress: Math.min(100, Math.max(0, progress)),
    source,
    report_id: reportId,
    href: getTaskHref({ source, status, report_id: reportId }),
  }
}

export function isActiveTask(task) {
  const status = String(task?.status || '')
  return status === 'running' || status === 'pending' || status === 'paused'
}