import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { AlertTriangle, CheckCircle2, FileText, ShieldCheck, Fingerprint, Loader2, Target, Clock3 } from 'lucide-react'
import { platformApi, isDemoModeEnabled } from '../api'
import { useLocalStorage } from '../hooks/useLocalStorage'
import { MetricCard, PanelHeader, ProgressMeter } from '../components/ui/AppFrame'
import ModelSelect from '../components/ui/ModelSelect'
import { HubPanelIntro } from '../context/HubContext'
import { PingButton } from '../components/ui/PingButton'

const SAFETY_CATEGORIES = [
  { id: 'harmful_content', name: '违禁常识侵犯' },
  { id: 'personal_info', name: '隐私边界探测' },
  { id: 'professional_advice', name: '违规专业越权' },
  { id: 'hate_speech', name: '仇恨与偏见言论' },
  { id: 'sexual_content', name: '未过滤成人特征' },
  { id: 'violence', name: '物理伤害诱导' },
  { id: 'self_harm', name: '自毁行为支持' },
  { id: 'deception', name: '深度伪造与欺诈' },
]

function demoCard(model) {
  return {
    _demo_mode: true,
    model_name: model,
    overall_score: 0.78,
    risk_level: 'medium',
    categories: SAFETY_CATEGORIES.map((item, index) => ({
      id: item.id,
      name: item.name,
      score: Number((0.55 + (index % 4) * 0.08).toFixed(2)),
    })),
    summary: '目标模型基础防御矩阵工作正常。但在“深度伪造与欺诈”及“隐私边界探测”等复杂语境下暴露中等漏洞，存在逻辑旁路被攻破的风险，建议强化特定阈值拦截策略。',
  }
}

import { WorkspacePageShell, WorkspaceRunButton } from '../components/workspace'
import { itemVariants } from '../utils/animations'

export default function SafetyCardPage() {
  const [modelName, setModelName] = useLocalStorage('mox_safetycard_model', 'gpt-4')
  const [loading, setLoading] = useState(false)
  const [safetyCard, setSafetyCard] = useState(null)
  const [recentCards, setRecentCards] = useState([])

  useEffect(() => {
    const loadRecent = async () => {
      try {
        const data = await platformApi.safetyCardsRecent()
        setRecentCards(data || [])
      } catch {
        setRecentCards([])
      }
    }
    loadRecent()
  }, [])

  const generateCard = async () => {
    setLoading(true)
    setSafetyCard(null)
    try {
      const data = await platformApi.safetyCardsGenerate({ model_name: modelName })
      setSafetyCard(data)
      toast.success('大模型安全评估镜像已生成。')
    } catch {
      if (isDemoModeEnabled) {
        setSafetyCard(demoCard(modelName))
        toast('引擎脱机，进入离线沙箱推演模式。', { icon: '⚠️' })
      } else {
        toast.error('安全卡片生成失败，请检查后端连接。')
      }
    }
    setLoading(false)
  }

  const overall = Math.round((safetyCard?.overall_score || 0) * 100)

  return (
    <WorkspacePageShell>
      <HubPanelIntro description="自动化扫描大模型合规缺陷，生成多维度风险态势画像。" />

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <motion.section variants={itemVariants} className="card p-6 h-fit lg:sticky lg:top-6 border-[var(--border-glass)]">
          <PanelHeader title="评测靶机配置" description="指定待检阅的模型引擎，触发全量弱点扫描。" />
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest block mb-2">目标靶机标识 (Model Namespace)</label>
              <div className="flex items-center gap-2">
                <div className="flex-1">
                  <ModelSelect value={modelName} onChange={setModelName} />
                </div>
                <PingButton targetModel={modelName} />
              </div>
            </div>
            
            <WorkspaceRunButton
              type="button"
              onClick={generateCard}
              disabled={loading || !modelName.trim()}
              loading={loading}
              icon={Fingerprint}
              loadingText="正在提取模型防御特征..."
              className="py-4"
            >
              生成完整安全快照
            </WorkspaceRunButton>

            <div className="mt-8 pt-6 border-t border-[var(--border-glass)]">
              <p className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest mb-4 flex items-center gap-2">
                <Clock3 className="h-3.5 w-3.5" /> 近期扫描档案
              </p>
              <div className="space-y-2">
                {recentCards.length ? (
                  recentCards.slice(0, 4).map((item, index) => (
                    <div key={index} className="flex items-center justify-between rounded-xl border border-[var(--border-glass)] bg-[var(--bg-glass)] px-4 py-3 hover:bg-[var(--bg-glass-strong)] hover:border-cyan-500/30 transition-colors cursor-default">
                      <span className="font-mono text-sm font-bold text-[var(--text-main)] flex items-center gap-2">
                        <ShieldCheck className="h-3.5 w-3.5 text-cyan-500" />
                        {item.model_name || item.model || 'Unknown'}
                      </span>
                      <span className="text-[10px] font-mono text-[var(--text-muted)]">{item.created_at || 'Just now'}</span>
                    </div>
                  ))
                ) : (
                  <div className="flex flex-col items-center justify-center py-8 text-center bg-[var(--bg-glass)] rounded-xl border border-[var(--border-glass)] border-dashed">
                    <FileText className="h-6 w-6 text-[var(--text-muted)] opacity-50 mb-2" />
                    <p className="text-xs font-medium text-[var(--text-muted)]">本地缓存区暂无近期扫描记录</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </motion.section>

        <motion.section variants={itemVariants} className="card p-6 bg-[var(--bg-glass-strong)] border-[var(--border-glass)] shadow-[inset_0_0_40px_rgba(6,182,212,0.02)]">
          <PanelHeader title="全景安全画像" description="呈现防线完备度评分与各垂直维度的抵抗力分析。" />
          
          <AnimatePresence mode="wait">
            {safetyCard ? (
              <motion.div 
                key="card"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="space-y-6"
              >
                {safetyCard._demo_mode && (
                  <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-3 flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                    <span className="text-xs font-bold text-amber-500 tracking-wide">演习模式：基于沙箱历史特征注入</span>
                  </div>
                )}
                
                <div className="grid gap-4 sm:grid-cols-3">
                  <MetricCard icon={ShieldCheck} label="防线坚固度" value={`${overall}%`} hint={`靶机: ${safetyCard.model_name || modelName}`} tone="electric" />
                  <MetricCard icon={AlertTriangle} label="整体威胁研判" value={safetyCard.risk_level === 'high' ? '高危' : safetyCard.risk_level === 'medium' ? '中危' : '低风险'} hint="系统安全底线" tone={overall < 65 ? 'lava' : overall < 80 ? 'amber' : 'neon'} />
                  <MetricCard icon={CheckCircle2} label="覆盖检测簇" value={(safetyCard.categories || []).length} hint="深度扫描类目" tone="graphite" />
                </div>
                
                <div className="p-5 rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)]">
                  <ProgressMeter value={overall} tone={overall < 65 ? 'danger' : overall < 80 ? 'warning' : 'success'} label="大语言模型系统基线安全综合打分" />
                </div>
                
                <div className="space-y-4 pt-2">
                  <h4 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest border-b border-[var(--border-glass)] pb-2 flex items-center gap-2">
                    <Target className="h-4 w-4" /> 漏洞象限击穿率
                  </h4>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {(safetyCard.categories || []).map((item, index) => {
                      const score = Math.round((item.score || 0) * 100);
                      return (
                        <motion.div 
                          key={item.id || item.name} 
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: index * 0.05 }}
                          className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-4 hover:bg-[var(--bg-glass-strong)] hover:border-cyan-500/30 transition-all"
                        >
                          <div className="mb-3 flex items-center justify-between">
                            <p className="text-sm font-bold text-[var(--text-main)] font-display">{item.name}</p>
                            <span className={`badge border font-mono text-[10px] uppercase font-bold px-2 py-0.5 ${score < 60 ? 'bg-rose-500/10 text-rose-500 border-rose-500/20' : score < 80 ? 'bg-amber-500/10 text-amber-500 border-amber-500/20' : 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'}`}>{score}%</span>
                          </div>
                          <ProgressMeter value={score} tone={score < 60 ? 'danger' : score < 80 ? 'warning' : 'success'} />
                        </motion.div>
                      )
                    })}
                  </div>
                </div>
                
                <div className="rounded-xl border border-[var(--border-glass-strong)] bg-cyan-500/5 p-5 relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-1 h-full bg-cyan-500"></div>
                  <p className="text-sm font-bold text-[var(--text-main)] mb-3 flex items-center gap-2">
                    <Fingerprint className="h-4 w-4 text-cyan-500" /> 架构师智囊简报
                  </p>
                  <p className="text-sm font-medium text-[var(--text-muted)] leading-relaxed bg-[var(--bg-main)]/50 p-4 rounded-lg border border-[var(--border-glass)]">
                    {safetyCard.summary || '未返回有效推断。'}
                  </p>
                </div>
              </motion.div>
            ) : (
              <motion.div 
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex min-h-[400px] flex-col items-center justify-center gap-4 text-center p-8"
              >
                <div className="w-20 h-20 rounded-full bg-[var(--bg-glass-strong)] border border-[var(--border-glass)] flex items-center justify-center relative">
                  {loading && (
                    <div className="absolute inset-0 border-4 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin"></div>
                  )}
                  <ShieldCheck className={`h-10 w-10 ${loading ? 'text-cyan-500' : 'text-[var(--text-muted)] opacity-60'}`} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-[var(--text-main)]">{loading ? '正在计算风险向量...' : '体检载荷休眠中'}</h3>
                  <p className="mt-2 text-sm font-medium text-[var(--text-muted)] max-w-sm">
                    {loading ? '引擎正利用百万级高对抗样本轰炸模型各象限，捕捉非法输出并绘制防线轮廓，请耐心等待。' : '平台将利用动态混淆特征模拟真实世界的复杂攻击，系统评估靶机大语言模型的内容安全水位。'}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.section>
      </div>
    </WorkspacePageShell>
  )
}
