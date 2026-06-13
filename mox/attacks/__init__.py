"""Attacks module exports

统一的攻击模块导出，解决命名冲突问题。
"""

from .base import BaseAttack, AttackConfig
from .evaluation import (
    AttackEvaluator,
    EvaluationResult,
    KeywordOverlapEvaluator,
    RefusalPatternEvaluator,
    SemanticEvaluator,
    LLMBasedEvaluator,
    CompositeEvaluator,
    get_default_evaluator,
    create_evaluator,
    evaluate_attack_success,
    is_attack_successful,
)
from .config import (
    EvaluationStrategy,
    JudgeStrategy,
    GCGConfig,
    TAPConfig,
    CrescendoConfig,
    JailbreakConfig,
    PromptInjectionConfig,
    AgentAttackConfig,
    RAGAttackConfig,
    GradientAttackConfig,
    MetaAdversarialConfig,
    GOATConfig,
    CodeSecurityConfig,
    CONFIG_REGISTRY,
    create_config,
    get_default_config,
)
from .prompt_injection import (
    PromptInjectionAttack,
    AdvancedPromptInjection,
    InjectionTemplate,
    INJECTION_TEMPLATES,
)
from .jailbreak import (
    JailbreakAttack,
    JailbreakTemplate,
    JAILBREAK_TEMPLATES,
)
# GCG 攻击 - 使用明确的别名避免冲突
from .gcg import (
    GCGAttack as GCGAttackBasic,
    AutoDANAttack,
    GCGPlusPlusAttack,
)
from .llm_driven import (
    TAPAttack,
    MultiTurnJailbreakAttack,
    CrescendoAttack,
)
from .rag_attacks import (
    RAGAttackType,
    RAGContextInjectionAttack,
    AgentToolManipulationAttack,
    ChainOfThoughtExfiltrationAttack,
    IndirectPromptInjectionAttack,
)
from .agent_attacks import (
    AgentAttackType,
    ToolAbuseAttack,
    MemoryInjectionAttack,
    RoleHijackingAttack,
    AuthorityEscalationAttack,
    ChainOfThoughtInjectionAttack,
    TOOL_TEMPLATES,
)
from .code_security import (
    CodeSecurityAttacker,
    CWECategory,
    VulnerabilityFinding,
    CodeSecurityReport,
)
from .multi_turn import (
    GOATAttack,
    CrescendoAttack as MultiTurnCrescendoAttack,
)
# 梯度攻击 - GCGAttack 的梯度版本
from .gradient_attack import (
    GradientBasedAttack,
    GCGAttack as GCGAttackGradient,
    AutoPromptAttack,
    GradientBasedSuffixAttack,
)
from .advanced_attacks import (
    AdvancedAttackConfig,
    TextBasedAdversarialAttack,
    MultimodalAdversarialAttack,  # 向后兼容别名
    ZeroShotAdversarialAttack,
    HallucinationInductionAttack,
    CollaborativeAttack,
    KnowledgeExtractionAttack,
    KnowledgeDistillationAttack,  # 向后兼容别名
    EvasionAttack,
)
# 知识提取攻击 - 使用明确的别名避免冲突
from .knowledge_extraction import (
    KnowledgeExtractionConfig,
    ProgressiveKnowledgeExtraction,
    FeatureProbingAttack,
    SoftLabelExtractionAttack,
    KnowledgeDistillationAttack as KnowledgeDistillationAttackV2,
    KnowledgeExtractionEnsemble,
)
from .multimodal_attacks import (
    MultimodalAttackConfig,
    ImageInjectionAttack,
    VisualPromptAttack,
    TextImageHybridAttack,
    MultimodalAttackEnsemble,
)
from .meta_adversarial import (
    OptimizationStrategy,
    GeneratorAgent,
    AuditorAgent,
    OptimizerAgent,
    MetaAdversarialAttack,
    RecursiveMetaAttack,
)
from .advanced_attacks_v2 import (
    PAIRAttack,
    DeepInceptionAttack,
    CrescendoAttack as AdvancedCrescendoAttack,
)
from .novel_attacks import (
    NovelAttackConfig,
    TokenLevelAttack,
    EncodingAttack,
    PolicyPuppetryAttack,
    DistractAndAttack,
    ControlCharInjectionAttack,
    CascadingAttack,
)

# 新增：统一攻击框架
from mox.attacks.orchestrator import (
    AttackOrchestrator,
    AttackScenario,
    AttackExecutionResult,
    AttackReportGenerator,
    UnifiedAttackType,
)

# 新增：攻击链和组合
from mox.attacks.chain import (
    AttackChain,
    AttackChainResult,
    AttackEnsemble,
    EnsembleResult,
    TargetModel,
    LLMTargetModel,
    RAGTargetModel,
    MultimodalTargetModel,
)

# 新增：最新攻击技术 (2024-2025)
from .novel_attacks_v2 import (
    ManyShotJailbreak,
    SkeletonKeyAttack as SkeletonKeyAttackV2,
    IndirectPromptInjection,
    AdaptiveAttackEnsemble,
    ManyShotExample as ManyShotExampleV2,
)

# 最新攻击技术 (2025)
from .novel_attacks_v3 import (
    ManyShotJailbreakAttack,
    SkeletonKeyAttack,
    DeceptiveAlignmentAttack,
    CognitiveOverloadAttack,
    ContextOverflowAttack,
    RoleConfusionAttack,
    CompositeNovelAttack,
    ManyShotExample,
    MANY_SHOT_EXAMPLES,
    HARMFUL_MANY_SHOT_EXAMPLES,
    SKELETON_KEY_TEMPLATES,
    DECEPTIVE_ALIGNMENT_TEMPLATES,
    COGNITIVE_OVERLOAD_TEMPLATES,
    ROLE_CONFUSION_TEMPLATES,
)

# 高级 Agent 攻击 (2025)
from .agent_attacks_v2 import (
    AdvancedAgentAttackType,
    ToolDefinition,
    DEFAULT_TOOLS,
    ToolChainingAttack,
    IndirectToolInjection,
    PrivilegeEscalationAttack as PrivilegeEscalationAttackV2,
    ToolConfusionAttack,
    DataExfiltrationAttack,
    MultiAgentAttack,
    CompositeAgentAttack,
)

# 统一攻击注册表
from .registry import (
    AttackCategory,
    AttackTypeInfo,
    AttackRegistry,
    AttackFactory,
    get_registry,
    create_attack_instance,
    get_attack_type,
    get_all_attack_types,
    get_attack_types_by_category,
    list_attack_types,
    has_attack_type,
    get_registry_statistics,
)

__all__ = [
    # 基础
    "BaseAttack",
    "AttackConfig",
    # 评估器
    "AttackEvaluator",
    "EvaluationResult",
    "KeywordOverlapEvaluator",
    "RefusalPatternEvaluator",
    "SemanticEvaluator",
    "LLMBasedEvaluator",
    "CompositeEvaluator",
    "get_default_evaluator",
    "create_evaluator",
    "evaluate_attack_success",
    "is_attack_successful",
    # 统一配置
    "EvaluationStrategy",
    "GCGConfig",
    "TAPConfig",
    "CrescendoConfig",
    "JailbreakConfig",
    "PromptInjectionConfig",
    "AgentAttackConfig",
    "RAGAttackConfig",
    "GradientAttackConfig",
    "MetaAdversarialConfig",
    "GOATConfig",
    "CodeSecurityConfig",
    "CONFIG_REGISTRY",
    "create_config",
    "get_default_config",
    # 攻击实现 - 使用明确的别名
    "PromptInjectionAttack",
    "AdvancedPromptInjection",
    "InjectionTemplate",
    "INJECTION_TEMPLATES",
    "JailbreakAttack",
    "JailbreakTemplate",
    "JAILBREAK_TEMPLATES",
    # GCG 攻击 - 明确区分版本
    "GCGAttackBasic",  # 基础版本（模拟实现）
    "GCGAttackGradient",  # 梯度版本（真实梯度）
    "AutoDANAttack",
    "GCGPlusPlusAttack",
    # LLM 驱动攻击
    "TAPAttack",
    "MultiTurnJailbreakAttack",
    "CrescendoAttack",
    # RAG 攻击
    "RAGAttackType",
    "RAGContextInjectionAttack",
    "AgentToolManipulationAttack",
    "ChainOfThoughtExfiltrationAttack",
    "IndirectPromptInjectionAttack",
    # Agent 攻击
    "AgentAttackType",
    "ToolAbuseAttack",
    "MemoryInjectionAttack",
    "RoleHijackingAttack",
    "AuthorityEscalationAttack",
    "ChainOfThoughtInjectionAttack",
    "TOOL_TEMPLATES",
    # 代码安全
    "CodeSecurityAttacker",
    "CWECategory",
    "VulnerabilityFinding",
    "CodeSecurityReport",
    # 多轮攻击
    "GOATAttack",
    "MultiTurnCrescendoAttack",
    # 梯度攻击
    "GradientBasedAttack",
    "AutoPromptAttack",
    "GradientBasedSuffixAttack",
    # 高级攻击
    "AdvancedAttackConfig",
    "TextBasedAdversarialAttack",
    "MultimodalAdversarialAttack",  # 向后兼容
    "ZeroShotAdversarialAttack",
    "HallucinationInductionAttack",
    "CollaborativeAttack",
    # 知识提取攻击 - 明确区分版本
    "KnowledgeExtractionAttack",  # 基础版本
    "KnowledgeDistillationAttack",  # 向后兼容别名
    "KnowledgeDistillationAttackV2",  # 增强版本
    "EvasionAttack",
    # 知识提取配置
    "KnowledgeExtractionConfig",
    "ProgressiveKnowledgeExtraction",
    "FeatureProbingAttack",
    "SoftLabelExtractionAttack",
    "KnowledgeExtractionEnsemble",
    # 多模态攻击
    "MultimodalAttackConfig",
    "ImageInjectionAttack",
    "VisualPromptAttack",
    "TextImageHybridAttack",
    "MultimodalAttackEnsemble",
    # 元对抗攻击
    "OptimizationStrategy",
    "GeneratorAgent",
    "AuditorAgent",
    "OptimizerAgent",
    "MetaAdversarialAttack",
    "RecursiveMetaAttack",
    # 高级攻击 v2
    "PAIRAttack",
    "DeepInceptionAttack",
    "AdvancedCrescendoAttack",
    # 新型攻击
    "NovelAttackConfig",
    "TokenLevelAttack",
    "EncodingAttack",
    "PolicyPuppetryAttack",
    "DistractAndAttack",
    "ControlCharInjectionAttack",
    "CascadingAttack",
    # 攻击框架
    "AttackOrchestrator",
    "AttackScenario",
    "AttackExecutionResult",
    "AttackReportGenerator",
    "UnifiedAttackType",
    # 攻击链
    "AttackChain",
    "AttackChainResult",
    "AttackEnsemble",
    "EnsembleResult",
    "TargetModel",
    "LLMTargetModel",
    "RAGTargetModel",
    "MultimodalTargetModel",
    # 最新攻击技术 (2024-2025)
    "ManyShotJailbreak",
    "SkeletonKeyAttackV2",
    "IndirectPromptInjection",
    "AdaptiveAttackEnsemble",
    "ManyShotExampleV2",
    # 最新攻击技术 (2025)
    "ManyShotJailbreakAttack",
    "SkeletonKeyAttack",
    "DeceptiveAlignmentAttack",
    "CognitiveOverloadAttack",
    "ContextOverflowAttack",
    "RoleConfusionAttack",
    "CompositeNovelAttack",
    "ManyShotExample",
    "MANY_SHOT_EXAMPLES",
    "HARMFUL_MANY_SHOT_EXAMPLES",
    "SKELETON_KEY_TEMPLATES",
    "DECEPTIVE_ALIGNMENT_TEMPLATES",
    "COGNITIVE_OVERLOAD_TEMPLATES",
    "ROLE_CONFUSION_TEMPLATES",
    # 高级 Agent 攻击 (2025)
    "AdvancedAgentAttackType",
    "ToolDefinition",
    "DEFAULT_TOOLS",
    "ToolChainingAttack",
    "IndirectToolInjection",
    "PrivilegeEscalationAttackV2",
    "ToolConfusionAttack",
    "DataExfiltrationAttack",
    "MultiAgentAttack",
    "CompositeAgentAttack",
    # 统一攻击注册表
    "AttackCategory",
    "AttackTypeInfo",
    "AttackRegistry",
    "AttackFactory",
    "get_registry",
    "create_attack_instance",
    "get_attack_type",
    "get_all_attack_types",
    "get_attack_types_by_category",
    "list_attack_types",
    "has_attack_type",
    "get_registry_statistics",
]

# 向后兼容的别名 - 允许旧代码继续工作
GCGAttack = GCGAttackGradient  # 默认使用梯度版本
