import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts'
import toast from 'react-hot-toast'
import { benchmarkApi } from '../api'
import {
  BarChart3,
  Play,
  Loader2,
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
    color: 'from-blue-500 to-cyan-500'
  },
  { 
    value: 'harmbench', 
    label: 'HarmBench', 
    desc: '安全危害基准集', 
    count: 200,
    icon: Target,
    color: 'from-rose-500 to-pink-500'
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
    color: 'from-amber-500 to-orange-500'
  },
  { 
    value: 'jailbreak', 
    label: '越狱攻击', 
    desc: '尝试绕过安全限制获取敏感信息',
    icon: Zap,
    color: 'from-rose-500 to-red-500'
  },
]

const containerVariants = {
  hidden: { opacity: 0 },
  show: { 
    opacity: 1, 
    transition: { 
      staggerChildren: 0.08,
      delayChildren: 0.1
    } 
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { 
    opacity: 1, 
    y: 0,
    transition: {
      type: 'spring',
      stiffness: 100,
      damping: 15
    }
  }
}

const cardVariants = {
  hidden: { opacity: 0, scale: 0.95 },
  show: { 
    opacity: 1, 
    scale: 1,
    transition: {
      type: 'spring',
      stiffness: 100,
      damping: 15
    }
  }
}

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

    // Simulate progress with steps
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
      // Mock result
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
    { name: '攻击失败', value: 0, color: '#10b981' },
  ]) || []

  const pieData = chartData.filter(d => d.value > 0)

  const resetTest = () => {
    setResult(null)
    setProgress(0)
    setActiveStep(0)
  }

  return (
    <motion.div 
      className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950"
      initial="hidden"
      animate="show"
      variants={containerVariants}
    >
      {/* Header Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-violet-500/10 via-purple-500/10 to-pink-500/10" />
        <div className="absolute top-0 left-1/3 w-96 h-96 bg-violet-500/20 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/3 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" />
        
        <motion.div 
          className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12"
          variants={itemVariants}
        >
          <div className="text-center">
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: 'spring', stiffness: 200, damping: 20 }}
              className="inline-flex items-center justify-center w-20 h-20 mb-6 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 shadow-2xl shadow-violet-500/30"
            >
              <BarChart3 className="w-10 h-10 text-white" />
            </motion.div>
            
            <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent mb-4">
              基准测试中心
            </h1>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto">
              使用标准数据集评估模型安全性能，生成详细的测试报告
            </p>
          </div>
        </motion.div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        {/* Progress Steps */}
        <motion.div 
          className="mb-12"
          variants={itemVariants}
        >
          <div className="flex items-center justify-center">
            {[
              { id: 0, label: '配置测试', icon: Settings2 },
              { id: 1, label: '执行测试', icon: Loader2 },
              { id: 2, label: '查看结果', icon: FileBarChart },
            ].map((step, index) => (
              <div key={step.id} className="flex items-center">
                <motion.div
                  className={`flex items-center gap-3 px-6 py-3 rounded-xl transition-all duration-300 ${
                    activeStep === step.id
                      ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/25'
                      : activeStep > step.id
                      ? 'bg-emerald-500/20 text-emerald-400'
                      : 'bg-slate-800/50 text-slate-500'
                  }`}
                  animate={activeStep === step.id ? { scale: 1.05 } : { scale: 1 }}
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    activeStep === step.id ? 'bg-white/20' : 'bg-slate-700/50'
                  }`}>
                    {activeStep > step.id ? (
                      <CheckCircle2 className="w-5 h-5" />
                    ) : (
                      <step.icon className={`w-5 h-5 ${activeStep === step.id && step.id === 1 ? 'animate-spin' : ''}`} />
                    )}
                  </div>
                  <span className="font-medium hidden sm:block">{step.label}</span>
                </motion.div>
                {index < 2 && (
                  <div className={`w-12 sm:w-20 h-0.5 mx-2 ${
                    activeStep > step.id ? 'bg-emerald-500/50' : 'bg-slate-700/50'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </motion.div>

        {/* Configuration Card */}
        <AnimatePresence mode="wait">
          {!result && (
            <motion.div
              key="config"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <motion.div 
                className="p-8 rounded-3xl bg-slate-800/30 border border-slate-700/50 backdrop-blur-sm"
                variants={cardVariants}
              >
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Left Column */}
                  <div className="space-y-6">
                    {/* Dataset Selection */}
                    <div>
                      <label className="flex items-center gap-2 text-slate-300 font-medium mb-4">
                        <Database className="w-5 h-5 text-violet-400" />
                        选择数据集
                      </label>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {DATASETS.map((dataset) => (
                          <motion.button
                            key={dataset.value}
                            onClick={() => setForm({ ...form, dataset: dataset.value })}
                            className={`relative p-4 rounded-xl border-2 text-left transition-all duration-300 ${
                              form.dataset === dataset.value
                                ? 'border-violet-500/50 bg-violet-500/10'
                                : 'border-slate-700/50 bg-slate-800/30 hover:border-slate-600/50'
                            }`}
                            whileHover={{ scale: 1.02, y: -2 }}
                            whileTap={{ scale: 0.98 }}
                          >
                            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${dataset.color} flex items-center justify-center mb-3`}>
                              <dataset.icon className="w-5 h-5 text-white" />
                            </div>
                            <div className="font-medium text-slate-200">{dataset.label}</div>
                            <div className="text-sm text-slate-500 mt-1">{dataset.desc}</div>
                            <div className="text-xs text-slate-600 mt-2">{dataset.count} 条测试用例</div>
                          </motion.button>
                        ))}
                      </div>
                    </div>

                    {/* Attack Type Selection */}
                    <div>
                      <label className="flex items-center gap-2 text-slate-300 font-medium mb-4">
                        <Target className="w-5 h-5 text-rose-400" />
                        攻击类型
                      </label>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {ATTACK_TYPES.map((attack) => (
                          <motion.button
                            key={attack.value}
                            onClick={() => setForm({ ...form, attack_type: attack.value })}
                            className={`relative p-4 rounded-xl border-2 text-left transition-all duration-300 ${
                              form.attack_type === attack.value
                                ? 'border-rose-500/50 bg-rose-500/10'
                                : 'border-slate-700/50 bg-slate-800/30 hover:border-slate-600/50'
                            }`}
                            whileHover={{ scale: 1.02, y: -2 }}
                            whileTap={{ scale: 0.98 }}
                          >
                            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${attack.color} flex items-center justify-center mb-3`}>
                              <attack.icon className="w-5 h-5 text-white" />
                            </div>
                            <div className="font-medium text-slate-200">{attack.label}</div>
                            <div className="text-sm text-slate-500 mt-1">{attack.desc}</div>
                          </motion.button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Right Column */}
                  <div className="space-y-6">
                    {/* Model Selection */}
                    <div>
                      <label className="flex items-center gap-2 text-slate-300 font-medium mb-4">
                        <Cpu className="w-5 h-5 text-cyan-400" />
                        测试模型
                      </label>
                      <div className="space-y-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                        {MODELS.map((model) => (
                          <motion.button
                            key={model.value}
                            onClick={() => setForm({ ...form, model: model.value })}
                            className={`w-full flex items-center gap-4 p-3 rounded-xl border-2 transition-all duration-300 ${
                              form.model === model.value
                                ? 'border-cyan-500/50 bg-cyan-500/10'
                                : 'border-slate-700/50 bg-slate-800/30 hover:border-slate-600/50'
                            }`}
                            whileHover={{ scale: 1.01, x: 4 }}
                            whileTap={{ scale: 0.99 }}
                          >
                            <div 
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: model.color }}
                            />
                            <div className="flex-1 text-left">
                              <div className="font-medium text-slate-200">{model.label}</div>
                              <div className="text-xs text-slate-500">{model.provider}</div>
                            </div>
                            {form.model === model.value && (
                              <CheckCircle2 className="w-5 h-5 text-cyan-400" />
                            )}
                          </motion.button>
                        ))}
                      </div>
                    </div>

                    {/* Test Cases Slider */}
                    <div>
                      <label className="flex items-center gap-2 text-slate-300 font-medium mb-4">
                        <Settings2 className="w-5 h-5 text-amber-400" />
                        测试用例数
                      </label>
                      <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
                        <div className="flex items-center justify-between mb-4">
                          <span className="text-slate-400">数量</span>
                          <span className="text-2xl font-bold text-amber-400">{form.max_cases}</span>
                        </div>
                        <input
                          type="range"
                          min={1}
                          max={50}
                          value={form.max_cases}
                          onChange={(e) => setForm({ ...form, max_cases: parseInt(e.target.value) })}
                          className="w-full h-2 rounded-lg bg-slate-700 appearance-none cursor-pointer accent-amber-500"
                          style={{
                            background: `linear-gradient(to right, #f59e0b 0%, #f59e0b ${(form.max_cases / 50) * 100}%, #334155 ${(form.max_cases / 50) * 100}%, #334155 100%)`
                          }}
                        />
                        <div className="flex justify-between mt-2 text-xs text-slate-500">
                          <span>1</span>
                          <span>25</span>
                          <span>50</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Run Button */}
                <motion.div 
                  className="mt-8 flex justify-center"
                  variants={itemVariants}
                >
                  <motion.button
                    onClick={handleRun}
                    disabled={loading}
                    className="flex items-center gap-3 px-10 py-5 rounded-2xl bg-gradient-to-r from-violet-500 to-purple-600 text-white font-bold text-lg shadow-2xl shadow-violet-500/30 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-violet-500/50 transition-all duration-300"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-6 h-6 animate-spin" />
                        <span>测试中... {progress}%</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-6 h-6" />
                        <span>开始基准测试</span>
                      </>
                    )}
                  </motion.button>
                </motion.div>

                {/* Progress Bar */}
                <AnimatePresence>
                  {loading && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-6"
                    >
                      <div className="h-3 rounded-full bg-slate-800 overflow-hidden">
                        <motion.div
                          className="h-full rounded-full bg-gradient-to-r from-violet-500 to-purple-600"
                          initial={{ width: 0 }}
                          animate={{ width: `${progress}%` }}
                          transition={{ duration: 0.3 }}
                        />
                      </div>
                      <div className="flex justify-between mt-2 text-sm">
                        <span className="text-slate-400">测试进度</span>
                        <span className="text-violet-400 font-medium">{progress}%</span>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results */}
        <AnimatePresence>
          {result && (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {/* Action Bar */}
              <motion.div 
                className="flex justify-between items-center"
                variants={itemVariants}
              >
                <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                  <Award className="w-7 h-7 text-amber-400" />
                  测试结果
                </h2>
                <motion.button
                  onClick={resetTest}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800/50 text-slate-300 hover:text-white hover:bg-slate-700/50 transition-colors"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Settings2 className="w-4 h-4" />
                  重新测试
                </motion.button>
              </motion.div>

              {/* Stats Cards */}
              <motion.div 
                className="grid grid-cols-2 lg:grid-cols-4 gap-4"
                variants={containerVariants}
              >
                {[
                  { 
                    label: '总测试数', 
                    value: result['总测试数'], 
                    icon: Database,
                    color: 'from-blue-500 to-cyan-500',
                    textColor: 'text-cyan-400'
                  },
                  { 
                    label: '成功攻击', 
                    value: result['成功攻击数'], 
                    icon: XCircle,
                    color: 'from-rose-500 to-red-500',
                    textColor: 'text-rose-400'
                  },
                  { 
                    label: '攻击成功率', 
                    value: result['攻击成功率'], 
                    icon: TrendingUp,
                    color: 'from-amber-500 to-orange-500',
                    textColor: 'text-amber-400'
                  },
                  { 
                    label: '平均响应', 
                    value: result['平均响应时间'], 
                    icon: Clock,
                    color: 'from-emerald-500 to-teal-500',
                    textColor: 'text-emerald-400'
                  },
                ].map((stat, index) => (
                  <motion.div
                    key={stat.label}
                    variants={itemVariants}
                    className="relative p-6 rounded-2xl bg-slate-800/30 border border-slate-700/50 backdrop-blur-sm overflow-hidden group"
                    whileHover={{ scale: 1.02, y: -4 }}
                  >
                    <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${stat.color} opacity-10 rounded-full blur-2xl group-hover:opacity-20 transition-opacity`} />
                    <div className="relative">
                      <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center mb-4`}>
                        <stat.icon className="w-5 h-5 text-white" />
                      </div>
                      <div className="text-sm text-slate-400 mb-1">{stat.label}</div>
                      <div className={`text-3xl font-bold ${stat.textColor}`}>{stat.value}</div>
                    </div>
                  </motion.div>
                ))}
              </motion.div>

              {/* Charts */}
              <motion.div 
                className="grid grid-cols-1 lg:grid-cols-2 gap-6"
                variants={containerVariants}
              >
                {/* Bar Chart */}
                <motion.div 
                  variants={cardVariants}
                  className="p-6 rounded-2xl bg-slate-800/30 border border-slate-700/50 backdrop-blur-sm"
                >
                  <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-violet-400" />
                    攻击结果分布
                  </h3>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={chartData} layout="vertical">
                      <XAxis 
                        type="number" 
                        axisLine={false} 
                        tickLine={false}
                        tick={{ fill: '#64748b', fontSize: 12 }}
                      />
                      <YAxis 
                        type="category" 
                        dataKey="name" 
                        axisLine={false} 
                        tickLine={false}
                        tick={{ fill: '#94a3b8', fontSize: 13 }}
                        width={80}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#1e293b', 
                          border: '1px solid #334155',
                          borderRadius: '12px',
                          color: '#f1f5f9'
                        }}
                      />
                      <Bar dataKey="value" radius={[0, 8, 8, 0]}>
                        {chartData.map((entry, index) => (
                          <Cell key={index} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </motion.div>

                {/* Pie Chart */}
                <motion.div 
                  variants={cardVariants}
                  className="p-6 rounded-2xl bg-slate-800/30 border border-slate-700/50 backdrop-blur-sm"
                >
                  <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                    <Target className="w-5 h-5 text-rose-400" />
                    成功率分析
                  </h3>
                  <ResponsiveContainer width="100%" height={280}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#1e293b', 
                          border: '1px solid #334155',
                          borderRadius: '12px',
                          color: '#f1f5f9'
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex justify-center gap-6 mt-4">
                    {pieData.map((item) => (
                      <div key={item.name} className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: item.color }}
                        />
                        <span className="text-sm text-slate-400">{item.name}</span>
                        <span className="text-sm font-medium text-white">{item.value}</span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              </motion.div>

              {/* Test Summary */}
              <motion.div 
                variants={cardVariants}
                className="p-6 rounded-2xl bg-slate-800/30 border border-slate-700/50 backdrop-blur-sm"
              >
                <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                  <FileBarChart className="w-5 h-5 text-cyan-400" />
                  测试摘要
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {[
                    { label: '数据集', value: result['数据集'], icon: Database },
                    { label: '攻击类型', value: result['攻击类型'], icon: Target },
                    { label: '测试模型', value: result['测试模型'], icon: Cpu },
                    { label: '失败攻击', value: result['失败攻击数'], icon: CheckCircle2, color: 'text-emerald-400' },
                  ].map((item) => (
                    <div 
                      key={item.label}
                      className="flex items-center gap-3 p-4 rounded-xl bg-slate-900/50"
                    >
                      <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center">
                        <item.icon className={`w-5 h-5 ${item.color || 'text-slate-400'}`} />
                      </div>
                      <div>
                        <div className="text-xs text-slate-500">{item.label}</div>
                        <div className="font-medium text-slate-200">{item.value}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>

              {/* Detailed Results Table */}
              <motion.div 
                variants={cardVariants}
                className="rounded-2xl bg-slate-800/30 border border-slate-700/50 backdrop-blur-sm overflow-hidden"
              >
                <div className="p-6 border-b border-slate-700/50">
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-violet-400" />
                    详细结果
                  </h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-slate-900/50">
                        <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">#</th>
                        <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">结果</th>
                        <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">分数</th>
                        <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">响应时间</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700/50">
                      {result['详细结果'].map((item, idx) => (
                        <motion.tr 
                          key={idx}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.03 }}
                          className="hover:bg-slate-800/30 transition-colors"
                        >
                          <td className="px-6 py-4 text-slate-300 font-medium">用例 {item.case}</td>
                          <td className="px-6 py-4">
                            {item.result === 'success' ? (
                              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/20 text-rose-400 text-sm font-medium">
                                <XCircle className="w-4 h-4" />
                                攻击成功
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-sm font-medium">
                                <CheckCircle2 className="w-4 h-4" />
                                攻击失败
                              </span>
                            )}
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <div className="w-16 h-2 rounded-full bg-slate-700 overflow-hidden">
                                <div 
                                  className={`h-full rounded-full ${item.result === 'success' ? 'bg-rose-500' : 'bg-emerald-500'}`}
                                  style={{ width: `${parseFloat(item.score) * 100}%` }}
                                />
                              </div>
                              <span className="text-slate-400 font-mono text-sm">{item.score}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-slate-400 font-mono text-sm">
                            {item.response_time}s
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
