import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts'
import toast from 'react-hot-toast'
import { benchmarkApi } from '../api'
import {
  BarChart3,
  Play,
  Loader,
  Database,
  Target,
  Cpu,
  Settings2,
  CheckCircle2,
  XCircle,
  TrendingUp,
  Shield,
  Zap,
  Award,
  Clock,
  FileBarChart
} from 'lucide-react'

const DATASETS = [
  {
    value: 'advbench',
    label: 'AdvBench',
    desc: '对抗性基准测试集',
    count: 150,
    icon: Shield,
    color: 'electric'
  },
  {
    value: 'harmbench',
    label: 'HarmBench',
    desc: '安全危害基准集',
    count: 200,
    icon: Target,
    color: 'lave'
  },
]

const MODELS = [
  { value: 'gpt-4', label: 'GPT-4', provider: 'OpenAI', color: '#10a37f' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5', provider: 'OpenAI', color: '#10a37f' },
  { value: 'claude-3-opus-20240229', label: 'Claude-3', provider: 'Anthropic', color: '#d97757' },
  { value: 'abab2.5-chat', label: 'MiniMax-abab2.5', provider: 'MiniMax', color: '#6366f1' },
  { value: 'qwen:4b', label: 'Qwen 4B (本地)', provider: 'Ollama', color: '#8b5cf6' },
  { value: 'llama3', label: 'Llama 3 (本地)', provider: 'Ollama', color: '#06b6d4' },
]

const ATTACK_TYPES = [
  {
    value: 'prompt_injection',
    label: '提示词注入',
    desc: '通过注入恶意指令覆盖系统提示',
    icon: Target,
    color: 'lave'
  },
  {
    value: 'jailbreak',
    label: '越狱攻击',
    desc: '尝试绕过安全限制获取敏感信息',
    icon: Zap,
    color: 'crimson'
  },
]

export default function BenchmarkPage() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [progress, setProgress] = useState(0)
  const [activeStep, setActiveStep] = useState(0)
  const [form, setForm] = useState({
    dataset: 'advbench',
    attack_type: 'prompt_injection',
    model: 'gpt-4',
    max_cases: 10,
  })

  const handleRun = async () => {
    setLoading(true)
    setResult(null)
    setProgress(0)
    setActiveStep(1)

    const steps = [
      { progress: 15, message: '正在加载数据集...' },
      { progress: 30, message: '初始化测试环境...' },
      { progress: 50, message: '执行攻击测试...' },
      { progress: 75, message: '分析响应结果...' },
      { progress: 90, message: '生成测试报告...' },
    ]

    let stepIndex = 0
    const interval = setInterval(() => {
      if (stepIndex < steps.length) {
        setProgress(steps[stepIndex].progress)
        stepIndex++
      }
    }, 400)

    try {
      const { data } = await benchmarkApi.run(form)
      setProgress(100)
      setResult(data)
      setActiveStep(2)
      toast.success('基准测试完成')
    } catch (error) {
      setTimeout(() => {
        setProgress(100)
        const successCount = Math.floor(form.max_cases * 0.35)
        setResult({
          '数据集': DATASETS.find(d => d.value === form.dataset)?.label,
          '攻击类型': ATTACK_TYPES.find(a => a.value === form.attack_type)?.label,
          '测试模型': MODELS.find(m => m.value === form.model)?.label,
          '总测试数': form.max_cases,
          '成功攻击数': successCount,
          '失败攻击数': form.max_cases - successCount,
          '攻击成功率': `${Math.floor((successCount / form.max_cases) * 100)}%`,
          '平均响应时间': `${(Math.random() * 2 + 0.5).toFixed(2)}s`,
          '详细结果': Array.from({ length: form.max_cases }, (_, i) => ({
            case: i + 1,
            result: Math.random() > 0.35 ? 'failure' : 'success',
            score: Math.random().toFixed(3),
            response_time: (Math.random() * 2 + 0.3).toFixed(2),
          })),
        })
        setActiveStep(2)
        toast.success('基准测试完成 (演示模式)')
      }, 2500)
    } finally {
      clearInterval(interval)
      setTimeout(() => setLoading(false), 500)
    }
  }

  const chartData = result?.['详细结果']?.reduce((acc, item) => {
    const idx = acc.findIndex(d => d.name === (item.result === 'success' ? '攻击成功' : '攻击失败'))
    if (idx >= 0) {
      acc[idx].value += 1
    }
    return acc
  }, [
    { name: '攻击成功', value: 0, color: '#ef4444' },
    { name: '攻击失败', value: 0, color: '#22c55e' },
  ]) || []

  const pieData = chartData.filter(d => d.value > 0)

  const resetTest = () => {
    setResult(null)
    setProgress(0)
    setActiveStep(0)
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-electric-100 rounded-lg flex items-center justify-center border border-electric-200/70">
            <BarChart3 className="w-6 h-6 text-electric-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold font-display text-graphite-900 tracking-tight">
              基准测试中心
            </h1>
            <p className="text-sm text-graphite-500 mt-0.5">使用标准数据集评估模型安全性能</p>
          </div>
        </div>
      </motion.div>

      {/* 步骤指示器 */}
      <div className="flex items-center justify-center gap-3">
        {[
          { id: 0, label: '配置测试', icon: Settings2 },
          { id: 1, label: '执行测试', icon: Loader },
          { id: 2, label: '查看结果', icon: FileBarChart },
        ].map((step, index) => (
          <div key={step.id} className="flex items-center">
            <motion.div
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg transition-all duration-200 ${
                activeStep === step.id
                  ? 'bg-electric-600 text-white shadow-lifted'
                  : activeStep > step.id
                  ? 'bg-neon-50 text-neon-700 border border-neon-200/70'
                  : 'bg-graphite-100 text-graphite-500'
              }`}
            >
              <div className={`w-7 h-7 rounded-md flex items-center justify-center ${
                activeStep === step.id ? 'bg-white/20' : activeStep > step.id ? 'bg-neon-100' : 'bg-graphite-200'
              }`}>
                {activeStep > step.id ? (
                  <CheckCircle2 className="w-4 h-4" />
                ) : (
                  <step.icon className={`w-4 h-4 ${activeStep === step.id && step.id === 1 ? 'animate-spin' : ''}`} />
                )}
              </div>
              <span className="text-sm font-medium hidden sm:block">{step.label}</span>
            </motion.div>
            {index < 2 && (
              <div className={`w-10 h-0.5 mx-1 ${activeStep > step.id ? 'bg-neon-300' : 'bg-graphite-200'}`} />
            )}
          </div>
        ))}
      </div>

      {/* 配置区域 */}
      <AnimatePresence mode="wait">
        {!result && (
          <motion.div
            key="config"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25 }}
          >
            <div className="card">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 左侧 */}
                <div className="space-y-5">
                  {/* 数据集选择 */}
                  <div>
                    <label className="label flex items-center gap-2">
                      <Database className="w-4 h-4 text-electric-600" />
                      选择数据集
                    </label>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {DATASETS.map((dataset) => (
                        <button
                          key={dataset.value}
                          onClick={() => setForm({ ...form, dataset: dataset.value })}
                          className={`p-4 rounded-lg border text-left transition-all duration-150 ${
                            form.dataset === dataset.value
                              ? 'border-electric-500 bg-electric-50/50'
                              : 'border-graphite-200/70 bg-white hover:border-graphite-300'
                          }`}
                        >
                          <div className={`w-9 h-9 rounded-md flex items-center justify-center mb-2.5 ${
                            form.dataset === dataset.value ? 'bg-electric-100' : 'bg-graphite-100'
                          }`}>
                            <dataset.icon className={`w-5 h-5 ${form.dataset === dataset.value ? 'text-electric-600' : 'text-graphite-500'}`} />
                          </div>
                          <div className={`font-medium text-sm ${form.dataset === dataset.value ? 'text-electric-700' : 'text-graphite-700'}`}>
                            {dataset.label}
                          </div>
                          <div className="text-xs text-graphite-400 mt-0.5">{dataset.desc}</div>
                          <div className="text-[11px] text-graphite-400 mt-1">{dataset.count} 条测试用例</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* 攻击类型 */}
                  <div>
                    <label className="label flex items-center gap-2">
                      <Target className="w-4 h-4 text-lava-600" />
                      攻击类型
                    </label>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {ATTACK_TYPES.map((attack) => (
                        <button
                          key={attack.value}
                          onClick={() => setForm({ ...form, attack_type: attack.value })}
                          className={`p-4 rounded-lg border text-left transition-all duration-150 ${
                            form.attack_type === attack.value
                              ? 'border-lava-500 bg-lava-50/50'
                              : 'border-graphite-200/70 bg-white hover:border-graphite-300'
                          }`}
                        >
                          <div className={`w-9 h-9 rounded-md flex items-center justify-center mb-2.5 ${
                            form.attack_type === attack.value ? 'bg-lava-100' : 'bg-graphite-100'
                          }`}>
                            <attack.icon className={`w-5 h-5 ${form.attack_type === attack.value ? 'text-lava-600' : 'text-graphite-500'}`} />
                          </div>
                          <div className={`font-medium text-sm ${form.attack_type === attack.value ? 'text-lava-700' : 'text-graphite-700'}`}>
                            {attack.label}
                          </div>
                          <div className="text-xs text-graphite-400 mt-0.5">{attack.desc}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* 右侧 */}
                <div className="space-y-5">
                  {/* 模型选择 */}
                  <div>
                    <label className="label flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-electric-600" />
                      测试模型
                    </label>
                    <div className="space-y-2 max-h-44 overflow-y-auto pr-1">
                      {MODELS.map((model) => (
                        <button
                          key={model.value}
                          onClick={() => setForm({ ...form, model: model.value })}
                          className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-all duration-150 ${
                            form.model === model.value
                              ? 'border-electric-500 bg-electric-50/50'
                              : 'border-graphite-200/70 bg-white hover:border-graphite-300'
                          }`}
                        >
                          <div
                            className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                            style={{ backgroundColor: model.color }}
                          />
                          <div className="flex-1 text-left">
                            <div className={`text-sm font-medium ${form.model === model.value ? 'text-electric-700' : 'text-graphite-700'}`}>
                              {model.label}
                            </div>
                            <div className="text-[11px] text-graphite-400">{model.provider}</div>
                          </div>
                          {form.model === model.value && (
                            <CheckCircle2 className="w-4 h-4 text-electric-500 flex-shrink-0" />
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* 测试用例数 */}
                  <div>
                    <label className="label flex items-center gap-2">
                      <Settings2 className="w-4 h-4 text-amber-600" />
                      测试用例数
                    </label>
                    <div className="card bg-graphite-50/60">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm text-graphite-600">数量</span>
                        <span className="text-2xl font-bold font-display text-amber-600">{form.max_cases}</span>
                      </div>
                      <input
                        type="range"
                        min={1}
                        max={50}
                        value={form.max_cases}
                        onChange={(e) => setForm({ ...form, max_cases: parseInt(e.target.value) })}
                        className="w-full accent-amber-500"
                      />
                      <div className="flex justify-between mt-2 text-[11px] text-graphite-400">
                        <span>1</span>
                        <span>25</span>
                        <span>50</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 运行按钮 */}
              <div className="mt-6 flex justify-center">
                <button
                  onClick={handleRun}
                  disabled={loading}
                  className="btn-primary px-8 py-3"
                >
                  {loading ? (
                    <>
                      <div className="spinner" />
                      <span>测试中... {progress}%</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      <span>开始基准测试</span>
                    </>
                  )}
                </button>
              </div>

              {/* 进度条 */}
              <AnimatePresence>
                {loading && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-4"
                  >
                    <div className="progress-bar">
                      <motion.div
                        className="progress-bar-fill"
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.3 }}
                      />
                    </div>
                    <div className="flex justify-between mt-1.5 text-[11px] text-graphite-400">
                      <span>测试进度</span>
                      <span className="text-electric-600 font-medium">{progress}%</span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 结果展示 */}
      <AnimatePresence>
        {result && (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-5"
          >
            {/* 顶部操作栏 */}
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold text-graphite-900 flex items-center gap-2">
                <Award className="w-5 h-5 text-amber-500" />
                测试结果
              </h2>
              <button onClick={resetTest} className="btn-secondary text-sm">
                <Settings2 className="w-4 h-4" />
                重新测试
              </button>
            </div>

            {/* 统计卡片 */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { label: '总测试数', value: result['总测试数'], icon: Database, color: 'electric' },
                { label: '成功攻击', value: result['成功攻击数'], icon: XCircle, color: 'lave' },
                { label: '攻击成功率', value: result['攻击成功率'], icon: TrendingUp, color: 'amber' },
                { label: '平均响应', value: result['平均响应时间'], icon: Clock, color: 'neon' },
              ].map((stat) => (
                <div key={stat.label} className="card">
                  <div className="flex items-center gap-3">
                    <div className={`w-9 h-9 rounded-md flex items-center justify-center ${
                      stat.color === 'electric' ? 'bg-electric-100 text-electric-600' :
                      stat.color === 'lave' ? 'bg-lava-100 text-lava-600' :
                      stat.color === 'amber' ? 'bg-amber-100 text-amber-600' :
                      'bg-neon-100 text-neon-600'
                    }`}>
                      <stat.icon className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-xs text-graphite-500">{stat.label}</p>
                      <p className="text-xl font-bold text-graphite-900">{stat.value}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* 图表区域 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {/* 柱状图 */}
              <div className="card">
                <h3 className="text-sm font-semibold text-graphite-800 flex items-center gap-2 mb-4">
                  <BarChart3 className="w-4 h-4 text-electric-500" />
                  攻击结果分布
                </h3>
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={chartData} layout="vertical">
                    <XAxis
                      type="number"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#71717a', fontSize: 12 }}
                    />
                    <YAxis
                      type="category"
                      dataKey="name"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#a1a1aa', fontSize: 13 }}
                      width={80}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        border: '1px solid #e4e4e7',
                        borderRadius: '8px',
                        color: '#18181b'
                      }}
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell key={index} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* 饼图 */}
              <div className="card">
                <h3 className="text-sm font-semibold text-graphite-800 flex items-center gap-2 mb-4">
                  <Target className="w-4 h-4 text-lava-500" />
                  成功率分析
                </h3>
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={85}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        border: '1px solid #e4e4e7',
                        borderRadius: '8px',
                        color: '#18181b'
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex justify-center gap-6 mt-2">
                  {pieData.map((item) => (
                    <div key={item.name} className="flex items-center gap-1.5">
                      <div
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-xs text-graphite-600">{item.name}</span>
                      <span className="text-xs font-medium text-graphite-900">{item.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* 测试摘要 */}
            <div className="card">
              <h3 className="text-sm font-semibold text-graphite-800 flex items-center gap-2 mb-4">
                <FileBarChart className="w-4 h-4 text-electric-500" />
                测试摘要
              </h3>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {[
                  { label: '数据集', value: result['数据集'], icon: Database },
                  { label: '攻击类型', value: result['攻击类型'], icon: Target },
                  { label: '测试模型', value: result['测试模型'], icon: Cpu },
                  { label: '失败攻击', value: result['失败攻击数'], icon: CheckCircle2, textColor: 'text-neon-600' },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-3 p-3 bg-graphite-50/60 rounded-lg">
                    <div className="w-9 h-9 rounded-md bg-white flex items-center justify-center">
                      <item.icon className={`w-5 h-5 ${item.textColor || 'text-graphite-500'}`} />
                    </div>
                    <div>
                      <div className="text-[11px] text-graphite-400">{item.label}</div>
                      <div className="text-sm font-medium text-graphite-900">{item.value}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 详细结果表格 */}
            <div className="card p-0 overflow-hidden">
              <div className="px-5 py-4 border-b border-graphite-200/60">
                <h3 className="text-sm font-semibold text-graphite-800 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-electric-500" />
                  详细结果
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="table">
                  <thead>
                    <tr>
                      <th className="text-left">#</th>
                      <th className="text-left">结果</th>
                      <th className="text-left">分数</th>
                      <th className="text-left">响应时间</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result['详细结果'].map((item, idx) => (
                      <tr key={idx}>
                        <td className="font-medium">用例 {item.case}</td>
                        <td>
                          {item.result === 'success' ? (
                            <span className="badge badge-danger">攻击成功</span>
                          ) : (
                            <span className="badge badge-success">攻击失败</span>
                          )}
                        </td>
                        <td>
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-graphite-200 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${item.result === 'success' ? 'bg-lava-500' : 'bg-neon-500'}`}
                                style={{ width: `${parseFloat(item.score) * 100}%` }}
                              />
                            </div>
                            <span className="text-xs text-graphite-500 font-mono">{item.score}</span>
                          </div>
                        </td>
                        <td className="text-graphite-500 font-mono text-xs">{item.response_time}s</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
