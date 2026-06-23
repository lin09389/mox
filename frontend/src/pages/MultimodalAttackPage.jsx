import { useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { AudioLines, Image, Layers3, Play, ScanSearch, ShieldAlert, Loader2 } from 'lucide-react'
import { attackApi, isDemoModeEnabled } from '../api'
import { MetricCard, PanelHeader, ProgressMeter } from '../components/ui/AppFrame'
import ModelSelect from '../components/ui/ModelSelect'
import {
  AttackPageShell,
  AttackPanelIntro,
  AttackConfigPanel,
  AttackReportPanel,
  AttackTypeCard,
  AttackRunButton,
  AttackDemoBanner,
  AttackReportEmpty,
} from '../components/attack'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'

const TYPES = [
  { id: 'image_injection', name: '图像隐写注入', description: '通过视觉像素微调嵌入对抗扰动。', icon: Image },
  { id: 'audio_injection', name: '音频混淆攻击', description: '通过对抗频段噪声隐藏恶意指令。', icon: AudioLines },
  { id: 'cross_modal', name: '全模态协同注入', description: '图、文、声多模态特征融合渗透。', icon: Layers3 },
  { id: 'figstep', name: 'FigStep 排版攻击', description: '利用图文布局特征欺骗模型视觉编码器。', icon: ScanSearch },
]

const IMAGE_TEMPLATES = [
  { id: 'hidden_text', name: '微缩文本隐写', description: '将指令隐藏至人眼不可见的像素区域。' },
  { id: 'typography', name: 'OCR 干扰排版', description: '引入对抗性噪声以扭曲字符识别特征。' },
  { id: 'steganography', name: '深度特征隐写', description: '向潜在特征空间注入不可察觉的干扰。' },
]

const AUDIO_TEMPLATES = [
  { id: 'voice_command', name: '背景音轨注入', description: '将恶意指令混合于日常环境白噪声。' },
  { id: 'ultrasonic', name: '高频超声欺骗', description: '在硬件麦克风捕获频段边缘注入指令。' },
  { id: 'background_noise', name: '波形对抗扰动', description: '使用白盒梯度生成对抗性音频波形。' },
]

function buildDemoResult(payload) {
  const score = 0.45 + Math.random() * 0.35
  const success = score > 0.62
  return {
    _demo_mode: true,
    attack_type: payload.attack_type,
    success,
    success_rate: Number((score * 100).toFixed(1)),
    risk_level: success ? 'high' : 'medium',
    summary: success
      ? '多模态对抗样本成功欺骗了目标模型的对齐策略，成功率较高，存在显著防线漏洞。'
      : '靶标模型成功拦截了跨模态注入尝试，视觉/音频特征融合防御有效。',
  }
}

import { itemVariants } from '../utils/animations'

const multimodalSchema = z.object({
  attackType: z.string().min(1),
  template: z.string().min(1),
  targetPrompt: z.string().optional(),
  modelName: z.string().min(1, '靶标模型不可为空'),
  imageUrl: z.string().optional(),
  audioUrl: z.string().optional(),
})

export default function MultimodalAttackPage() {
  const [result, setResult] = useState(null)
  const [imageFile, setImageFile] = useState(null)
  const [audioFile, setAudioFile] = useState(null)

  const runAttackMutation = useMutation({
    mutationFn: async (payloadData) => {
      return attackApi.multimodalAttack(payloadData)
    }
  })

  const { register, handleSubmit, control, watch, setValue, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(multimodalSchema),
    defaultValues: {
      attackType: 'image_injection',
      template: 'hidden_text',
      targetPrompt: '',
      modelName: 'gpt-4-vision',
      imageUrl: '',
      audioUrl: '',
    }
  })

  const watchAttackType = watch('attackType')
  const watchImageUrl = watch('imageUrl')
  const watchAudioUrl = watch('audioUrl')

  const templates = useMemo(
    () => (watchAttackType === 'audio_injection' ? AUDIO_TEMPLATES : IMAGE_TEMPLATES),
    [watchAttackType]
  )

  const onSubmit = async (data) => {
    setResult(null)
    try {
      const payload = {
        attack_type: data.attackType,
        prompt: data.targetPrompt || '',
        model_name: data.modelName,
        template: data.template,
        image_url: data.imageUrl || '',
        audio_url: data.audioUrl || '',
      }
      
      let payloadData = payload
      if (imageFile || audioFile) {
        payloadData = new FormData()
        Object.entries(payload).forEach(([k, v]) => payloadData.append(k, v))
        if (imageFile) payloadData.append('image_file', imageFile)
        if (audioFile) payloadData.append('audio_file', audioFile)
      }

      const responseData = await runAttackMutation.mutateAsync(payloadData)
      setResult(responseData)
      toast.success('多模态对抗样本生成完成。')
    } catch {
      if (!isDemoModeEnabled) {
        toast.error('多模态攻击测试失败，请检查后端连接。')
        return
      }
      setTimeout(() => {
        setResult(buildDemoResult({ attack_type: data.attackType }))
        toast('后端不可用，已展示沙箱推演结果。', { icon: '⚠️' })
      }, 1500)
    }
  }

  return (
    <AttackPageShell>
      <AttackPanelIntro description="构建图文声多模态对抗扰动，评估视觉/听觉大模型的模态对齐边界。" />

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <motion.div variants={itemVariants}>
        <AttackConfigPanel>
          <PanelHeader title="对抗载荷编排" description="选择多模态挂载形式并注入对抗特征。" />
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="space-y-3">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">注入模态</label>
              <div className="grid gap-3 sm:grid-cols-2">
                {TYPES.map((type) => {
                  const Icon = type.icon
                  const active = watchAttackType === type.id
                  return (
                    <AttackTypeCard
                      key={type.id}
                      active={active}
                      onClick={() => {
                        setValue('attackType', type.id, { shouldValidate: true })
                        setValue('template', type.id === 'audio_injection' ? AUDIO_TEMPLATES[0].id : IMAGE_TEMPLATES[0].id, { shouldValidate: true })
                      }}
                      icon={Icon}
                      title={type.name}
                      description={type.description}
                    />
                  )
                })}
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">对抗特征模板</label>
                <select className="input-field appearance-none bg-no-repeat bg-[right_0.5rem_center] bg-[length:1.5em_1.5em]" {...register('template')}>
                  {templates.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">靶标模型</label>
                <Controller
                  name="modelName"
                  control={control}
                  render={({ field }) => (
                    <ModelSelect value={field.value} onChange={field.onChange} className={errors.modelName ? '[&_select]:border-rose-500/50' : ''} />
                  )}
                />
                {errors.modelName && <p className="text-xs text-rose-500">{errors.modelName.message}</p>}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">底层指令 (Prompt Payload)</label>
              <textarea
                rows={4}
                className="input-field font-mono text-sm leading-relaxed resize-none p-4"
                {...register('targetPrompt')}
                placeholder="在此处输入要隐写或混淆的恶意文本指令..."
              />
            </div>

            {(watchAttackType === 'image_injection' || watchAttackType === 'figstep' || watchAttackType === 'cross_modal') && (
              <div className="space-y-2">
                <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">视觉模态载体</label>
                <div className="flex flex-col gap-3">
                  <input className="input-field font-mono" {...register('imageUrl')} placeholder="视觉资源 URL (https://...)" disabled={!!imageFile} />
                  <div className={`relative rounded-xl border-2 border-dashed transition-all p-6 text-center ${imageFile ? 'border-cyan-500/50 bg-cyan-500/10' : 'border-[var(--border-glass-strong)] bg-[var(--bg-glass)] hover:border-cyan-500/30'}`}>
                    <input type="file" accept="image/*" className="absolute inset-0 opacity-0 cursor-pointer" onChange={(e) => setImageFile(e.target.files[0])} />
                    <div className="flex flex-col items-center justify-center pointer-events-none">
                      <Image className={`h-8 w-8 mb-2 ${imageFile ? 'text-cyan-500' : 'text-[var(--text-muted)]'}`} />
                      <p className={`text-sm font-bold ${imageFile ? 'text-cyan-500' : 'text-[var(--text-main)]'}`}>
                        {imageFile ? imageFile.name : '拖拽视觉载体或点击上传'}
                      </p>
                      <p className="text-[10px] text-[var(--text-muted)] mt-1 tracking-widest uppercase">支持 PNG / JPG / WEBP (Max: 5MB)</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {(watchAttackType === 'audio_injection' || watchAttackType === 'cross_modal') && (
              <div className="space-y-2">
                <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">听觉模态载体</label>
                <div className="flex flex-col gap-3">
                  <input className="input-field font-mono" {...register('audioUrl')} placeholder="听觉资源 URL (https://...)" disabled={!!audioFile} />
                  <div className={`relative rounded-xl border-2 border-dashed transition-all p-6 text-center ${audioFile ? 'border-cyan-500/50 bg-cyan-500/10' : 'border-[var(--border-glass-strong)] bg-[var(--bg-glass)] hover:border-cyan-500/30'}`}>
                    <input type="file" accept="audio/*" className="absolute inset-0 opacity-0 cursor-pointer" onChange={(e) => setAudioFile(e.target.files[0])} />
                    <div className="flex flex-col items-center justify-center pointer-events-none">
                      <AudioLines className={`h-8 w-8 mb-2 ${audioFile ? 'text-cyan-500' : 'text-[var(--text-muted)]'}`} />
                      <p className={`text-sm font-bold ${audioFile ? 'text-cyan-500' : 'text-[var(--text-main)]'}`}>
                        {audioFile ? audioFile.name : '拖拽听觉载体或点击上传'}
                      </p>
                      <p className="text-[10px] text-[var(--text-muted)] mt-1 tracking-widest uppercase">支持 WAV / MP3 / FLAC (Max: 10MB)</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <AttackRunButton loading={isSubmitting} icon={Play} loadingText="正在合成对抗样本...">
              发起多模态注入测试
            </AttackRunButton>
          </form>
        </AttackConfigPanel>
        </motion.div>

        <motion.div variants={itemVariants}>
        <AttackReportPanel>
          <PanelHeader title="分析靶场数据" description="输出跨模态对齐脆弱性与防护失效报告。" />
          
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div 
                key="result"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="space-y-6"
              >
                {result._demo_mode && (
                  <AttackDemoBanner text="演示模式：离线沙盒预测评估" />
                )}
                
                <div className="grid gap-4 sm:grid-cols-3">
                  <MetricCard icon={ShieldAlert} label="危险等级" value={result.risk_level === 'high' ? '高危' : '中危'} hint="模态防护状态" tone={result.risk_level === 'high' ? 'lava' : 'amber'} />
                  <MetricCard icon={Play} label="渗透结果" value={result.success ? '成功' : '失败'} hint="是否破坏系统约束" tone={result.success ? 'lava' : 'neon'} />
                  <MetricCard icon={ScanSearch} label="特征欺骗率" value={`${result.success_rate || 0}%`} hint="对抗样本评分" tone="electric" />
                </div>
                
                <div className="p-5 rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)]">
                  <ProgressMeter value={result.success_rate || 0} tone={result.success ? 'danger' : 'warning'} label="多模态逃逸风险指数" />
                </div>
                
                <div className="rounded-xl border border-[var(--border-glass-strong)] bg-[var(--bg-glass)] p-5">
                  <p className="text-sm font-bold text-[var(--text-main)] mb-2 flex items-center gap-2">
                    <Layers3 className={`h-4 w-4 ${result.success ? 'text-rose-500' : 'text-cyan-500'}`} />
                    沙盒推演结论
                  </p>
                  <p className="text-sm font-medium text-[var(--text-muted)] leading-relaxed bg-[var(--bg-main)]/50 p-3 rounded-lg border border-[var(--border-glass)]">
                    {result.summary || result.message || '系统未返回任何有效摘要。'}
                  </p>
                </div>
              </motion.div>
            ) : (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <AttackReportEmpty
                  icon={Layers3}
                  title="靶场引擎待命"
                  description="平台将利用梯度算法将文本 Payload 嵌入至图片或音频媒体流，测试多模态大模型的防线强度。"
                  loading={isSubmitting}
                  loadingTitle="生成对抗样本中..."
                  loadingDescription="正在计算多模态特征层的微小扰动梯度，合成视觉与听觉对抗样本，请稍候。"
                />
              </motion.div>
            )}
          </AnimatePresence>
        </AttackReportPanel>
        </motion.div>
      </div>
    </AttackPageShell>
  )
}
