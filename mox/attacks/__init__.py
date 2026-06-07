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


# ----------------------------------------------------------------------------
# Centralized attack-type dispatcher
# ----------------------------------------------------------------------------
#
# The HTTP layer in routes/attack.py used to keep FOUR separate maps for
# the 4 attack families (novel, gradient, advanced, default) and inline
# them in three places (run_attack, run_batch_attacks, stream_attack).
# Adding a new attack required editing every copy of every map.  This
# factory consolidates the dispatch into one place, behind one
# signature that the routes can call regardless of attack family.
#
# The special cases (gradient attacks need GradientAttackConfig; meta
# attacks need use_adversarial_trinity=True) are handled here, not
# in the routes.
# ----------------------------------------------------------------------------

def _lazy_novel():
    from .novel_attacks import (
        TokenLevelAttack, EncodingAttack, PolicyPuppetryAttack,
        DistractAndAttack, ControlCharInjectionAttack, CascadingAttack,
    )
    return (TokenLevelAttack, EncodingAttack, PolicyPuppetryAttack,
            DistractAndAttack, ControlCharInjectionAttack, CascadingAttack)


def _lazy_gradient():
    from .gradient_attack import (
        FGSMAttack, PGDAttack, AdversarialSuffixAttack, GradientAttackConfig,
    )
    return (FGSMAttack, PGDAttack, AdversarialSuffixAttack, GradientAttackConfig)


def _lazy_advanced():
    from .advanced_attacks import (
        MultimodalAdversarialAttack, ZeroShotAdversarialAttack,
        HallucinationInductionAttack, CollaborativeAttack, EvasionAttack,
        AdvancedAttackConfig,
    )
    return (MultimodalAdversarialAttack, ZeroShotAdversarialAttack,
            HallucinationInductionAttack, CollaborativeAttack, EvasionAttack,
            AdvancedAttackConfig)


def _lazy_meta():
    from .meta_adversarial import MetaAdversarialAttack, MetaAdversarialConfig
    return MetaAdversarialAttack, MetaAdversarialConfig


def create_attack_from_request(
    attack_type: str,
    llm,
    max_iterations: int = 100,
) -> BaseAttack:
    """Map a request's ``attack_type`` string to a concrete attack instance.

    Centralizes what used to be four separate maps duplicated across
    three handlers in routes/attack.py.  Handles the special cases
    (gradient attacks need GradientAttackConfig; meta_adversarial
    needs use_adversarial_trinity=True) here, not in the routes.

    Raises ValueError for unknown attack_type.  The routes layer
    maps this to HTTP 400.
    """
    # ----- novel attacks -----
    if attack_type in {"token_level", "encoding", "policy_puppetry",
                       "control_char", "distract_attack", "cascading"}:
        (TokenLevelAttack, EncodingAttack, PolicyPuppetryAttack,
         DistractAndAttack, ControlCharInjectionAttack,
         CascadingAttack) = _lazy_novel()
        cls_map = {
            "token_level": TokenLevelAttack,
            "encoding": EncodingAttack,
            "policy_puppetry": PolicyPuppetryAttack,
            "control_char": ControlCharInjectionAttack,
            "distract_attack": DistractAndAttack,
            "cascading": CascadingAttack,
        }
        return cls_map[attack_type](llm)

    # ----- gradient attacks -----
    if attack_type in {"fgsm", "pgd", "gradient_optimization", "adversarial_suffix"}:
        FGSMAttack, PGDAttack, AdversarialSuffixAttack, GradientAttackConfig = _lazy_gradient()
        gradient_config = GradientAttackConfig(
            max_iterations=max_iterations, verbose=True,
        )
        if attack_type == "fgsm":
            return FGSMAttack(target_llm=llm, gradient_config=gradient_config)
        if attack_type == "pgd":
            return PGDAttack(target_llm=llm, gradient_config=gradient_config)
        # gradient_optimization and adversarial_suffix both use
        # AdversarialSuffixAttack (same algorithm, different name).
        return AdversarialSuffixAttack(
            target_llm=llm, gradient_config=gradient_config,
        )

    # ----- meta-adversarial (must precede the advanced branch) -----
    if attack_type == "meta_adversarial":
        MetaAdversarialAttack, MetaAdversarialConfig = _lazy_meta()
        return MetaAdversarialAttack(
            target_llm=llm,
            meta_config=MetaAdversarialConfig(
                max_iterations=max_iterations,
                use_adversarial_trinity=True,
            ),
        )

    # ----- advanced attacks -----
    if attack_type in {"multimodal_adversarial", "zero_shot_adversarial",
                       "hallucination_induction", "collaborative_attack",
                       "evasion_attack"}:
        (MultimodalAdversarialAttack, ZeroShotAdversarialAttack,
         HallucinationInductionAttack, CollaborativeAttack,
         EvasionAttack, AdvancedAttackConfig) = _lazy_advanced()
        cls_map = {
            "multimodal_adversarial": MultimodalAdversarialAttack,
            "zero_shot_adversarial": ZeroShotAdversarialAttack,
            "hallucination_induction": HallucinationInductionAttack,
            "collaborative_attack": CollaborativeAttack,
            "evasion_attack": EvasionAttack,
        }
        advanced_config = AdvancedAttackConfig(max_iterations=max_iterations)
        return cls_map[attack_type](target_llm=llm, config=advanced_config)

    # ----- default family (uses plain AttackConfig) -----
    default_map = {
        "prompt_injection": PromptInjectionAttack,
        "jailbreak": JailbreakAttack,
        "gcg": GCGAttack,
        "autodan": AutoDANAttack,
    }
    if attack_type in default_map:
        config = AttackConfig(max_iterations=max_iterations)
        return default_map[attack_type](target_llm=llm, config=config)

    raise ValueError(
        f"Unknown attack_type '{attack_type}'. "
        f"Known: {sorted(default_map) + ['token_level', 'encoding', 'policy_puppetry', 'control_char', 'distract_attack', 'cascading', 'fgsm', 'pgd', 'gradient_optimization', 'adversarial_suffix', 'meta_adversarial', 'multimodal_adversarial', 'zero_shot_adversarial', 'hallucination_induction', 'collaborative_attack', 'evasion_attack']}"
    )


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
