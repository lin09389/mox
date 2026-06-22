import { motion } from 'framer-motion'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, Lock, Mail, User, UserPlus, Shield } from 'lucide-react'
import toast from 'react-hot-toast'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRegister } from '../hooks/queries'

const registerSchema = z.object({
  username: z.string().min(3, '操作员别名至少3个字符'),
  email: z.string().email('必须是有效的邮箱地址'),
  password: z.string().min(8, '验证口令至少8个字符'),
  agree: z.literal(true, {
    errorMap: () => ({ message: '必须同意服务协议与隐私策略' }),
  }),
})

import { containerVariants, itemVariants } from '../utils/animations'

export default function RegisterPage() {
  const navigate = useNavigate()
  const registerMutation = useRegister()

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(registerSchema),
    defaultValues: { username: '', email: '', password: '', agree: false }
  })

  const onSubmit = async (data) => {
    try {
      await registerMutation.mutateAsync({
        username: data.username,
        email: data.email,
        password: data.password,
      })
      toast.success('注册成功，工作区已初始化，请登录。')
      navigate('/login')
    } catch (error) {
      const detail = error?.response?.data?.detail || error?.response?.data?.message
      toast.error(detail || '注册失败，请稍后重试。')
    }
  }

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="page-shell min-h-[calc(100dvh-4rem)] justify-center py-6 pb-8 sm:min-h-[calc(100vh-7rem)] sm:py-10">
      <section className="grid gap-6 lg:gap-8 lg:grid-cols-[1.1fr_480px] lg:items-center max-w-6xl mx-auto w-full">
        <motion.div variants={itemVariants} className="hidden lg:block space-y-8 pr-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest text-cyan-500">
            <Shield className="h-3.5 w-3.5" />
            全新工作区准入
          </div>
          <h1 className="font-display text-4xl font-bold tracking-tight text-[var(--text-main)] sm:text-5xl leading-[1.15]">
            创建并初始化你的 <br className="hidden sm:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">大模型安全评测账户</span>
          </h1>
          <p className="text-base font-medium text-[var(--text-muted)] max-w-lg leading-relaxed">
            从对抗攻击挂载、防御策略评估到沙盒推演报告，所有的安全生命周期模块已无缝集成。在此构建专属安全画像。
          </p>
          
          <div className="grid gap-4 mt-8">
            <div className="flex items-start gap-4 p-4 rounded-xl border border-[var(--border-glass)] bg-[var(--bg-glass)] hover:bg-[var(--bg-glass-strong)] transition-colors">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-500 font-mono font-bold text-sm">1</div>
              <div>
                <h4 className="text-sm font-bold text-[var(--text-main)]">统一授权系统</h4>
                <p className="mt-1 text-xs font-medium text-[var(--text-muted)]">通过此门户完成安全审计与工作区绑定认证。</p>
              </div>
            </div>
            <div className="flex items-start gap-4 p-4 rounded-xl border border-[var(--border-glass)] bg-[var(--bg-glass)] hover:bg-[var(--bg-glass-strong)] transition-colors">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-500 font-mono font-bold text-sm">2</div>
              <div>
                <h4 className="text-sm font-bold text-[var(--text-main)]">无缝体验交接</h4>
                <p className="mt-1 text-xs font-medium text-[var(--text-muted)]">账户就绪后，系统将自动配置大屏总线环境并引导至登录节点。</p>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.section
          variants={itemVariants}
          className="card p-5 sm:p-8 bg-[var(--bg-glass-strong)] border-[var(--border-glass)] shadow-[0_20px_50px_rgba(0,0,0,0.5)] mx-auto w-full max-w-[480px] relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 to-blue-500 opacity-80"></div>
          
          <div className="mb-6 sm:mb-8 flex items-center gap-4">
            <div className="rounded-xl bg-cyan-500/10 border border-cyan-500/30 p-3 text-cyan-500 shadow-[inset_0_0_15px_rgba(6,182,212,0.2)]">
              <UserPlus className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-bold font-display text-[var(--text-main)]">新账户注册</h2>
              <p className="mt-1 text-xs font-medium text-[var(--text-muted)]">接入红蓝对抗演练平台。</p>
            </div>
          </div>

          <p className="mb-4 text-sm text-[var(--text-muted)] lg:hidden">
            创建账户后即可使用攻击、防御与评估模块。
          </p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 sm:space-y-5">
            <div>
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest block mb-2" htmlFor="username">操作员别名</label>
              <div className="relative">
                <User className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" />
                <input id="username" autoComplete="username" {...register('username')} className={`input-field pl-11 py-3.5 text-base min-h-[48px] ${errors.username ? 'border-rose-500/50' : ''}`} placeholder="mox_operator_01" />
              </div>
              {errors.username && <p className="mt-1 text-xs text-rose-500">{errors.username.message}</p>}
            </div>

            <div>
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest block mb-2" htmlFor="register-email">通讯邮箱地址</label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" />
                <input id="register-email" type="email" autoComplete="email" {...register('email')} className={`input-field pl-11 py-3.5 text-base min-h-[48px] ${errors.email ? 'border-rose-500/50' : ''}`} placeholder="sysadmin@example.com" />
              </div>
              {errors.email && <p className="mt-1 text-xs text-rose-500">{errors.email.message}</p>}
            </div>

            <div>
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest block mb-2" htmlFor="register-password">安全验证口令</label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" />
                <input id="register-password" type="password" autoComplete="new-password" {...register('password')} className={`input-field pl-11 py-3.5 text-base min-h-[48px] ${errors.password ? 'border-rose-500/50' : ''}`} placeholder="包含数字及字母组合的强口令" />
              </div>
              {errors.password && <p className="mt-1 text-xs text-rose-500">{errors.password.message}</p>}
            </div>

            <label className="flex items-start gap-3 rounded-xl border border-[var(--border-glass)] bg-[var(--bg-glass)] px-4 py-3 mt-6 hover:border-cyan-500/30 transition-colors cursor-pointer">
              <input type="checkbox" {...register('agree')} className="mt-0.5 rounded border-[var(--border-glass-strong)] bg-transparent text-cyan-500 focus:ring-cyan-500/20" />
              <div className="flex flex-col">
                <span className="text-xs font-medium text-[var(--text-muted)] leading-relaxed">
                  我已授权并接受平台
                  <a href="#" className="mx-1 font-bold text-cyan-500 hover:text-cyan-400 transition-colors">终端服务许可协议 (EULA)</a>
                  与
                  <a href="#" className="ml-1 font-bold text-cyan-500 hover:text-cyan-400 transition-colors">隐私保护策略</a>。
                </span>
                {errors.agree && <span className="text-xs text-rose-500 mt-1">{errors.agree.message}</span>}
              </div>
            </label>

            <button type="submit" disabled={isSubmitting || registerMutation.isPending} className="btn-primary mt-6 sm:mt-8 w-full justify-center py-3.5 sm:py-4 min-h-[48px] bg-cyan-500 hover:bg-cyan-600 border-cyan-500 text-white font-bold text-base shadow-[0_0_20px_rgba(6,182,212,0.3)] disabled:opacity-70 disabled:shadow-none">
              {(isSubmitting || registerMutation.isPending) ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-3" />
                  正在配置工作区资源...
                </>
              ) : (
                <>
                  建立档案并创建账户
                  <ArrowRight className="h-5 w-5 ml-2" />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-[var(--border-glass)] text-center">
            <p className="text-sm font-medium text-[var(--text-muted)]">
              系统内已有活动账户？
              <Link to="/login" className="ml-2 font-bold text-cyan-500 hover:text-cyan-400 transition-colors">
                前往认证中心
              </Link>
            </p>
          </div>
        </motion.section>
      </section>
    </motion.div>
  )
}
