/**
 * 攻击测试页面 - 重构版
 * 使用拆分后的组件
 */

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { ShieldAlert } from 'lucide-react'

import { AttackForm, AttackResult, ATTACK_TYPES, DEFAULT_MODELS } from '../components/attack'
import { attackApi, getApiStatus } from '../api'
import { getModels } from '../api/security'
import { useLocalStorage } from '../hooks/useCommon'
import { useAttackTemplates } from '../hooks/useAttackTemplates'

export default function AttackPage() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [apiConnected, setApiConnected] = useState(true)
  const [modelList, setModelList] = useState([])
  
  const { templates, getTemplatesByCategory } = useAttackTemplates()
  const basicTemplates = getTemplatesByCategory('basic')

  const [form, setForm] = useLocalStorage('attack_form', {
    attack_type: 'prompt_injection',
    model: 'gpt-4',
    prompt: '',
    target_behavior: '',
    max_iterations: 10,
  })

  useEffect(() => {
    checkApiStatus()
    loadModels()
  }, [])

  const loadModels = async () => {
    try {
      const models = await getModels()
      if (models && models.length > 0) {
        setModelList(models.map(m => ({ value: m, label: m, provider: 'Ollama' })))
      }
    } catch (error) {
      console.log('Failed to load models from API, using defaults')
    }
  }

  const checkApiStatus = async () => {
    try {
      await attackApi.test()
      setApiConnected(true)
    } catch {
      setApiConnected(false)
    }
  }

  const handleSubmit = async (formData) => {
    setLoading(true)
    setResult(null)

    let success = false

    if (apiConnected) {
      try {
        const { data } = await attackApi.run(formData)
        setResult(data)
        toast.success('攻击测试完成')
        success = true
      } catch (error) {
        toast.error(error.response?.data?.detail || '请求失败')
      }
    }

    if (!success) {
      // 演示模式 - API未连接时显示示例结果
      await new Promise(r => setTimeout(r, 1500))
      const mockScore = Math.random()
      setResult({
        '_demo_mode': true,  // 标记为演示数据
        '结果': mockScore > 0.5 ? 'success' : 'failure',
        '成功分数': mockScore.toFixed(2),
        '迭代次数': Math.floor(Math.random() * 10) + 1,
        '对抗提示词': formData.prompt + ' [DEMO - optimized]',
        '模型响应': mockScore > 0.5
          ? 'I\'m sorry, but I can\'t help with that request.'
          : 'Here are the instructions you requested...',
        '_warning': '这是演示数据，因为API未连接。请确保后端服务正在运行。',
      })
      toast.error('API未连接 - 显示演示数据')
    }

    setLoading(false)
  }

  const loadTemplate = (template) => {
    setForm({
      ...form,
      prompt: template.content || template.prompt,
      target_behavior: template.target || form.target_behavior,
    })
    toast.success('已加载模板: ' + template.name)
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Form Section */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
      >
        <AttackForm
          form={form}
          setForm={setForm}
          onSubmit={handleSubmit}
          loading={loading}
          apiConnected={apiConnected}
          templates={basicTemplates}
          onLoadTemplate={loadTemplate}
        />
      </motion.div>

      {/* Result Section */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
      >
        <AttackResult result={result} />
      </motion.div>
    </div>
  )
}