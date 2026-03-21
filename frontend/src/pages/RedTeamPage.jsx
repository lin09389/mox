import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Play,
  Target,
  Zap,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Shield,
  Skull
} from 'lucide-react'
import { runRedTeam } from '../api/security'

const techniques = [
  { id: 'prompt_injection', name: '提示词注入', description: '直接注入恶意指令' },
  { id: 'jailbreak', name: '越狱攻击', description: '绕过安全限制获取禁止内容' },
  { id: 'role_play', name: '角色扮演', description: '通过扮演其他角色绕过限制' },
  { id: 'encoding', name: '编码绕过', description: '使用Base64等编码隐藏恶意内容' },
  { id: 'context_injection', name: '上下文注入', description: 'RAG上下文注入攻击' },
  { id: 'chain_of_thought', name: '思维链窃取', description: '提取模型推理过程' },
  { id: 'privilege_escalation', name: '权限提升', description: '获取更高执行权限' },
  { id: 'data_exfiltration', name: '数据泄露', description: '提取敏感训练数据' },
]

export default function RedTeamPage() {
  const [results, setResults] = useState([])
  const [running, setRunning] = useState(false)
  const [targetModel, setTargetModel] = useState('qwen3:4b')
  const [selectedTechniques, setSelectedTechniques] = useState(techniques.map(t => t.id))

  const handleRun = async () => {
    setRunning(true)
    try {
      const testResults = await runRedTeam(targetModel, selectedTechniques)
      setResults(testResults)
    } catch (error) {
      console.error('红队演练失败:', error)
    } finally {
      setRunning(false)
    }
  }

  const toggleTechnique = (id) => {
    setSelectedTechniques(prev =>
      prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]
    )
  }

  const successCount = results.filter(r => r.success).length
  const successRate = results.length > 0 ? (successCount / results.length * 100).toFixed(1) : 0

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-lava-100 rounded-lg flex items-center justify-center border border-lava-200/70">
            <Skull className="w-6 h-6 text-lava-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold font-display text-graphite-900 tracking-tight">
              红队演练模拟器
            </h1>
            <p className="text-sm text-graphite-500 mt-0.5">模拟真实攻击场景测试您的 LLM 安全性</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={targetModel}
            onChange={(e) => setTargetModel(e.target.value)}
            className="select-field w-40"
          >
            <option value="qwen3:4b">Qwen3:4B (本地)</option>
            <option value="gemma3:4b">Gemma3:4B (本地)</option>
            <option value="gpt-4">GPT-4</option>
            <option value="gpt-3.5">GPT-3.5</option>
            <option value="claude-3">Claude 3</option>
          </select>
          <button
            onClick={handleRun}
            disabled={running || selectedTechniques.length === 0}
            className="btn-primary"
          >
            {running ? (
              <>
                <div className="spinner" />
                攻击中...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" />
                开始攻击
              </>
            )}
          </button>
        </div>
      </motion.div>

      {/* 统计卡片 */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
      >
        <div className="card text-center">
          <p className="text-3xl font-bold font-display text-graphite-900">{results.length}</p>
          <p className="text-xs text-graphite-500 mt-1">攻击场景总数</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold font-display text-lava-600">{successCount}</p>
          <p className="text-xs text-graphite-500 mt-1">成功突破</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold font-display text-amber-600">{successRate}%</p>
          <p className="text-xs text-graphite-500 mt-1">突破成功率</p>
        </div>
      </motion.div>

      {/* 攻击技术选择 */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="card"
      >
        <h2 className="text-base font-semibold text-graphite-900 mb-4 flex items-center gap-2">
          <Target className="w-4.5 h-4.5 text-lava-500" />
          选择攻击技术
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {techniques.map((tech) => (
            <button
              key={tech.id}
              onClick={() => toggleTechnique(tech.id)}
              className={`p-4 rounded-lg border text-left transition-all duration-150 ${
                selectedTechniques.includes(tech.id)
                  ? 'border-lava-500 bg-lava-50/50'
                  : 'border-graphite-200/70 bg-white hover:border-graphite-300'
              }`}
            >
              <div className={`font-medium text-sm mb-1 ${selectedTechniques.includes(tech.id) ? 'text-lava-700' : 'text-graphite-700'}`}>
                {tech.name}
              </div>
              <div className="text-[11px] text-graphite-400">{tech.description}</div>
            </button>
          ))}
        </div>
      </motion.div>

      {/* 攻击结果 */}
      {results.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-0 overflow-hidden"
        >
          <div className="px-5 py-4 border-b border-graphite-200/60">
            <h2 className="text-base font-semibold text-graphite-900 flex items-center gap-2">
              <Skull className="w-4.5 h-4.5 text-lava-500" />
              攻击结果详情
            </h2>
          </div>
          <div className="divide-y divide-graphite-200/60">
            {results.map((result, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="p-5"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {result.success ? (
                      <div className="w-10 h-10 rounded-lg bg-lava-100 flex items-center justify-center">
                        <XCircle className="w-5 h-5 text-lava-600" />
                      </div>
                    ) : (
                      <div className="w-10 h-10 rounded-lg bg-neon-100 flex items-center justify-center">
                        <CheckCircle className="w-5 h-5 text-neon-600" />
                      </div>
                    )}
                    <div>
                      <h3 className="font-semibold text-sm text-graphite-900">{result.scenario}</h3>
                      <p className="text-xs text-graphite-500">{result.technique}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`font-bold text-sm ${result.success ? 'text-lava-600' : 'text-neon-600'}`}>
                      {result.success ? '突破成功' : '成功防御'}
                    </div>
                    <div className="text-[11px] text-graphite-400">尝试次数: {result.attempts}</div>
                  </div>
                </div>
                {result.final_prompt && (
                  <div className="mt-3 p-3 bg-graphite-50/80 rounded-md">
                    <div className="text-[11px] font-semibold text-graphite-500 mb-1">攻击提示词:</div>
                    <div className="text-xs font-mono text-graphite-700">{result.final_prompt.substring(0, 100)}...</div>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* 空状态 */}
      {results.length === 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="card flex flex-col items-center justify-center min-h-[300px] text-center"
        >
          <div className="w-16 h-16 rounded-xl bg-graphite-100 flex items-center justify-center mb-4">
            <Skull className="w-8 h-8 text-graphite-400" />
          </div>
          <h3 className="text-base font-semibold text-graphite-700 mb-2">点击开始红队演练</h3>
          <p className="text-sm text-graphite-500 mb-5">选择攻击技术并开始模拟真实攻击场景</p>
          <div className="flex justify-center gap-6 text-xs text-graphite-400">
            <span className="flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5" />
              8种攻击技术
            </span>
            <span className="flex items-center gap-1.5">
              <Target className="w-3.5 h-3.5" />
              真实场景模拟
            </span>
          </div>
        </motion.div>
      )}
    </div>
  )
}
