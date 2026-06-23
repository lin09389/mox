import { AlertTriangle, Wifi, WifiOff } from 'lucide-react'
import { isDemoModeEnabled } from '../../api'
import { useApiStatus } from '../../hooks/useApiStatus'

export default function DemoBanner({ enabled = true }) {
  const { isConnected, isDegraded, isDisconnected } = useApiStatus(30000, enabled)

  if (!enabled) return null

  const showDemo = isDemoModeEnabled
  const showOffline = isDisconnected && !isDemoModeEnabled
  const showDegraded = isDegraded

  if (!showDemo && !showOffline && !showDegraded) return null

  let message = ''
  let tone = 'amber'

  if (showOffline) {
    message = '后端 API 未连接。请启动服务（python -m mox api），否则多数操作将失败。'
    tone = 'rose'
  } else if (showDegraded) {
    message = 'API 处于降级状态，部分请求可能失败。建议检查后端日志与网络连接。'
    tone = 'amber'
  } else if (showDemo) {
    message = '演示模式已开启：后端不可用时将展示本地模拟数据，写入/下载类操作不会持久化。'
    tone = 'amber'
  }

  const styles = {
    amber: 'border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400',
    rose: 'border-rose-500/30 bg-rose-500/10 text-rose-600 dark:text-rose-400',
  }

  const Icon = showOffline ? WifiOff : showDemo && isConnected ? AlertTriangle : isConnected ? Wifi : AlertTriangle

  return (
    <div
      role="status"
      className={`border-b px-4 py-2.5 text-sm font-medium ${styles[tone]}`}
    >
      <div className="app-container flex items-start gap-3">
        <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
        <p>{message}</p>
      </div>
    </div>
  )
}

/** 是否允许调用会写入后端的操作 */
export function canUseLiveBackend(apiStatus) {
  return apiStatus === 'connected' && !isDemoModeEnabled
}