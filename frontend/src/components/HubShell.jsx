import { Suspense, useCallback, useMemo, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ChevronRight, Loader } from 'lucide-react'
import { HubContext } from '../context/HubContext'

function TabLoader() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center gap-3 text-sm text-[var(--text-muted)]">
      <Loader className="h-5 w-5 animate-spin text-cyan-500" />
      模块加载中...
    </div>
  )
}

export default function HubShell({
  icon: Icon,
  title,
  description,
  accentClass = 'text-cyan-400',
  tabIndicatorClass = 'bg-cyan-400',
  layoutId = 'hub-tab',
  defaultTab,
  tabStorageKey,
  tabs = [],
}) {
  const [searchParams, setSearchParams] = useSearchParams()
  const tabRefs = useRef([])

  const storedTab = tabStorageKey
    ? (() => {
        try {
          return localStorage.getItem(tabStorageKey)
        } catch {
          return null
        }
      })()
    : null

  const activeTab =
    searchParams.get('tab') ||
    (storedTab && tabs.some((tab) => tab.id === storedTab) ? storedTab : null) ||
    defaultTab

  const activePanel = useMemo(
    () => tabs.find((tab) => tab.id === activeTab) ?? tabs[0],
    [tabs, activeTab]
  )

  const handleTabChange = useCallback(
    (tabId) => {
      if (tabStorageKey) {
        try {
          localStorage.setItem(tabStorageKey, tabId)
        } catch {
          // ignore quota / privacy mode
        }
      }
      const next = new URLSearchParams(searchParams)
      next.set('tab', tabId)
      if (tabId !== 'reports') next.delete('highlight')
      if (tabId !== 'audit') next.delete('action')
      setSearchParams(next, { replace: true })
    },
    [searchParams, setSearchParams, tabStorageKey]
  )

  const focusTab = useCallback((index) => {
    const el = tabRefs.current[index]
    if (el) el.focus()
  }, [])

  const handleTabKeyDown = useCallback(
    (event, index) => {
      const last = tabs.length - 1
      let next = index
      if (event.key === 'ArrowRight') {
        event.preventDefault()
        next = index >= last ? 0 : index + 1
      } else if (event.key === 'ArrowLeft') {
        event.preventDefault()
        next = index <= 0 ? last : index - 1
      } else if (event.key === 'Home') {
        event.preventDefault()
        next = 0
      } else if (event.key === 'End') {
        event.preventDefault()
        next = last
      } else {
        return
      }
      const tab = tabs[next]
      if (tab) {
        handleTabChange(tab.id)
        focusTab(next)
      }
    },
    [tabs, focusTab, handleTabChange]
  )

  const Panel = activePanel?.component

  const hubValue = useMemo(
    () => ({
      hubTitle: title,
      tabId: activeTab,
      tabLabel: activePanel?.label || '',
      accentClass,
    }),
    [title, activeTab, activePanel?.label, accentClass]
  )

  return (
    <div className="flex h-full flex-col space-y-6">
      <div className="flex flex-col space-y-4">
        <div>
          <nav aria-label="工作台导航" className="mb-2 flex items-center gap-1.5 text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">
            <span>{title}</span>
            {activePanel?.label ? (
              <>
                <ChevronRight className="h-3.5 w-3.5 opacity-60" aria-hidden />
                <span className={accentClass}>{activePanel.label}</span>
              </>
            ) : null}
          </nav>
          <h1 className={`flex items-center gap-2 text-2xl font-bold tracking-tight text-[var(--text-main)]`}>
            {Icon ? <Icon className={`h-6 w-6 ${accentClass}`} /> : null}
            {activePanel?.label || title}
          </h1>
          {description ? <p className="mt-1 text-sm text-[var(--text-muted)]">{description}</p> : null}
        </div>

        <div
          role="tablist"
          aria-label={`${title} 标签`}
          className="scrollbar-hide flex space-x-1 overflow-x-auto border-b border-[var(--border-glass)] pb-px"
        >
          {tabs.map((tab, index) => {
            const TabIcon = tab.icon
            const isActive = activeTab === tab.id
            const panelId = `hub-panel-${layoutId}-${tab.id}`
            return (
              <button
                key={tab.id}
                ref={(el) => {
                  tabRefs.current[index] = el
                }}
                type="button"
                role="tab"
                id={`hub-tab-${layoutId}-${tab.id}`}
                aria-selected={isActive}
                aria-controls={panelId}
                tabIndex={isActive ? 0 : -1}
                onClick={() => handleTabChange(tab.id)}
                onKeyDown={(event) => handleTabKeyDown(event, index)}
                className={`relative flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${
                  isActive ? accentClass : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
                }`}
              >
                {TabIcon ? <TabIcon className="h-4 w-4" /> : null}
                {tab.label}
                {isActive ? (
                  <motion.div
                    layoutId={layoutId}
                    className={`absolute bottom-0 left-0 right-0 h-0.5 rounded-t-full ${tabIndicatorClass}`}
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                ) : null}
              </button>
            )
          })}
        </div>
      </div>

      <div
        className="relative flex-1 overflow-hidden"
        role="tabpanel"
        id={`hub-panel-${layoutId}-${activeTab}`}
        aria-labelledby={`hub-tab-${layoutId}-${activeTab}`}
      >
        {Panel ? (
          <HubContext.Provider value={hubValue}>
            <Suspense fallback={<TabLoader />}>
              <Panel />
            </Suspense>
          </HubContext.Provider>
        ) : null}
      </div>
    </div>
  )
}