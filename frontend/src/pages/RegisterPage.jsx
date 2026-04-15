import { useState } from 'react'
import { motion } from 'framer-motion'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, Lock, Mail, User, UserPlus } from 'lucide-react'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = (event) => {
    event.preventDefault()
    setIsLoading(true)
    window.setTimeout(() => {
      setIsLoading(false)
      toast.success('注册成功，请继续登录。')
      navigate('/login')
    }, 800)
  }

  return (
    <div className="page-shell min-h-[calc(100vh-7rem)] justify-center">
      <section className="grid gap-6 lg:grid-cols-[1.05fr_500px] lg:items-center">
        <div className="hero-panel">
          <div className="relative z-10 max-w-xl space-y-5">
            <span className="badge badge-success">NEW WORKSPACE</span>
            <h1 className="font-display text-4xl font-bold tracking-tight text-graphite-950 sm:text-5xl">
              创建你的安全评测账户
            </h1>
            <p className="text-base text-graphite-600">
              从攻击测试、历史记录到治理报告，新的界面已经统一到同一套监控台语言里，首次使用也能快速上手。
            </p>
            <div className="space-y-3 text-sm text-graphite-600">
              <p>1. 账号创建后会自动跳转到登录页。</p>
              <p>2. 本轮前端已统一中文文案和表单交互，不再出现乱码提示。</p>
              <p>3. 后续可在工作台中切换攻击、防御、评测和报告模块。</p>
            </div>
          </div>
        </div>

        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="card card-glow mx-auto w-full max-w-[500px]"
        >
          <div className="mb-6 flex items-center gap-3">
            <div className="rounded-[18px] bg-electric-600 p-3 text-white shadow-glow-electric">
              <UserPlus className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-graphite-950">创建账户</h2>
              <p className="text-sm text-graphite-500">开始你的 AI 安全评测旅程。</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label" htmlFor="username">用户名</label>
              <div className="relative">
                <User className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-graphite-600" />
                <input id="username" required className="input-field pl-11" placeholder="mox_operator" />
              </div>
            </div>

            <div>
              <label className="label" htmlFor="register-email">邮箱地址</label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-graphite-600" />
                <input id="register-email" type="email" required className="input-field pl-11" placeholder="you@example.com" />
              </div>
            </div>

            <div>
              <label className="label" htmlFor="register-password">密码</label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-graphite-600" />
                <input id="register-password" type="password" required className="input-field pl-11" placeholder="至少 8 位，建议包含字母和数字" />
              </div>
            </div>

            <label className="flex items-start gap-3 rounded-[18px] border border-graphite-200/70 bg-graphite-50/70 px-4 py-3 text-sm text-graphite-600">
              <input type="checkbox" required className="mt-0.5 rounded border-graphite-300 text-electric-700" />
              <span>
                我已阅读并同意
                <a href="#" className="mx-1 text-electric-700 hover:text-electric-800">服务条款</a>
                和
                <a href="#" className="ml-1 text-electric-700 hover:text-electric-800">隐私政策</a>。
              </span>
            </label>

            <button type="submit" disabled={isLoading} className="btn-primary w-full justify-center py-3">
              {isLoading ? (
                <>
                  <div className="spinner" />
                  正在创建账户
                </>
              ) : (
                <>
                  创建账户
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          <div className="glass-divider my-6" />

          <p className="text-center text-sm text-graphite-500">
            已有账户？
            <Link to="/login" className="ml-2 font-medium text-electric-700 hover:text-electric-800">
              返回登录
            </Link>
          </p>
        </motion.section>
      </section>
    </div>
  )
}
