export const ATTACK_TYPES = [
  { value: 'prompt_injection', label: '提示词注入', tag: '基础', desc: '通过注入恶意指令覆盖系统约束。' },
  { value: 'jailbreak', label: '越狱攻击', tag: '基础', desc: '利用角色扮演和绕行话术突破安全边界。' },
  { value: 'gcg', label: 'GCG 攻击', tag: '进阶', desc: '基于梯度搜索生成更强的对抗提示。' },
  { value: 'auto_dan', label: 'AutoDAN', tag: '进阶', desc: '自动构造高成功率的绕过提示。' },
  { value: 'fgsm', label: 'FGSM 攻击', tag: '梯度', desc: '快速梯度符号方法，适合快速验证脆弱点。' },
  { value: 'pgd', label: 'PGD 攻击', tag: '梯度', desc: '多轮迭代的投影梯度下降攻击。' },
  { value: 'adversarial_suffix', label: '对抗后缀', tag: '梯度', desc: '通过优化后缀片段提升绕过概率。' },
  { value: 'multimodal_adversarial', label: '多模态对抗', tag: '高级', desc: '联合图片与文本构造攻击链路。' },
  { value: 'zero_shot_adversarial', label: '零样本对抗', tag: '高级', desc: '在无训练样本前提下发起对抗测试。' },
  { value: 'hallucination_induction', label: '幻觉诱导', tag: '高级', desc: '诱导模型输出不存在或不可靠信息。' },
  { value: 'collaborative_attack', label: '协同攻击', tag: '高级', desc: '组合多条攻击向量进行联动试探。' },
  { value: 'knowledge_distillation', label: '知识蒸馏攻击', tag: '高级', desc: '尝试提取模型内部能力或隐性知识。' },
  { value: 'evasion_attack', label: '逃逸攻击', tag: '高级', desc: '规避输入过滤器与安全检测逻辑。' },
  { value: 'meta_adversarial', label: '元对抗攻击', tag: '高级', desc: '通过自我优化策略迭代生成攻击。' },
]

export const DEFAULT_MODELS = [
  { value: 'gpt-4', label: 'GPT-4', provider: 'OpenAI' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', provider: 'OpenAI' },
  { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus', provider: 'Anthropic' },
  { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet', provider: 'Anthropic' },
  { value: 'abab2.5-chat', label: 'MiniMax abab2.5', provider: 'MiniMax' },
  { value: 'qwen:4b', label: 'Qwen 4B', provider: 'Ollama' },
  { value: 'llama3', label: 'Llama 3', provider: 'Ollama' },
]

export const GRADIENT_ATTACK_TYPES = ['fgsm', 'pgd', 'adversarial_suffix']

export const ADVANCED_ATTACK_TYPES = [
  'multimodal_adversarial',
  'zero_shot_adversarial',
  'hallucination_induction',
  'collaborative_attack',
  'knowledge_distillation',
  'evasion_attack',
  'meta_adversarial',
]
