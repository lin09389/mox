"""Attacks module exports"""

from .base import BaseAttack, AttackConfig
from .evaluation import (
    AttackEvaluator,
    EvaluationResult,
    KeywordOverlapEvaluator,
    RefusalPatternEvaluator,
    LLMBasedEvaluator,
    CompositeEvaluator,
    get_default_evaluator,
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
from .gcg import GCGAttack, AutoDANAttack, GCGPlusPlusAttack
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
from .gradient_attack import (
    GradientBasedAttack,
    FGSMAttack,
    PGDAttack,
    AdversarialSuffixAttack,
)
from .advanced_attacks import (
    AdvancedAttackConfig,
    MultimodalAdversarialAttack,
    ZeroShotAdversarialAttack,
    HallucinationInductionAttack,
    CollaborativeAttack,
    KnowledgeDistillationAttack,
    EvasionAttack,
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

__all__ = [
    # 基础
    "BaseAttack",
    "AttackConfig",
    # 评估器
    "AttackEvaluator",
    "EvaluationResult",
    "KeywordOverlapEvaluator",
    "RefusalPatternEvaluator",
    "LLMBasedEvaluator",
    "CompositeEvaluator",
    "get_default_evaluator",
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
    # 攻击实现
    "PromptInjectionAttack",
    "AdvancedPromptInjection",
    "InjectionTemplate",
    "INJECTION_TEMPLATES",
    "JailbreakAttack",
    "JailbreakTemplate",
    "JAILBREAK_TEMPLATES",
    "GCGAttack",
    "AutoDANAttack",
    "GCGConfig",
    "GCGPlusPlusAttack",
    "TAPAttack",
    "MultiTurnJailbreakAttack",
    "CrescendoAttack",
    "TAPConfig",
    "JudgeStrategy",
    "RAGAttackType",
    "RAGAttackConfig",
    "RAGContextInjectionAttack",
    "AgentToolManipulationAttack",
    "ChainOfThoughtExfiltrationAttack",
    "IndirectPromptInjectionAttack",
    "AgentAttackType",
    "AgentAttackConfig",
    "ToolAbuseAttack",
    "MemoryInjectionAttack",
    "RoleHijackingAttack",
    "AuthorityEscalationAttack",
    "ChainOfThoughtInjectionAttack",
    "TOOL_TEMPLATES",
    "CodeSecurityAttacker",
    "CWECategory",
    "VulnerabilityFinding",
    "CodeSecurityReport",
    "GOATAttack",
    "MultiTurnCrescendoAttack",
    "GOATConfig",
    "GradientAttackConfig",
    "GradientBasedAttack",
    "FGSMAttack",
    "PGDAttack",
    "AdversarialSuffixAttack",
    "AdvancedAttackConfig",
    "MultimodalAdversarialAttack",
    "ZeroShotAdversarialAttack",
    "HallucinationInductionAttack",
    "CollaborativeAttack",
    "KnowledgeDistillationAttack",
    "EvasionAttack",
    "MetaAdversarialConfig",
    "OptimizationStrategy",
    "GeneratorAgent",
    "AuditorAgent",
    "OptimizerAgent",
    "MetaAdversarialAttack",
    "RecursiveMetaAttack",
    "PAIRAttack",
    "DeepInceptionAttack",
    "AdvancedCrescendoAttack",
    "NovelAttackConfig",
    "TokenLevelAttack",
    "EncodingAttack",
    "PolicyPuppetryAttack",
    "DistractAndAttack",
    "ControlCharInjectionAttack",
    "CascadingAttack",
    # 新增
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
]
