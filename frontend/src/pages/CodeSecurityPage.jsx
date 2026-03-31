import { useState } from 'react'
import { toast } from 'react-hot-toast'
import { AlertTriangle, Code2, ShieldAlert, ShieldCheck } from 'lucide-react'
import api from '../api'
import { MetricCard, PageHeader, PanelHeader } from '../components/ui/AppFrame'

const CWE_TYPES = [
  { cwe: 'CWE-89', name: 'SQL 注入', severity: 'critical' },
  { cwe: 'CWE-79', name: 'XSS 跨站脚本', severity: 'high' },
  { cwe: 'CWE-78', name: '命令注入', severity: 'critical' },
  { cwe: 'CWE-22', name: '路径遍历', severity: 'high' },
  { cwe: 'CWE-287', name: '鉴权缺陷', severity: 'high' },
  { cwe: 'CWE-200', name: '敏感信息泄露', severity: 'high' },
]

function demoResult(text) {
  const critical = text.toLowerCase().includes('exec') || text.toLowerCase().includes('shell')
  return {
    _demo_mode: true,
    vulnerabilities: [
      critical
        ? { cwe: 'CWE-78', name: '命令注入', severity: 'critical', detail: '检测到可执行命令拼接。' }
        : { cwe: 'CWE-79', name: 'XSS 风险', severity: 'high', detail: '输出内容缺少转义处理。' },
      { cwe: 'CWE-22', name: '路径遍历', severity: 'medium', detail: '文件路径输入缺少白名单限制。' },
    ],
    summary: critical ? '存在高危注入风险，建议立即修复。' : '发现中高风险问题，建议补充校验。'
  }
}

export default function CodeSecurityPage() {
  const [selectedModel, setSelectedModel] = useState('qwen:4b')
  const [codePrompt, setCodePrompt] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const runSecurityTest = async () => {
    if (!codePrompt.trim()) {
      toast.error('请输入代码或需求描述。')
      return
    }

    setLoading(true)
    setResult(null)
    try {
      const response = await api.post('/api/code/security', { prompt: codePrompt, model: selectedModel })
      setResult(response.data)
      toast.success('代码安全检测完成。')
    } catch {
      setResult(demoResult(codePrompt))
      toast('后端不可用，已展示演示检测结果。', { icon: '⚠️' })
    } finally {
      setLoading(false)
    }
  }

  const vulnerabilities = result?.vulnerabilities || []
  const criticalCount = vulnerabilities.filter((item) => item.severity === 'critical').length

  return (
    <div className="page-shell">
      <PageHeader
        eyebrow="CODE SECURITY"
        title="代码安全检测中心"
        description="快速识别常见 CWE 风险，统一输出严重程度与修复建议。"
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <section className="card card-glow">
          <PanelHeader title="检测配置" description="输入代码片段或需求描述后开始扫描。" />
          <div className="space-y-5">
            <div>
              <label className="label">检测模型</label>
              <input className="input-field" value={selectedModel} onChange={(event) => setSelectedModel(event.target.value)} />
            </div>
            <div>
              <label className="label">代码或需求描述</label>
              <textarea rows={7} className="textarea-field font-mono" value={codePrompt} onChange={(event) => setCodePrompt(event.target.value)} placeholder="粘贴代码片段，或描述你要实现的逻辑。" />
            </div>
            <button type="button" onClick={runSecurityTest} disabled={loading} className="btn-primary w-full justify-center py-3">
              <ShieldAlert className="h-4 w-4" />
              {loading ? '检测中' : '运行安全检测'}
            </button>
          </div>
        </section>

        <section className="card card-glow">
          <PanelHeader title="检测结果" description="按漏洞类型和严重程度展示结果。" />
          {result ? (
            <div className="space-y-4">
              {result._demo_mode ? <div className="badge badge-warning">当前为演示结果</div> : null}
              <div className="grid gap-3 sm:grid-cols-3">
                <MetricCard icon={Code2} label="检测项" value={CWE_TYPES.length} hint="内置规则数量" tone="electric" />
                <MetricCard icon={ShieldAlert} label="发现漏洞" value={vulnerabilities.length} hint="需修复项" tone="lava" />
                <MetricCard icon={AlertTriangle} label="高危数量" value={criticalCount} hint="优先处理" tone="amber" />
              </div>
              <div className="space-y-3">
                {vulnerabilities.map((item, index) => (
                  <div key={`${item.cwe}-${index}`} className="rounded-[18px] border border-graphite-200/70 bg-white/80 p-4">
                    <div className="mb-2 flex items-center justify-between">
                      <p className="text-sm font-semibold text-graphite-900">{item.cwe} · {item.name}</p>
                      <span className={`badge ${item.severity === 'critical' ? 'badge-danger' : item.severity === 'high' ? 'badge-warning' : 'badge-neutral'}`}>
                        {item.severity}
                      </span>
                    </div>
                    <p className="text-sm text-graphite-600">{item.detail}</p>
                  </div>
                ))}
              </div>
              <div className="rounded-[18px] border border-graphite-200/70 bg-white/80 p-4">
                <p className="text-sm font-semibold text-graphite-900">综合结论</p>
                <p className="mt-2 text-sm text-graphite-600">{result.summary || '未返回摘要。'}</p>
              </div>
            </div>
          ) : (
            <div className="panel-muted flex min-h-[380px] items-center justify-center text-sm text-graphite-500">
              运行检测后，这里会显示漏洞清单与修复优先级。
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
