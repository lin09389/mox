"""Mox Attacks Module

Unified interface for all attack implementations.
Supports dynamic loading and registry-based instantiation.
"""

# 1. First, import everything we want to export
from .orchestrator import orchestrator, AttackOrchestrator
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
    "verify_registry",
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

# 5. Dynamic loading — triggers registration decorators in submodules.
#    Uses a guard so the work happens exactly once, either at first import
#    or on an explicit init() call (useful for tests that need a clean slate).

import pkgutil
import importlib
from pathlib import Path

_load_failures: list[tuple[str, Exception]] = []
_loaded = False

_EXCLUDED_MODULES = frozenset(["base", "registry", "evaluation", "config", "__init__"])


def _load_all_attacks():
    """Dynamically load all submodules to trigger registration."""
    global _loaded
    if _loaded:
        return
    _loaded = True

    import logging
    _log = logging.getLogger(__name__)
    package_dir = str(Path(__file__).parent)
    for _, module_name, is_pkg in pkgutil.iter_modules([package_dir]):
        if not is_pkg and module_name not in _EXCLUDED_MODULES:
            try:
                importlib.import_module(f".{module_name}", package=__name__)
            except Exception as e:
                _load_failures.append((module_name, e))
                _log.warning(
                    "Failed to load attack module '%s': %s. "
                    "This attack type will NOT be available in the registry.",
                    module_name, e,
                )

    n_ok = len(ATTACK_REGISTRY.registered_names)
    n_fail = len(_load_failures)
    if n_fail:
        _log.warning(
            "Attack registry loaded with %d attacks (%d modules failed: %s)",
            n_ok, n_fail, [name for name, _ in _load_failures],
        )
    else:
        _log.info("Attack registry loaded successfully: %d attacks registered", n_ok)


# Auto-load on first import.  Call init_attack_modules() to re-trigger.
_load_all_attacks()


def init_attack_modules() -> None:
    """Explicitly trigger attack module loading (idempotent).

    Normally called automatically at import time.  In tests you can call
    ``ATTACK_REGISTRY._entries.clear(); init_attack_modules()`` to reload.
    """
    global _loaded
    _loaded = False
    _load_failures.clear()
    _load_all_attacks()


def verify_registry() -> list[str]:
    """Return names of attack modules that failed to load.

    Intended for CI health-checks and startup diagnostics.
    An empty list means everything loaded successfully.
    """
    return [name for name, _ in _load_failures]
