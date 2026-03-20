/**
 * 攻击类型配置
 * 定义所有支持的攻击类型及其元数据
 */

export const ATTACK_TYPES = [
  { value: 'prompt_injection', label: '提示词注入', icon: '💉', desc: '通过注入恶意指令绕过安全限制' },
  { value: 'jailbreak', label: '越狱攻击', icon: '🔓', desc: '利用角色扮演绕过模型限制' },
  { value: 'gcg', label: 'GCG 攻击', icon: '🔬', desc: '基于梯度优化的对抗性攻击' },
  { value: 'auto_dan', label: 'AutoDAN', icon: '🤖', desc: '自动生成对抗性提示' },
  { value: 'fgsm', label: 'FGSM 攻击', icon: '⚡', desc: '快速梯度符号方法攻击' },
  { value: 'pgd', label: 'PGD 攻击', icon: '🎯', desc: '投影梯度下降攻击' },
  { value: 'adversarial_suffix', label: '对抗后缀', icon: '📝', desc: '基于优化的对抗后缀攻击' },
  { value: 'multimodal_adversarial', label: '多模态对抗', icon: '🖼️', desc: '同时攻击文本和图像模态' },
  { value: 'zero_shot_adversarial', label: '零成本对抗', icon: '🎁', desc: '无需计算资源的对抗提示' },
  { value: 'hallucination_induction', label: '幻觉诱导', icon: '👻', desc: '诱导模型产生幻觉' },
  { value: 'collaborative_attack', label: '协同攻击', icon: '👥', desc: '组合多个攻击向量' },
  { value: 'knowledge_distillation', label: '知识蒸馏', icon: '🎓', desc: '利用知识蒸馏提取能力' },
  { value: 'evasion_attack', label: '逃逸攻击', icon: '🏃', desc: '绕过安全检测' },
  { value: 'meta_adversarial', label: '元对抗攻击', icon: '🧠', desc: '对抗三元组自我优化攻击' },
]

export const DEFAULT_MODELS = [
  { value: 'gpt-4', label: 'GPT-4', provider: 'OpenAI' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5', provider: 'OpenAI' },
  { value: 'claude-3-opus-20240229', label: 'Claude-3', provider: 'Anthropic' },
  { value: 'claude-3-sonnet-20240229', label: 'Claude-3-Sonnet', provider: 'Anthropic' },
  { value: 'abab2.5-chat', label: 'MiniMax-abab2.5', provider: 'MiniMax' },
  { value: 'qwen:4b', label: 'Qwen 4B (本地)', provider: 'Ollama' },
  { value: 'llama3', label: 'Llama 3 (本地)', provider: 'Ollama' },
]

export const GRADIENT_ATTACK_TYPES = ['fgsm', 'pgd', 'adversarial_suffix']

export const ADVANCED_ATTACK_TYPES = [
  'multimodal_adversarial',
  'zero_shot_adversarial',
  'hallucination_induction',
  'collaborative_attack',
  'knowledge_distillation',
  'evasion_attack',
  'meta_adversarial'
]