import { useState } from 'react'
import { Play, Target, Zap, AlertTriangle, CheckCircle, XCircle, Shield, Skull } from 'lucide-react'
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">红队演练模拟器</h1>
          <p className="text-gray-500">模拟真实攻击场景测试您的LLM安全性</p>
        </div>
        <div className="flex items-center gap-4">
          <select
            value={targetModel}
            onChange={(e) => setTargetModel(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg"
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
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            <Zap className={`w-4 h-4 ${running ? 'animate-pulse' : ''}`} />
            {running ? '攻击中...' : '开始攻击'}
          </button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <div className="text-3xl font-bold">{results.length}</div>
          <div className="text-gray-500">攻击场景总数</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <div className="text-3xl font-bold text-red-600">{successCount}</div>
          <div className="text-gray-500">成功突破</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <div className="text-3xl font-bold text-orange-600">{successRate}%</div>
          <div className="text-gray-500">突破成功率</div>
        </div>
      </div>

      {/* 攻击技术选择 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Target className="w-5 h-5 text-red-500" />
          选择攻击技术
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {techniques.map((tech) => (
            <button
              key={tech.id}
              onClick={() => toggleTechnique(tech.id)}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                selectedTechniques.includes(tech.id)
                  ? 'border-red-500 bg-red-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="font-medium">{tech.name}</div>
              <div className="text-xs text-gray-500 mt-1">{tech.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* 攻击结果 */}
      {results.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Skull className="w-5 h-5 text-red-500" />
              攻击结果详情
            </h2>
          </div>
          <div className="divide-y divide-gray-200">
            {results.map((result, i) => (
              <div key={i} className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {result.success ? (
                      <XCircle className="w-6 h-6 text-red-500" />
                    ) : (
                      <CheckCircle className="w-6 h-6 text-green-500" />
                    )}
                    <div>
                      <h3 className="font-semibold">{result.scenario}</h3>
                      <p className="text-sm text-gray-500">{result.technique}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`font-bold ${result.success ? 'text-red-600' : 'text-green-600'}`}>
                      {result.success ? '⚠️ 突破成功' : '✅ 成功防御'}
                    </div>
                    <div className="text-sm text-gray-500">尝试次数: {result.attempts}</div>
                  </div>
                </div>
                {result.final_prompt && (
                  <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                    <div className="text-xs text-gray-500 mb-1">攻击提示词:</div>
                    <div className="text-sm font-mono text-gray-700">{result.final_prompt.substring(0, 100)}...</div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 空状态 */}
      {results.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <Skull className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-600 mb-2">点击开始红队演练</h3>
          <p className="text-gray-500 mb-4">选择攻击技术并开始模拟真实攻击场景</p>
          <div className="flex justify-center gap-4 text-sm text-gray-400">
            <span className="flex items-center gap-1"><Zap className="w-4 h-4" /> 8种攻击技术</span>
            <span className="flex items-center gap-1"><Target className="w-4 h-4" /> 真实场景模拟</span>
          </div>
        </div>
      )}
    </div>
  )
}
