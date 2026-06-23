import { NavLink, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useMemo, useState } from 'react'
import clsx from 'clsx'
import {
  ChevronRight,
  CreditCard,
  LogIn,
  LogOut,
  Menu,
  User,
  X,
  Sun,
  Moon,
  ChevronDown,
} from 'lucide-react'
import { NAV_GROUPS } from '../constants/copy'
import { StatusPill } from './ui/AppFrame'
import { useApiStatus } from '../hooks/useApiStatus'
import { useTheme } from '../hooks/useTheme'
import { useAuthSession, clearSession } from '../auth'
import { authCardVariants, drawerVariants, pageVariants } from '../utils/animations'
import { TaskTray } from './ui/TaskTray'
import DemoBanner from './ui/DemoBanner'

const PRIMARY_GROUPS = NAV_GROUPS
const SECONDARY_GROUPS = []

function NavAccordion({ group }) {
  const location = useLocation()
  const isActiveGroup = group.items.some(i => location.pathname.startsWith(i.path))
  const [open, setOpen] = useState(isActiveGroup)

  return (
    <div className="card p-4">
      <button 
        type="button" 
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between text-left group"
      >
        <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--text-muted)] opacity-80 group-hover:text-[var(--text-main)] transition-colors">
          {group.title}
        </p>
        <ChevronDown className={`h-4 w-4 text-[var(--text-muted)] transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="space-y-2 mt-4 pt-4 border-t border-[var(--border-glass)]">
              {group.items.map(item => {
                const Icon = item.icon
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      clsx(
                        'flex items-center justify-between rounded-xl border px-4 py-3 text-sm font-medium transition-all duration-200',
                        isActive
                          ? 'border-cyan-200/50 bg-cyan-500/10 text-cyan-600 dark:text-cyan-400'
                          : 'border-transparent hover:bg-[var(--bg-glass-strong)] hover:border-[var(--border-glass)] text-[var(--text-main)]'
                      )
                    }
                  >
                    <span className="flex items-center gap-3">
                      <Icon className="h-4.5 w-4.5" />
                      {item.label}
                    </span>
                    <ChevronRight className="h-4 w-4 opacity-50" />
                  </NavLink>
                )
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

const AUTH_ROUTES = ['/login', '/register']

export default function Layout({ children }) {
  const location = useLocation()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const { resolvedTheme, toggleTheme } = useTheme()
  const { session, isAuthenticated } = useAuthSession()

  const handleLogout = () => {
    clearSession()
  }

  const isAuthPage = AUTH_ROUTES.includes(location.pathname)

  useEffect(() => {
    const t = setTimeout(() => setDrawerOpen(false), 0)
    return () => clearTimeout(t)
  }, [location.pathname])

  const { isConnected, isDegraded } = useApiStatus(30000, !isAuthPage)

  if (isAuthPage) {
    return (
      <div className="app-shell">
        <main className="app-container py-8 flex items-center justify-center min-h-screen">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial="initial"
              animate="animate"
              exit="exit"
              variants={authCardVariants}
              className="w-full max-w-md"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    )
  }

  return (
    <div className="app-shell relative">
      <header className="header-glass sticky top-0 z-50 rounded-none">
        <div className="app-container py-3">
          <div className="flex items-center justify-between gap-4">
            <div className="flex min-w-0 items-center gap-6">
              <NavLink to="/" className="group flex items-center gap-3">
                <div className="logo-mark relative flex h-12 w-12 items-center justify-center rounded-[18px] bg-gradient-to-br from-slate-800 to-slate-950 dark:from-white dark:to-slate-200 text-white dark:text-slate-900 shadow-lifted">
                  <span className="font-display text-2xl font-bold tracking-tight">M</span>
                  <span className="absolute -right-2 -top-2 rounded-full bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.6)] px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-[0.2em] text-white">
                    SOC
                  </span>
                </div>
                <div className="hidden sm:block">
                  <p className="font-display text-lg font-bold tracking-tight text-gradient">Mox Console</p>
                  <p className="text-xs text-[var(--text-muted)] font-medium">AI 安全攻防与治理工作台</p>
                </div>
              </NavLink>

              <div className="hidden xl:flex items-center gap-1 rounded-full border border-[var(--border-glass)] bg-[var(--bg-glass)] p-1.5 shadow-fine backdrop-blur-md">
                {PRIMARY_GROUPS.flatMap((group) => group.items).map((item) => {
                  const Icon = item.icon
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      className={({ isActive }) => clsx('nav-link', isActive && 'nav-link-active')}
                    >
                      <Icon className="h-4 w-4" />
                      {item.short}
                    </NavLink>
                  )
                })}
              </div>
            </div>

            <div className="hidden items-center gap-4 lg:flex">
              <StatusPill
                online={isConnected}
                onlineLabel={isDegraded ? 'API 降级' : 'API 已连接'}
                offlineLabel="API 离线"
              />
              <button
                type="button"
                onClick={toggleTheme}
                className="btn-secondary w-10 h-10 p-0 rounded-full flex items-center justify-center"
                aria-label="Toggle theme"
              >
                {resolvedTheme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </button>
              <NavLink to="/pricing" className="btn-secondary px-4">
                <CreditCard className="h-4 w-4" />
                <span>专业版</span>
              </NavLink>
              {isAuthenticated ? (
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 rounded-full border border-[var(--border-glass)] bg-[var(--bg-glass-strong)] px-3 py-1.5 backdrop-blur-md">
                    <div className="h-6 w-6 rounded-full bg-cyan-500/20 text-cyan-500 flex items-center justify-center border border-cyan-500/30">
                      <User className="h-3.5 w-3.5" />
                    </div>
                    <span className="text-xs font-bold text-[var(--text-main)] font-mono">{session?.user?.username || 'Admin'}</span>
                  </div>
                  <button type="button" onClick={handleLogout} className="btn-secondary px-4 hover:border-rose-500/50 hover:text-rose-500 hover:bg-rose-500/10 transition-colors" title="注销会话">
                    <LogOut className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <NavLink to="/login" className="btn-primary px-5">
                  <LogIn className="h-4 w-4" />
                  <span>登录</span>
                </NavLink>
              )}
            </div>

            <button
              type="button"
              onClick={() => setDrawerOpen((value) => !value)}
              className="btn-secondary w-10 h-10 p-0 rounded-full flex items-center justify-center lg:hidden"
              aria-label={drawerOpen ? '关闭导航菜单' : '打开导航菜单'}
              aria-expanded={drawerOpen}
            >
              {drawerOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
          </div>

          {SECONDARY_GROUPS.length > 0 && (
            <div className="mt-4 hidden items-center justify-between gap-4 lg:flex border-t border-[var(--border-glass)] pt-4">
              <div className="flex min-w-0 flex-wrap items-center gap-4">
              {SECONDARY_GROUPS.map((group) => (
                <div key={group.title} className="flex items-center gap-3">
                  <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--text-muted)] opacity-70">
                    {group.title}
                  </span>
                  <div className="flex flex-wrap items-center gap-1">
                    {group.items.map((item) => {
                      const Icon = item.icon
                      return (
                        <NavLink
                          key={item.path}
                          to={item.path}
                          className={({ isActive }) =>
                            clsx('subnav-link', isActive && 'subnav-link-active')
                          }
                        >
                          <Icon className="h-3.5 w-3.5" />
                          {item.label}
                        </NavLink>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
          )}
        </div>
      </header>

      <DemoBanner enabled={!isAuthPage} />

      <AnimatePresence>
        {drawerOpen && (
          <motion.div
            className="fixed inset-0 z-40 lg:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" onClick={() => setDrawerOpen(false)} />
            <motion.aside
              className="absolute right-0 top-0 h-full w-[min(92vw,380px)] border-l border-[var(--border-glass)] bg-[var(--bg-glass-strong)] backdrop-blur-xl p-6 shadow-card overflow-y-auto"
              initial="initial"
              animate="animate"
              exit="exit"
              variants={drawerVariants}
            >
              <div className="flex items-center justify-between mb-8">
                <div>
                  <p className="text-lg font-bold font-display text-[var(--text-main)]">导航中心</p>
                  <p className="text-xs text-[var(--text-muted)]">Mox Console 快捷访问</p>
                </div>
                <button type="button" onClick={() => setDrawerOpen(false)} className="btn-secondary w-8 h-8 p-0 rounded-full flex items-center justify-center">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-6">
                <div className="card p-4">
                  <div className="flex items-center justify-between mb-4">
                    <StatusPill
                      online={isConnected}
                      onlineLabel={isDegraded ? 'API 降级' : 'API 已连接'}
                      offlineLabel="API 离线"
                    />
                    <button
                      type="button"
                      onClick={toggleTheme}
                      className="btn-ghost w-8 h-8 p-0 rounded-full flex items-center justify-center"
                      aria-label="Toggle theme"
                    >
                      {resolvedTheme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                    </button>
                  </div>
                  <div className="glass-divider my-4" />
                  <div className="space-y-3">
                    <NavLink to="/pricing" className="btn-secondary w-full justify-between">
                      专业版方案
                      <ChevronRight className="h-4 w-4" />
                    </NavLink>
                    {isAuthenticated ? (
                      <button onClick={handleLogout} className="btn-secondary w-full justify-between text-rose-500 hover:bg-rose-500/10 hover:border-rose-500/30">
                        <span className="flex items-center gap-2"><LogOut className="h-4 w-4" /> 注销 ({session?.user?.username || 'Admin'})</span>
                      </button>
                    ) : (
                      <NavLink to="/login" className="btn-primary w-full justify-between">
                        登录账户
                        <ChevronRight className="h-4 w-4" />
                      </NavLink>
                    )}
                  </div>
                </div>

                {[...PRIMARY_GROUPS, ...SECONDARY_GROUPS].map((group) => (
                  <NavAccordion key={group.title} group={group} />
                ))}
              </div>
            </motion.aside>
          </motion.div>
        )}
      </AnimatePresence>

      <main className="app-container py-8 flex-1">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial="initial"
            animate="animate"
            exit="exit"
            variants={pageVariants}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>

      <TaskTray />

      <footer className="border-t border-[var(--border-glass)] bg-[var(--bg-glass)] backdrop-blur-md">
        <div className="app-container flex flex-col gap-2 py-6 text-xs text-[var(--text-muted)] sm:flex-row sm:items-center sm:justify-between">
          <p>
            <span className="font-semibold text-[var(--text-main)]">Mox Console</span> &copy; {new Date().getFullYear()} · 现代AI安全防护矩阵
          </p>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-2">
              <span className={`status-dot ${isConnected ? 'status-dot-online' : 'status-dot-demo'}`} />
              {isConnected ? '服务运行正常' : '演示 / 离线模式'}
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
}
