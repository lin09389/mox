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
      <div className="app-shell bg-white">
        <main className="app-container py-12">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, scale: 0.98, y: 8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 1.02, y: -8 }}
              transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    )
  }

  return (
    <div className="app-shell min-h-screen selection:bg-electric-50 selection:text-electric-900">
      <header className="sticky top-0 z-50 border-b border-white/40 bg-white/60 backdrop-blur-xl shadow-sm">
        <div className="app-container py-3">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-10">
              <NavLink to="/" className="group flex items-center gap-3">
                <div className="relative flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-graphite-900 to-graphite-800 text-white shadow-md transition-all duration-300 group-hover:scale-105 group-hover:shadow-graphite-900/20">
                  <div className="absolute inset-0 rounded-xl bg-white/10 opacity-0 transition-opacity group-hover:opacity-100" />
                  <span className="font-display text-lg font-bold">M</span>
                </div>
                <div>
                  <p className="font-display text-lg font-bold tracking-tight text-graphite-950 leading-none mb-1 group-hover:text-electric-700 transition-colors">Mox</p>
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-graphite-600">Security Console</p>
                </div>
              </NavLink>

              <nav className="hidden xl:flex items-center gap-1.5 bg-white/50 p-1.5 rounded-xl border border-white/60 shadow-inner backdrop-blur-sm">
                {PRIMARY_GROUPS.flatMap((group) => group.items).map((item) => {
                  const Icon = item.icon
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      className={({ isActive }) => 
                        clsx(
                          'relative flex items-center gap-2.5 px-4 py-2.5 text-sm font-medium transition-all duration-300 rounded-lg overflow-hidden',
                          isActive 
                            ? 'text-electric-700 shadow-sm' 
                            : 'text-graphite-500 hover:text-graphite-900 hover:bg-white/60'
                        )
                      }
                    >
                      {({ isActive }) => (
                        <>
                          {isActive && (
                            <motion.div
                              layoutId="nav-active-bg"
                              className="absolute inset-0 bg-white border border-electric-100/50"
                              initial={false}
                              transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                            />
                          )}
                          <Icon className={clsx("h-4 w-4 relative z-10 transition-transform duration-300", isActive && "scale-110")} />
                          <span className="relative z-10">{item.label}</span>
                        </>
                      )}
                    </NavLink>
                  )
                })}
              </nav>
            </div>

            <div className="hidden lg:flex items-center gap-5">
              <div className="h-8 w-px bg-graphite-200/60" />
              <NavLink to="/login" className="text-sm font-medium text-graphite-600 hover:text-electric-700 transition-colors">
                登录
              </NavLink>
              <NavLink to="/pricing" className="btn-primary !px-6 !py-2.5 !rounded-xl">
                <Sparkles className="h-4 w-4" />
                升级专业版
              </NavLink>
            </div>

            <div className="xl:hidden flex items-center gap-2">
              <button
                type="button"
                className="p-2.5 rounded-xl text-graphite-600 bg-white/50 border border-white/60 hover:bg-white transition-colors shadow-sm"
                onClick={() => setDrawerOpen(true)}
              >
                <Menu className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* 次级导航栏 */}
        <div className="hidden xl:block border-t border-white/40 bg-graphite-50/50">
          <div className="app-container py-2 flex items-center gap-8">
            <div className="text-xs font-bold uppercase tracking-wider text-graphite-500 flex items-center gap-2">
              {currentSecondary.title}
              <ChevronRight className="h-3 w-3 opacity-50" />
            </div>
            <nav className="flex items-center gap-1">
              {currentSecondary.items.map((item) => {
                const Icon = item.icon
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      clsx(
                        'flex items-center gap-2 px-3 py-1.5 text-[13px] font-medium rounded-lg transition-colors',
                        isActive
                          ? 'bg-white text-electric-700 shadow-sm border border-white/60'
                          : 'text-graphite-600 hover:bg-white/60 hover:text-graphite-900'
                      )
                    }
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {item.label}
                  </NavLink>
                )
              })}
            </nav>
          </div>
        </div>
      </header>

      {/* 移动端抽屉导航 */}
      <AnimatePresence>
        {drawerOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-[60] bg-graphite-900/40 backdrop-blur-sm"
              onClick={() => setDrawerOpen(false)}
            />
            <motion.div
              initial={{ x: '100%', borderTopLeftRadius: 30, borderBottomLeftRadius: 30 }}
              animate={{ x: 0, borderTopLeftRadius: 0, borderBottomLeftRadius: 0 }}
              exit={{ x: '100%', borderTopLeftRadius: 30, borderBottomLeftRadius: 30 }}
              transition={{ type: 'spring', bounce: 0, duration: 0.4 }}
              className="fixed inset-y-0 right-0 z-[70] w-full max-w-sm bg-white/95 backdrop-blur-xl border-l border-white/60 shadow-2xl flex flex-col overflow-hidden"
            >
              <div className="flex items-center justify-between p-5 border-b border-graphite-200/50">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-graphite-900 to-graphite-800 text-white shadow-md">
                    <span className="font-display text-sm font-bold">M</span>
                  </div>
                  <span className="font-display font-bold text-graphite-950">导航菜单</span>
                </div>
                <button
                  onClick={() => setDrawerOpen(false)}
                  className="rounded-full p-2 bg-graphite-100/80 text-graphite-600 hover:bg-graphite-200 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto px-5 py-6 no-scrollbar space-y-8">
                {/* 主导航模块 */}
                <div className="space-y-4">
                  <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-graphite-500">基础功能</p>
                  <nav className="grid grid-cols-2 gap-2">
                    {PRIMARY_GROUPS.flatMap(g => g.items).map(item => (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) => clsx(
                          "flex flex-col gap-3 p-4 rounded-xl border transition-all",
                          isActive 
                            ? "bg-electric-50 border-electric-200 text-electric-700 shadow-sm" 
                            : "bg-graphite-50/50 border-transparent text-graphite-700 hover:bg-white hover:border-graphite-200 hover:shadow-sm"
                        )}
                      >
                        <item.icon className="h-5 w-5" />
                        <span className="text-sm font-bold">{item.label}</span>
                      </NavLink>
                    ))}
                  </nav>
                </div>

                {/* 次级导航模块 */}
                {SECONDARY_GROUPS.map((group) => (
                  <div key={group.title} className="space-y-3">
                    <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-graphite-500">{group.title}</p>
                    <nav className="flex flex-col space-y-1">
                      {group.items.map((item) => (
                        <NavLink
                          key={item.path}
                          to={item.path}
                          className={({ isActive }) => clsx(
                            "flex items-center gap-3 px-4 py-3 rounded-xl transition-all",
                            isActive 
                              ? "bg-electric-50 text-electric-700 font-bold" 
                              : "text-graphite-600 font-medium hover:bg-graphite-50 hover:text-graphite-900"
                          )}
                        >
                          <item.icon className={clsx("h-4 w-4", isActive ? "text-electric-600" : "opacity-60")} />
                          {item.label}
                        </NavLink>
                      ))}
                    </nav>
                  </div>
                ))}
              </div>
              
              <div className="p-5 border-t border-graphite-200/50 bg-graphite-50/50 flex flex-col gap-3">
                <NavLink to="/login" className="btn-secondary w-full justify-center">登录账号</NavLink>
                <NavLink to="/pricing" className="btn-primary w-full justify-center">
                  <Sparkles className="h-4 w-4" /> 升级专业版
                </NavLink>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <main className="app-container py-10">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 15, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -15, scale: 0.98 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25, mass: 0.8 }}
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
