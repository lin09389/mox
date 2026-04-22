"""Mox Attacks Module

Unified interface for all attack implementations.
Supports dynamic loading and registry-based instantiation.
"""

# 1. First, import everything we want to export
from .base import BaseAttack, AttackConfig
from .registry import ATTACK_REGISTRY, create_attack_instance
from .evaluation import AttackEvaluator, EvaluationResult, get_default_evaluator
from .config import CONFIG_REGISTRY, create_config, get_default_config, TAPConfig, JudgeStrategy

# 2. Explicitly import attack classes for backward compatibility
from .prompt_injection import PromptInjectionAttack, AdvancedPromptInjection
from .jailbreak import JailbreakAttack
from .gcg import GCGAttack, AutoDANAttack, GCGPlusPlusAttack
from .llm_driven import TAPAttack, MultiTurnJailbreakAttack, CrescendoAttack
from .novel_attacks import (
    NovelAttackConfig,
    ManyShotJailbreakAttack,
    SkeletonKeyAttack,
    TokenLevelAttack,
    EncodingAttack,
    PolicyPuppetryAttack,
    DeceptiveAlignmentAttack,
    DistractAndAttack,
    CognitiveOverloadAttack,
    ContextOverflowAttack,
    RoleConfusionAttack,
    ControlCharInjectionAttack,
    CompositeNovelAttack,
)
from .agent_attacks import (
    AgentAttackType,
    AgentAttackConfig,
    ToolAbuseAttack,
    MemoryInjectionAttack,
    RoleHijackingAttack,
    ToolChainingAttack,
    IndirectToolInjectionAttack,
    PrivilegeEscalationAttack,
    DataExfiltrationAttack,
    MultiAgentAttack,
    CompositeAgentAttack,
)
from .rag_attacks import (
    RAGAttackType,
    RAGAttackConfig,
    RAGContextInjectionAttack,
)

# 3. Aliases for backward compatibility
AgentToolManipulationAttack = ToolAbuseAttack
IndirectPromptInjectionAttack = IndirectToolInjectionAttack
AuthorityEscalationAttack = PrivilegeEscalationAttack
ChainOfThoughtInjectionAttack = RoleHijackingAttack
ChainOfThoughtExfiltrationAttack = DataExfiltrationAttack

# 4. Define __all__
__all__ = [
    "BaseAttack",
    "AttackConfig",
    "ATTACK_REGISTRY",
    "create_attack_instance",
    "AttackEvaluator",
    "EvaluationResult",
    "get_default_evaluator",
    "CONFIG_REGISTRY",
    "create_config",
    "get_default_config",
    "TAPConfig",
    "JudgeStrategy",
    "PromptInjectionAttack",
    "AdvancedPromptInjection",
    "JailbreakAttack",
    "GCGAttack",
    "AutoDANAttack",
    "GCGPlusPlusAttack",
    "TAPAttack",
    "MultiTurnJailbreakAttack",
    "CrescendoAttack",
    "AgentAttackType",
    "AgentAttackConfig",
    "ToolAbuseAttack",
    "MemoryInjectionAttack",
    "RoleHijackingAttack",
    "RAGAttackType",
    "RAGAttackConfig",
    "RAGContextInjectionAttack",
    "AgentToolManipulationAttack",
    "IndirectPromptInjectionAttack",
    "AuthorityEscalationAttack",
    "ChainOfThoughtInjectionAttack",
    "ChainOfThoughtExfiltrationAttack",
]

# 5. Finally, run dynamic loading to ensure all registry decorators are triggered
# (Moved to end to prevent circular import issues during initialization)
import pkgutil
import importlib
from pathlib import Path

def _load_all_attacks():
    """Dynamically load all submodules to trigger registration."""
    package_dir = str(Path(__file__).parent)
    for _, module_name, is_pkg in pkgutil.iter_modules([package_dir]):
        if not is_pkg and module_name not in ["base", "registry", "evaluation", "config", "__init__"]:
            try:
                # We use a guarded import here
                importlib.import_module(f".{module_name}", package=__name__)
            except Exception:
                pass # Already loaded or error handled elsewhere

_load_all_attacks()
