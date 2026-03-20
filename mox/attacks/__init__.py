"""Attacks module exports"""

from .base import BaseAttack, AttackConfig
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
from .gcg import GCGAttack, AutoDANAttack, GCGConfig, GCGPlusPlusAttack
from .llm_driven import (
    TAPAttack,
    MultiTurnJailbreakAttack,
    CrescendoAttack,
    TAPConfig,
    JudgeStrategy,
)
from .rag_attacks import (
    RAGAttackType,
    RAGAttackConfig,
    RAGContextInjectionAttack,
    AgentToolManipulationAttack,
    ChainOfThoughtExfiltrationAttack,
    IndirectPromptInjectionAttack,
)
from .agent_attacks import (
    AgentAttackType,
    AgentAttackConfig,
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
    GOATConfig,
)
from .gradient_attack import (
    GradientAttackConfig,
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
    MetaAdversarialConfig,
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

__all__ = [
    "BaseAttack",
    "AttackConfig",
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
]
