import { NavLink, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'
import { useState, useEffect } from 'react'
import { getApiStatus } from '../api'
import {
  LayoutDashboard,
  ShieldAlert,
  ShieldCheck,
  BarChart3,
  Clock,
  Code2,
  Scale,
  Zap,
  Target,
  FileText,
  ListChecks,
  History,
  Menu,
  X,
  ChevronDown,
  Loader
} from 'lucide-react'

const navItems = [
  { path: '/', label: '安全仪表盘', icon: LayoutDashboard },
  { path: '/attack', label: '攻击测试', icon: ShieldAlert },
  { path: '/attack/advanced', label: '高级攻击', icon: Zap },
  { path: '/attack/novel', label: '新型攻击', icon: Target },
  { path: '/defense', label: '防御检测', icon: ShieldCheck },
  { path: '/owasp', label: 'OWASP测试', icon: ShieldAlert },
  { path: '/redteam', label: '红队演练', icon: Target },
  { path: '/benchmark', label: '基准测试', icon: BarChart3 },
  { path: '/code-security', label: '代码安全', icon: Code2 },
  { path: '/bias', label: '偏见检测', icon: Scale },
  { path: '/templates', label: '模板库', icon: FileText },
  { path: '/reports', label: '评估报告', icon: ListChecks },
  { path: '/tasks', label: '任务中心', icon: Clock },
  { path: '/audit', label: '审计日志', icon: History },
  { path: '/history', label: '历史记录', icon: History },
]

const mainNavItems = navItems.slice(0, 6)
const secondaryNavItems = navItems.slice(6, 12)
const moreNavItems = navItems.slice(12)

export default function Layout({ children }) {
  const [apiStatus, setApiStatus] = useState('unknown')
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [showMoreNav, setShowMoreNav] = useState(false)
  const [showSecondaryNav, setShowSecondaryNav] = useState(false)
  const location = useLocation()

  useEffect(() => {
    const checkStatus = () => {
      setApiStatus(getApiStatus())
    }
    checkStatus()
    const interval = setInterval(checkStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    setIsMobileMenuOpen(false)
    setShowMoreNav(false)
    setShowSecondaryNav(false)
  }, [location])

  return (
    <div className="min-h-screen flex flex-col bg-graphite-50/30">
      {/* 顶部导航 */}
      <header className="sticky top-0 z-50 bg-white/95 border-b border-graphite-200/60 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <motion.div
              className="flex items-center gap-3"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            >
              <div className="relative">
                <div className="w-9 h-9 bg-graphite-900 rounded-md flex items-center justify-center shadow-lifted">
                  <span className="text-lg text-white font-bold font-display tracking-tight">M</span>
                </div>
                <motion.div
                  className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-neon-500 rounded-full border-2 border-white"
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              </div>
              <div className="hidden sm:block">
                <h1 className="text-lg font-bold font-display text-graphite-900 tracking-tight">
                  Mox
                </h1>
                <p className="text-[11px] text-graphite-500 -mt-0.5">LLM 对抗攻防平台</p>
              </div>
            </motion.div>

            {/* 状态 + 导航 */}
            <div className="flex items-center gap-3">
              {/* API 状态 */}
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className={clsx(
                  'hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200',
                  apiStatus === 'connected'
                    ? 'bg-neon-50 text-neon-700 border border-neon-200/70'
                    : 'bg-amber-50 text-amber-700 border border-amber-200/70'
                )}
              >
                {apiStatus === 'connected' ? (
                  <span className="w-1.5 h-1.5 bg-neon-500 rounded-full animate-pulse" />
                ) : (
                  <Loader className="w-3 h-3 animate-spin" />
                )}
                {apiStatus === 'connected' ? 'API 已连接' : '演示模式'}
              </motion.div>

              {/* 桌面端导航 */}
              <nav className="hidden lg:flex items-center gap-0.5">
                {mainNavItems.map((item, idx) => {
                  const Icon = item.icon
                  return (
                    <motion.div
                      key={item.path}
                      initial={{ opacity: 0, y: -8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{
                        delay: idx * 0.04,
                        duration: 0.35,
                        ease: [0.16, 1, 0.3, 1]
                      }}
                    >
                      <NavLink
                        to={item.path}
                        className={({ isActive }) =>
                          clsx(
                            'nav-link',
                            isActive && 'nav-link-active'
                          )
                        }
                      >
                        <Icon className="w-4 h-4" />
                        <span className="hidden xl:inline">{item.label}</span>
                      </NavLink>
                    </motion.div>
                  )
                })}

                {/* 更多下拉 */}
                <motion.div
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{
                    delay: mainNavItems.length * 0.04,
                    duration: 0.35,
                    ease: [0.16, 1, 0.3, 1]
                  }}
                  className="relative"
                >
                  <button
                    onClick={() => setShowMoreNav(!showMoreNav)}
                    className="nav-link"
                  >
                    <span className="hidden xl:inline">更多</span>
                    <ChevronDown className={clsx(
                      "w-4 h-4 transition-transform duration-200",
                      showMoreNav && "rotate-180"
                    )} />
                  </button>

                  <AnimatePresence>
                    {showMoreNav && (
                      <motion.div
                        initial={{ opacity: 0, y: -8, scale: 0.96 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -8, scale: 0.96 }}
                        transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
                        className="absolute top-full right-0 mt-2 w-52 bg-white rounded-lg border border-graphite-200/60 shadow-modal p-1.5"
                      >
                        {secondaryNavItems.map((item) => {
                          const Icon = item.icon
                          return (
                            <NavLink
                              key={item.path}
                              to={item.path}
                              className={({ isActive }) =>
                                clsx(
                                  'flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-all duration-150',
                                  isActive
                                    ? 'bg-electric-50/80 text-electric-700'
                                    : 'text-graphite-600 hover:text-graphite-900 hover:bg-graphite-100/60'
                                )
                              }
                            >
                              <Icon className="w-4 h-4" />
                              {item.label}
                            </NavLink>
                          )
                        })}
                        <div className="h-px bg-graphite-200/60 my-1.5" />
                        {moreNavItems.map((item) => {
                          const Icon = item.icon
                          return (
                            <NavLink
                              key={item.path}
                              to={item.path}
                              className={({ isActive }) =>
                                clsx(
                                  'flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-all duration-150',
                                  isActive
                                    ? 'bg-electric-50/80 text-electric-700'
                                    : 'text-graphite-600 hover:text-graphite-900 hover:bg-graphite-100/60'
                                )
                              }
                            >
                              <Icon className="w-4 h-4" />
                              {item.label}
                            </NavLink>
                          )
                        })}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              </nav>

              {/* 移动端菜单按钮 */}
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="lg:hidden p-2 rounded-md hover:bg-graphite-100/70 transition-colors"
              >
                {isMobileMenuOpen ? <X className="w-5 h-5 text-graphite-700" /> : <Menu className="w-5 h-5 text-graphite-700" />}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* 移动端菜单 */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 lg:hidden"
          >
            <div
              className="absolute inset-0 bg-graphite-900/20 backdrop-blur-sm"
              onClick={() => setIsMobileMenuOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, x: '100%' }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: '100%' }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="absolute right-0 top-0 bottom-0 w-72 bg-white shadow-modal"
            >
              <div className="p-5 border-b border-graphite-200/60">
                <div className="flex justify-between items-center">
                  <h2 className="text-base font-semibold text-graphite-900">导航菜单</h2>
                  <button
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="p-1.5 rounded-md hover:bg-graphite-100/70 transition-colors"
                  >
                    <X className="w-5 h-5 text-graphite-500" />
                  </button>
                </div>
              </div>
              <div className="p-3 overflow-y-auto h-[calc(100vh-73px)]">
                <div className="space-y-0.5">
                  {navItems.map((item, idx) => {
                    const Icon = item.icon
                    return (
                      <motion.div
                        key={item.path}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.03 }}
                      >
                        <NavLink
                          to={item.path}
                          className={({ isActive }) =>
                            clsx(
                              'flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-all duration-150',
                              isActive
                                ? 'bg-electric-50/80 text-electric-700 border border-electric-200/70'
                                : 'text-graphite-600 hover:text-graphite-900 hover:bg-graphite-100/60'
                            )
                          }
                        >
                          <Icon className="w-4.5 h-4.5" />
                          {item.label}
                        </NavLink>
                      </motion.div>
                    )
                  })}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 主内容区 */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full">
        <AnimatePresence mode="wait">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            key={location.pathname}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* 页脚 */}
      <footer className="border-t border-graphite-200/60 bg-white/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-2 text-xs">
            <p className="text-graphite-500">
              <span className="font-semibold text-graphite-700">Mox</span> — LLM 对抗攻防平台
            </p>
            <p className="text-graphite-400">仅供安全研究使用</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
