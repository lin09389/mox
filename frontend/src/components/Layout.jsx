import { NavLink, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useMemo, useState } from 'react'
import clsx from 'clsx'
import {
  Activity,
  BarChart3,
  BookOpen,
  ChevronRight,
  Clock3,
  Code2,
  CreditCard,
  FileText,
  History,
  LayoutDashboard,
  LogIn,
  Menu,
  Scale,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Sword,
  Target,
  Wand2,
  X,
  Zap,
} from 'lucide-react'
import { getApiStatus } from '../api'
import { StatusPill } from './ui/AppFrame'
import { useAutoRefresh } from '../hooks/useAutoRefresh'

const PRIMARY_GROUPS = [
  {
    title: '总览',
    items: [{ path: '/', label: '安全总览', short: '总览', icon: LayoutDashboard }],
  },
  {
    title: '攻防',
    items: [
      { path: '/attack', label: '攻击测试', short: '攻击', icon: Sword },
      { path: '/defense', label: '防御检测', short: '防御', icon: ShieldCheck },
      { path: '/benchmark', label: '基准评测', short: '评测', icon: BarChart3 },
      { path: '/history', label: '历史记录', short: '历史', icon: History },
    ],
  },
]

const SECONDARY_GROUPS = [
  {
    title: '高级模块',
    items: [
      { path: '/attack/advanced', label: '高级攻击', icon: Zap },
      { path: '/attack/novel', label: '新型攻击', icon: Wand2 },
      { path: '/attack/agent', label: 'Agent 攻击', icon: Sparkles },
      { path: '/attack/multimodal', label: '多模态攻击', icon: Target },
      { path: '/safety-card', label: '安全卡片', icon: Shield },
      { path: '/owasp', label: 'OWASP 测试', icon: ShieldAlert },
      { path: '/redteam', label: '红队演练', icon: Target },
    ],
  },
  {
    title: '治理与报告',
    items: [
      { path: '/code-security', label: '代码安全', icon: Code2 },
      { path: '/bias', label: '偏见检测', icon: Scale },
      { path: '/templates', label: '模板中心', icon: BookOpen },
      { path: '/reports', label: '评估报告', icon: FileText },
      { path: '/tasks', label: '任务中心', icon: Clock3 },
      { path: '/audit', label: '审计日志', icon: Activity },
    ],
  },
]

const AUTH_ROUTES = ['/login', '/register']

export default function Layout({ children }) {
  const location = useLocation()
  const [apiStatus, setApiStatus] = useState('unknown')
  const [drawerOpen, setDrawerOpen] = useState(false)

  const isAuthPage = AUTH_ROUTES.includes(location.pathname)
  const isPricingPage = location.pathname === '/pricing'

  const activeGroupTitle = useMemo(() => {
    const activeSecondary = SECONDARY_GROUPS.find((group) =>
      group.items.some((item) => location.pathname.startsWith(item.path))
    )
    return activeSecondary?.title ?? SECONDARY_GROUPS[0].title
  }, [location.pathname])

  const currentSecondary = useMemo(
    () => SECONDARY_GROUPS.find((group) => group.title === activeGroupTitle) ?? SECONDARY_GROUPS[0],
    [activeGroupTitle]
  )

  useEffect(() => {
    setDrawerOpen(false)
  }, [location.pathname])

  const syncApiStatus = () => setApiStatus(getApiStatus())

  useEffect(() => {
    syncApiStatus()
  }, [])

  useAutoRefresh(syncApiStatus, 30000, !isAuthPage)

  if (isAuthPage) {
    return (
      <div className="app-shell">
        <main className="app-container py-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <header className="sticky top-0 z-50 border-b border-white/70 bg-[#edf3fb]/85 backdrop-blur-xl">
        <div className="app-container py-3">
          <div className="flex items-center justify-between gap-4">
            <div className="flex min-w-0 items-center gap-4">
              <NavLink to="/" className="group flex items-center gap-3">
                <div className="relative flex h-12 w-12 items-center justify-center rounded-[18px] bg-graphite-950 text-white shadow-lifted">
                  <span className="font-display text-lg font-bold tracking-tight">M</span>
                  <span className="absolute -right-1 -top-1 rounded-full bg-electric-500 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-white">
                    SOC
                  </span>
                </div>
                <div className="hidden sm:block">
                  <p className="font-display text-lg font-bold tracking-tight text-graphite-950">Mox Console</p>
                  <p className="text-xs text-graphite-500">AI 安全攻防与治理工作台</p>
                </div>
              </NavLink>

              <div className="hidden xl:flex items-center gap-1 rounded-full border border-white/80 bg-white/65 p-1 shadow-fine">
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

            <div className="hidden items-center gap-3 lg:flex">
              <div className="rounded-full border border-white/80 bg-white/72 px-4 py-2 shadow-fine">
                <div className="flex items-center gap-2 text-xs text-graphite-500">
                  <span className="status-dot status-dot-online" />
                  监控周期 30s
                </div>
                <div className="mt-1 text-sm font-medium text-graphite-800">
                  {isPricingPage ? '当前浏览商业化页面' : currentSecondary.title}
                </div>
              </div>
              <StatusPill online={apiStatus === 'connected'} />
              <NavLink to="/pricing" className="btn-secondary px-4">
                <CreditCard className="h-4 w-4" />
                专业版
              </NavLink>
              <NavLink to="/login" className="btn-primary px-4">
                <LogIn className="h-4 w-4" />
                登录
              </NavLink>
            </div>

            <button
              type="button"
              onClick={() => setDrawerOpen((value) => !value)}
              className="btn-secondary px-3 lg:hidden"
              aria-label={drawerOpen ? '关闭导航菜单' : '打开导航菜单'}
              aria-expanded={drawerOpen}
            >
              {drawerOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
          </div>

          <div className="mt-3 hidden items-center justify-between gap-4 lg:flex">
            <div className="flex min-w-0 flex-wrap items-center gap-2">
              {SECONDARY_GROUPS.map((group) => (
                <div key={group.title} className="flex items-center gap-2">
                  <span className="text-[11px] font-semibold uppercase tracking-[0.22em] text-graphite-400">
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
        </div>
      </header>

      <AnimatePresence>
        {drawerOpen && (
          <motion.div
            className="fixed inset-0 z-40 lg:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div className="absolute inset-0 bg-graphite-950/35 backdrop-blur-sm" onClick={() => setDrawerOpen(false)} />
            <motion.aside
              className="absolute right-0 top-0 h-full w-[min(92vw,380px)] border-l border-white/70 bg-[#eff4fb]/96 p-5 shadow-modal"
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-graphite-950">导航中心</p>
                  <p className="text-xs text-graphite-500">快速切换模块与页面</p>
                </div>
                <button type="button" onClick={() => setDrawerOpen(false)} className="btn-ghost px-2.5 py-2">
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="mt-5 space-y-4">
                <div className="card p-4">
                  <StatusPill online={apiStatus === 'connected'} />
                  <div className="glass-divider my-4" />
                  <div className="space-y-3">
                    <NavLink to="/pricing" className="btn-secondary w-full justify-between">
                      专业版方案
                      <ChevronRight className="h-4 w-4" />
                    </NavLink>
                    <NavLink to="/login" className="btn-primary w-full justify-between">
                      登录账户
                      <ChevronRight className="h-4 w-4" />
                    </NavLink>
                  </div>
                </div>

                {[...PRIMARY_GROUPS, ...SECONDARY_GROUPS].map((group) => (
                  <div key={group.title} className="card p-4">
                    <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.22em] text-graphite-400">
                      {group.title}
                    </p>
                    <div className="space-y-2">
                      {group.items.map((item) => {
                        const Icon = item.icon
                        return (
                          <NavLink
                            key={item.path}
                            to={item.path}
                            className={({ isActive }) =>
                              clsx(
                                'flex items-center justify-between rounded-2xl border px-3 py-3 text-sm font-medium transition-all duration-200',
                                isActive
                                  ? 'border-electric-200 bg-electric-50 text-electric-700'
                                  : 'border-graphite-200/70 bg-white/75 text-graphite-700'
                              )
                            }
                          >
                            <span className="flex items-center gap-3">
                              <Icon className="h-4 w-4" />
                              {item.label}
                            </span>
                            <ChevronRight className="h-4 w-4 text-graphite-400" />
                          </NavLink>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </motion.aside>
          </motion.div>
        )}
      </AnimatePresence>

      <main className="app-container py-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>

      <footer className="border-t border-white/70 bg-white/55">
        <div className="app-container flex flex-col gap-2 py-5 text-xs text-graphite-500 sm:flex-row sm:items-center sm:justify-between">
          <p>
            <span className="font-semibold text-graphite-800">Mox Console</span> · 面向大模型安全的专业监控台
          </p>
          <p>建议在真实评测前确认后端服务状态与模型配置。</p>
        </div>
      </footer>
    </div>
  )
}
