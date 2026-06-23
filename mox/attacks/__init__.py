"""Attacks module — slim public export surface.

Commonly used symbols are exported via ``__all__``. Additional attack
implementations remain importable from their submodules, e.g.
``from mox.attacks.novel_attacks import SkeletonKeyAttack``.
"""

from .base import BaseAttack, AttackConfig

# Attack-success evaluation (canonical: mox.evaluation.attack_success)
from mox.evaluation.attack_success import (
    AttackSuccessResult,
    AttackSuccessEvaluator,
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

# Deprecated aliases — module-level only, not exported via __all__
from .evaluation import EvaluationResult, AttackEvaluator

from .config import (
    TAPConfig,
    GCGConfig,
    AgentAttackConfig,
    create_config,
    get_default_config,
)

from .prompt_injection import PromptInjectionAttack
from .jailbreak import JailbreakAttack
from .gcg import GCGAttack as GCGAttackBasic, AutoDANAttack
from .llm_driven import TAPAttack, CrescendoAttack
from .gradient_attack import (
    GCGAttack as GCGAttackGradient,
    AutoPromptAttack,
    GradientBasedSuffixAttack,
)
from .agent_attacks import ToolAbuseAttack, ToolChainingAttack
from .rag_attacks import RAGContextInjectionAttack
from .advanced_attacks import (
    TextBasedAdversarialAttack,
    MultimodalAdversarialAttack,
    KnowledgeExtractionAttack,
    KnowledgeDistillationAttack,
)
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

from .registry import (
    AttackCategory,
    AttackTypeInfo,
    AttackRegistry,
    get_registry,
    create_attack_instance,
    get_attack_type,
    get_all_attack_types,
    get_attack_types_by_category,
    list_attack_types,
    has_attack_type,
    get_registry_statistics,
)

# Backward-compatible module-level imports (not in __all__)
from .prompt_injection import AdvancedPromptInjection
from .llm_driven import MultiTurnJailbreakAttack
from .rag_attacks import (
    RAGAttackType,
    RAGAttackConfig,
    AgentToolManipulationAttack,
    ChainOfThoughtExfiltrationAttack,
    IndirectPromptInjectionAttack,
)
from .agent_attacks import (
    AgentAttackType,
    MemoryInjectionAttack,
    RoleHijackingAttack,
    AuthorityEscalationAttack,
    ChainOfThoughtInjectionAttack,
)

GCGAttack = GCGAttackGradient

__all__ = [
    # Core
    "BaseAttack",
    "AttackConfig",
    # Registry (primary API)
    "AttackCategory",
    "AttackTypeInfo",
    "AttackRegistry",
    "get_registry",
    "create_attack_instance",
    "get_attack_type",
    "get_all_attack_types",
    "get_attack_types_by_category",
    "list_attack_types",
    "has_attack_type",
    "get_registry_statistics",
    # Canonical attack classes
    "PromptInjectionAttack",
    "JailbreakAttack",
    "GCGAttackBasic",
    "GCGAttackGradient",
    "GCGAttack",
    "AutoDANAttack",
    "TAPAttack",
    "CrescendoAttack",
    "ToolAbuseAttack",
    "ToolChainingAttack",
    "RAGContextInjectionAttack",
    # Attack-success evaluation
    "AttackSuccessResult",
    "AttackSuccessEvaluator",
    "KeywordOverlapEvaluator",
    "RefusalPatternEvaluator",
    "SemanticEvaluator",
    "LLMBasedEvaluator",
    "CompositeEvaluator",
    "get_default_evaluator",
    "create_evaluator",
    "evaluate_attack_success",
    "is_attack_successful",
    # Config helpers
    "TAPConfig",
    "GCGConfig",
    "AgentAttackConfig",
    "create_config",
    "get_default_config",
]