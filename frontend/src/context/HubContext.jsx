import { createContext, useContext } from 'react'
import { WorkspacePanelIntro } from '../components/workspace'

export const HubContext = createContext(null)

export function useHubContext() {
  return useContext(HubContext)
}

const THEMED_HUBS = new Set(['attack', 'testing', 'evaluation', 'governance'])

/** Hub 子页用 Panel 级标题，避免与 HubShell 大标题重复 */
export function HubPanelIntro({ description, action, badge }) {
  const hub = useHubContext()
  if (!hub) return null

  if (hub.theme && THEMED_HUBS.has(hub.theme)) {
    return (
      <WorkspacePanelIntro
        theme={hub.theme}
        description={description}
        action={action}
        badge={badge}
      />
    )
  }

  return (
    <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
      <div className="space-y-2 max-w-2xl">
        {description ? (
          <p className="text-sm font-medium text-[var(--text-muted)]">{description}</p>
        ) : null}
        {badge}
      </div>
      {action ? <div className="flex shrink-0 flex-wrap items-center gap-2">{action}</div> : null}
    </div>
  )
}