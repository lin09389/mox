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
  X
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

const mainNavItems = navItems.slice(0, 8)
const moreNavItems = navItems.slice(8)

export default function Layout({ children }) {
  const [apiStatus, setApiStatus] = useState('unknown')
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [showMoreNav, setShowMoreNav] = useState(false)
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
  }, [location])

  return (
    <div className="min-h-screen flex flex-col">
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <motion.div 
          className="absolute -top-52 -right-52 w-96 h-96 bg-primary-200/40 rounded-full blur-3xl"
          animate={{ 
            scale: [1, 1.1, 1],
            opacity: [0.3, 0.5, 0.3]
          }}
          transition={{ duration: 8, repeat: Infinity }}
        />
        <motion.div 
          className="absolute -bottom-52 -left-52 w-96 h-96 bg-secondary-200/40 rounded-full blur-3xl"
          animate={{ 
            scale: [1, 1.15, 1],
            opacity: [0.3, 0.45, 0.3]
          }}
          transition={{ duration: 10, repeat: Infinity, delay: 1 }}
        />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] bg-gradient-to-br from-primary-100/20 to-secondary-100/20 rounded-full blur-3xl" />
      </div>

      <header className="sticky top-0 z-50 glass-strong border-b border-dark-200/50 backdrop-blur-3xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <motion.div 
              className="flex items-center gap-4"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="relative">
                <div className="w-12 h-12 bg-gradient-to-br from-primary-500 via-secondary-500 to-accent-500 rounded-2xl flex items-center justify-center shadow-glow-primary animate-float">
                  <span className="text-2xl text-white font-extrabold tracking-tight">M</span>
                </div>
                <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-success-500 rounded-full border-2 border-white shadow-sm" />
              </div>
              <div>
                <h1 className="text-2xl font-extrabold text-dark-900 tracking-tight">
                  <span className="text-gradient">Mox</span>
                </h1>
                <p className="text-sm text-dark-500 -mt-0.5 font-medium">大模型对抗攻防平台</p>
              </div>
            </motion.div>

            <div className="flex items-center gap-4">
              <div className={`hidden md:flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold transition-all duration-300 ${
                apiStatus === 'connected' 
                  ? 'bg-success-100 text-success-700 border border-success-200/70' 
                  : 'bg-warning-100 text-warning-700 border border-warning-200/70'
              }`}>
                <div className={`w-2.5 h-2.5 rounded-full animate-pulse ${
                  apiStatus === 'connected' ? 'bg-success-500' : 'bg-warning-500'
                }`} />
                {apiStatus === 'connected' ? 'API 已连接' : '演示模式'}
              </div>

              <nav className="hidden lg:flex items-center gap-1">
                {mainNavItems.map((item, idx) => {
                  const Icon = item.icon
                  return (
                    <motion.div
                      key={item.path}
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.05, duration: 0.4 }}
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
                        <Icon className="w-4.5 h-4.5" />
                        <span className="hidden xl:inline">{item.label}</span>
                      </NavLink>
                    </motion.div>
                  )
                })}
                
                <motion.button
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: mainNavItems.length * 0.05 }}
                  onClick={() => setShowMoreNav(!showMoreNav)}
                  className="nav-link relative"
                >
                  <span className="hidden xl:inline">更多</span>
                  <svg 
                    className={clsx("w-4 h-4 transition-transform duration-200", showMoreNav && "rotate-180")}
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </motion.button>
              </nav>

              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="lg:hidden p-2 rounded-xl hover:bg-dark-100/70 transition-colors"
              >
                {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>
        </div>

        <AnimatePresence>
          {showMoreNav && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden border-t border-dark-200/30"
            >
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                <div className="flex flex-wrap gap-2">
                  {moreNavItems.map((item) => {
                    const Icon = item.icon
                    return (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                          clsx(
                            'nav-link text-sm',
                            isActive && 'nav-link-active'
                          )
                        }
                      >
                        <Icon className="w-4 h-4" />
                        {item.label}
                      </NavLink>
                    )
                  })}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, x: '100%' }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: '100%' }}
            className="fixed inset-0 z-40 lg:hidden"
          >
            <div 
              className="absolute inset-0 bg-dark-900/30 backdrop-blur-sm"
              onClick={() => setIsMobileMenuOpen(false)}
            />
            <div className="absolute right-0 top-0 bottom-0 w-80 bg-white/95 backdrop-blur-2xl border-l border-dark-200/50 p-6 overflow-y-auto">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-dark-900">导航</h2>
                <button
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="p-2 rounded-xl hover:bg-dark-100/70 transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
              <div className="space-y-2">
                {navItems.map((item) => {
                  const Icon = item.icon
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      className={({ isActive }) =>
                        clsx(
                          'nav-link w-full',
                          isActive && 'nav-link-active'
                        )
                      }
                    >
                      <Icon className="w-5 h-5" />
                      {item.label}
                    </NavLink>
                  )
                })}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          key={location.pathname}
        >
          {children}
        </motion.div>
      </main>

      <footer className="border-t border-dark-200/40 mt-auto glass">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-3 text-sm">
            <p className="text-dark-600 font-medium">
              <span className="text-gradient font-bold">Mox</span> - 大模型对抗攻防平台
            </p>
            <p className="text-dark-400">仅供安全研究使用</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
