import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, Lock, LogOut, Mail, ShieldCheck, Fingerprint } from 'lucide-react'
import toast from 'react-hot-toast'
import { clearSession, DEMO_MODE_ENABLED, useAuthSession, persistSession } from '../auth'
import { useLogin } from '../hooks/queries'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const loginSchema = z.object({
  username: z.string().min(1, '操作员别名不能为空'),
  password: z.string().min(1, '授权访问口令不能为空'),
})

import { containerVariants, itemVariants } from '../utils/animations'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { session, isAuthenticated } = useAuthSession()
  const loginMutation = useLogin()

  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '' }
  })

  const nextPath = location.state?.from?.pathname || '/'
  const searchParams = new URLSearchParams(location.search)
  const expiredReason = searchParams.get('reason') === 'expired'

  const onSubmit = async (data) => {
    try {
      const payload = await loginMutation.mutateAsync({
        username: data.username.trim(),
        password: data.password,
      })
      persistSession(payload)
      toast.success('安全令牌验证通过，正在挂载系统总线。')
      navigate(nextPath, { replace: true })
    } catch (error) {
      const message = error.response?.data?.message || error.response?.data?.detail || '身份识别与访问管理 (IAM) 拒绝请求。'
      toast.error(message)
    }
  }

  const handleLogout = () => {
    clearSession()
    toast.success('安全隧道已断开，会话缓存已清理。')
  }

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="flex min-h-[calc(100vh-5rem)] items-center justify-center px-4 py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/5 blur-[120px] rounded-full pointer-events-none"></div>
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-blue-500/5 blur-[120px] rounded-[100%] pointer-events-none transform -rotate-45"></div>

      <motion.div variants={itemVariants} className="w-full max-w-md relative z-10">
        <div className="text-center mb-10">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="relative mx-auto flex h-20 w-20 items-center justify-center rounded-2xl bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] shadow-[0_0_30px_rgba(6,182,212,0.15)] mb-6"
          >
            <ShieldCheck className="h-10 w-10 text-cyan-500" />
            <motion.div
              className="absolute -bottom-1 -right-1 h-5 w-5 rounded-full border-2 border-[var(--bg-main)] bg-cyan-500"
              animate={{ scale: [1, 1.2, 1], boxShadow: ['0 0 0 0 rgba(6,182,212,0.7)', '0 0 0 10px rgba(6,182,212,0)', '0 0 0 0 rgba(6,182,212,0)'] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          </motion.div>
          <h1 className="font-display text-4xl font-bold tracking-tight text-[var(--text-main)] mb-3">
            Mox 身份网关认证
          </h1>
          <p className="text-sm font-medium text-[var(--text-muted)]">请输入授权密钥凭据以挂载您的安全评测工作区节点。</p>
        </div>

        {(expiredReason || DEMO_MODE_ENABLED) && (
          <motion.div variants={itemVariants} className="mb-8 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm font-medium text-amber-500 flex items-start gap-3 shadow-[inset_0_0_15px_rgba(245,158,11,0.05)]">
            <Fingerprint className="h-5 w-5 shrink-0 mt-0.5" />
            <p>
              {expiredReason
                ? '本地安全令牌（Token）生存周期已到期，系统强制注销会话。请重新签署身份凭据。'
                : '检测到前端运行在演示预演（Demo）环境。未联通后端引擎的接口请求将降级由本地沙箱代理拦截并返回静态模拟数据。'}
            </p>
          </motion.div>
        )}

        <motion.div variants={itemVariants} className="card p-8 bg-[var(--bg-glass-strong)] border-[var(--border-glass)] shadow-[0_20px_50px_rgba(0,0,0,0.3)] relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-500 to-transparent opacity-60"></div>
          
          {isAuthenticated ? (
            <div className="space-y-6 text-center py-4">
              <div className="flex justify-center mb-4">
                <div className="w-16 h-16 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
                  <Fingerprint className="w-8 h-8 text-cyan-500" />
                </div>
              </div>
              <div>
                <p className="text-lg font-bold text-[var(--text-main)] mb-1">隧道已连接</p>
                <p className="text-sm font-medium text-[var(--text-muted)]">
                  系统已与操作员 <span className="text-cyan-500 font-mono">{session?.user?.username || session?.user?.email || 'Authenticated User'}</span> 绑定。
                </p>
              </div>
              <div className="flex flex-col gap-3 pt-4">
                <button type="button" className="btn-primary w-full justify-center py-3.5 bg-cyan-500 hover:bg-cyan-600 border-cyan-500 text-white font-bold shadow-[0_0_20px_rgba(6,182,212,0.3)]" onClick={() => navigate('/', { replace: true })}>
                  进入控制台主界面
                  <ArrowRight className="h-4 w-4 ml-2" />
                </button>
                <button type="button" className="btn-secondary w-full justify-center py-3.5 bg-[var(--bg-glass)] hover:bg-[var(--bg-glass-strong)] border-[var(--border-glass-strong)] text-[var(--text-main)]" onClick={handleLogout}>
                  <LogOut className="h-4 w-4 mr-2" />
                  断开挂载并退出系统
                </button>
              </div>
            </div>
          ) : (
            <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
              <div>
                <label htmlFor="username" className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest block mb-2">
                  操作员别名 / 邮箱标识
                </label>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4">
                    <Mail className="h-4 w-4 text-[var(--text-muted)]" />
                  </div>
                  <input
                    id="username"
                    type="text"
                    autoComplete="username"
                    {...register('username')}
                    className={`input-field pl-11 py-3 text-base font-mono bg-[var(--bg-main)]/50 focus:bg-transparent ${errors.username ? 'border-rose-500/50 focus:border-rose-500/50' : ''}`}
                    placeholder="operator_sys_admin"
                  />
                </div>
                {errors.username && <p className="mt-1 text-xs text-rose-500">{errors.username.message}</p>}
              </div>

              <div>
                <label htmlFor="password" className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest block mb-2">
                  授权访问口令
                </label>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4">
                    <Lock className="h-4 w-4 text-[var(--text-muted)]" />
                  </div>
                  <input
                    id="password"
                    type="password"
                    autoComplete="current-password"
                    {...register('password')}
                    className={`input-field pl-11 py-3 text-base font-mono tracking-widest bg-[var(--bg-main)]/50 focus:bg-transparent ${errors.password ? 'border-rose-500/50 focus:border-rose-500/50' : ''}`}
                    placeholder="••••••••••••"
                  />
                </div>
                {errors.password && <p className="mt-1 text-xs text-rose-500">{errors.password.message}</p>}
              </div>

              <button
                type="submit"
                disabled={loginMutation.isPending}
                className="w-full btn-primary justify-center py-4 text-base bg-cyan-500 hover:bg-cyan-600 border-cyan-500 text-white font-bold shadow-[0_0_20px_rgba(6,182,212,0.3)] disabled:opacity-70 disabled:shadow-none transition-all mt-4"
              >
                {loginMutation.isPending ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-3" />
                    协商鉴权隧道中...
                  </>
                ) : (
                  <>
                    签发访问令牌并挂载 (Sign In)
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </>
                )}
              </button>
            </form>
          )}

          {!isAuthenticated && (
            <div className="mt-8 pt-6 border-t border-[var(--border-glass)]">
              <div className="text-center">
                <p className="text-sm font-medium text-[var(--text-muted)] mb-3">系统暂未录入您的数字指纹？</p>
                <Link
                  to="/register"
                  className="inline-flex items-center justify-center gap-2 font-bold text-cyan-500 hover:text-cyan-400 transition-colors bg-cyan-500/10 px-4 py-2 rounded-lg"
                >
                  前往申请分配新工作区 <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>
          )}
        </motion.div>
      </motion.div>
    </motion.div>
  )
}
