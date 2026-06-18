import React from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error', error, errorInfo)
    this.setState({ errorInfo })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[60vh] flex-col items-center justify-center p-6 text-center">
          <div className="w-20 h-20 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mb-6 shadow-[0_0_30px_rgba(244,63,94,0.15)]">
            <AlertTriangle className="h-10 w-10 text-rose-500" />
          </div>
          <h2 className="text-2xl font-bold font-display text-[var(--text-main)] tracking-tight">系统模块发生异常崩溃</h2>
          <p className="mt-3 max-w-md text-sm font-medium leading-relaxed text-[var(--text-muted)]">
            UI 层捕获到了未预期的渲染错误。已阻断异常扩散以保护系统主进程。请尝试刷新当前视图上下文。
          </p>
          
          <button
            type="button"
            className="btn-primary mt-8 px-6 py-2.5 bg-rose-500 hover:bg-rose-600 border-rose-500 text-white shadow-[0_0_15px_rgba(244,63,94,0.3)] font-bold transition-all"
            onClick={() => window.location.reload()}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            重载视图 (Hard Reload)
          </button>

          {process.env.NODE_ENV === 'development' && this.state.error && (
            <div className="mt-8 text-left w-full max-w-2xl bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] p-4 rounded-xl overflow-auto text-xs text-rose-400/80 font-mono">
              <p className="font-bold mb-2 text-rose-500">{this.state.error.toString()}</p>
              <pre>{this.state.errorInfo?.componentStack}</pre>
            </div>
          )}
        </div>
      )
    }

    return this.props.children
  }
}
