import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, Loader, Lock, LogOut, Mail, ShieldCheck } from 'lucide-react'
import toast from 'react-hot-toast'
import { clearSession, DEMO_MODE_ENABLED, useAuthSession, persistSession } from '../auth'
import { authApi } from '../api'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { session, isAuthenticated } = useAuthSession()
  const [form, setForm] = useState({ username: '', password: '' })
  const [isLoading, setIsLoading] = useState(false)

  const nextPath = location.state?.from?.pathname || '/'
  const searchParams = new URLSearchParams(location.search)
  const expiredReason = searchParams.get('reason') === 'expired'

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setIsLoading(true)

    try {
      const payload = await authApi.login({
        username: form.username.trim(),
        password: form.password,
      })
      persistSession(payload)
      toast.success('Login successful.')
      navigate(nextPath, { replace: true })
    } catch (error) {
      const message = error.response?.data?.message || error.response?.data?.detail || 'Login failed.'
      toast.error(message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = () => {
    clearSession()
    toast.success('Signed out.')
  }

  return (
    <div className="flex min-h-[80vh] items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-md space-y-8"
      >
        <div className="text-center">
          <motion.div
            initial={{ scale: 0.94 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="relative mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-graphite-50 shadow-lifted"
          >
            <ShieldCheck className="h-8 w-8 text-white" />
            <motion.div
              className="absolute -bottom-1 -right-1 h-4 w-4 rounded-full border-2 border-white bg-neon-500"
              animate={{ scale: [1, 1.18, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          </motion.div>
          <h1 className="mt-6 font-display text-3xl font-extrabold tracking-tight text-graphite-900">
            Sign in to Mox
          </h1>
          <p className="mt-2 text-sm text-graphite-500">Use a real backend account to access the security console.</p>
        </div>

        {(expiredReason || DEMO_MODE_ENABLED) && (
          <div className="rounded-2xl border border-amber-200/70 bg-amber-900/80 px-4 py-3 text-sm text-amber-800">
            {expiredReason
              ? 'Your session expired. Please sign in again.'
              : 'Demo mode is enabled. Some pages can fall back to sample data when the API is unavailable.'}
          </div>
        )}

        <div className="card mt-8 shadow-card">
          {isAuthenticated ? (
            <div className="space-y-6">
              <div>
                <p className="text-sm font-medium text-graphite-900">You are already signed in.</p>
                <p className="mt-1 text-sm text-graphite-500">
                  {session?.user?.username || session?.user?.email || 'Authenticated user'}
                </p>
              </div>
              <div className="flex gap-3">
                <button type="button" className="btn-primary flex-1" onClick={() => navigate('/', { replace: true })}>
                  Open Console
                  <ArrowRight className="h-4 w-4" />
                </button>
                <button type="button" className="btn-secondary" onClick={handleLogout}>
                  <LogOut className="h-4 w-4" />
                  Sign out
                </button>
              </div>
            </div>
          ) : (
            <form className="space-y-6" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="username" className="label">
                  Username or email
                </label>
                <div className="relative mt-1">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <Mail className="h-5 w-5 text-graphite-600" />
                  </div>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    autoComplete="username"
                    required
                    value={form.username}
                    onChange={handleChange}
                    className="input-field pl-10"
                    placeholder="admin"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="label">
                  Password
                </label>
                <div className="relative mt-1">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                    <Lock className="h-5 w-5 text-graphite-600" />
                  </div>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    required
                    value={form.password}
                    onChange={handleChange}
                    className="input-field pl-10"
                    placeholder="Enter your password"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="flex w-full justify-center rounded-md border border-transparent bg-graphite-50 px-4 py-2.5 text-sm font-medium text-white shadow-soft transition-all duration-200 hover:bg-graphite-100 disabled:opacity-70"
                aria-busy={isLoading}
              >
                {isLoading ? (
                  <Loader className="h-5 w-5 animate-spin" />
                ) : (
                  <>
                    Sign in <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </button>
            </form>
          )}

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-graphite-200" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="bg-white px-2 text-graphite-500">Need an account?</span>
              </div>
            </div>

            <div className="mt-6 text-center">
              <Link
                to="/register"
                className="flex items-center justify-center gap-1 font-medium text-electric-700 transition-colors hover:text-electric-500"
              >
                Create an account <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
