"""Attack registry used by route handlers and orchestration layers."""

from __future__ import annotations

from typing import Callable

from mox.core import BaseLLM

from .base import AttackConfig
from .gcg import GCGAttack
from .jailbreak import JailbreakAttack
from .prompt_injection import PromptInjectionAttack


AttackFactory = Callable[[BaseLLM, int], object]


def _build_basic_attack(factory: type, llm: BaseLLM, max_iterations: int) -> object:
    return factory(target_llm=llm, config=AttackConfig(max_iterations=max_iterations))


def _build_autodan(llm: BaseLLM, max_iterations: int) -> object:
    from . import AutoDANAttack

    return AutoDANAttack(target_llm=llm, config=AttackConfig(max_iterations=max_iterations))


def _build_novel_attack(attack_type: str, llm: BaseLLM) -> object:
    from .novel_attacks import (
        CascadingAttack,
        ControlCharInjectionAttack,
        DistractAndAttack,
        EncodingAttack,
        PolicyPuppetryAttack,
        TokenLevelAttack,
    )

    factory_map: dict[str, type] = {
        "token_level": TokenLevelAttack,
        "encoding": EncodingAttack,
        "policy_puppetry": PolicyPuppetryAttack,
        "control_char": ControlCharInjectionAttack,
        "distract_attack": DistractAndAttack,
        "cascading": CascadingAttack,
        "rag_poisoning": CascadingAttack,
    }
    return factory_map[attack_type](llm)


def _build_gradient_attack(attack_type: str, llm: BaseLLM, max_iterations: int) -> object:
    from .gradient_attack import (
        AdversarialSuffixAttack,
        FGSMAttack,
        GradientAttackConfig,
        PGDAttack,
    )

    gradient_config = GradientAttackConfig(max_iterations=max_iterations, verbose=True)
    factory_map: dict[str, Callable[[BaseLLM, GradientAttackConfig], object]] = {
        "fgsm": lambda target_llm, config: FGSMAttack(target_llm=target_llm, gradient_config=config),
        "pgd": lambda target_llm, config: PGDAttack(target_llm=target_llm, gradient_config=config),
        "gradient_optimization": lambda target_llm, config: AdversarialSuffixAttack(
            target_llm=target_llm, gradient_config=config
        ),
        "adversarial_suffix": lambda target_llm, config: AdversarialSuffixAttack(
            target_llm=target_llm, gradient_config=config
        ),
    }
    return factory_map[attack_type](llm, gradient_config)


def _build_advanced_attack(attack_type: str, llm: BaseLLM, max_iterations: int) -> object:
    from .advanced_attacks import (
        AdvancedAttackConfig,
        CollaborativeAttack,
        EvasionAttack,
        HallucinationInductionAttack,
        KnowledgeDistillationAttack,
        MultimodalAdversarialAttack,
        ZeroShotAdversarialAttack,
    )
    from .meta_adversarial import MetaAdversarialAttack, MetaAdversarialConfig

    if attack_type == "meta_adversarial":
        meta_config = MetaAdversarialConfig(
            max_iterations=max_iterations,
            use_adversarial_trinity=True,
        )
        return MetaAdversarialAttack(target_llm=llm, meta_config=meta_config)

    advanced_config = AdvancedAttackConfig(max_iterations=max_iterations)
    factory_map: dict[str, type] = {
        "multimodal_adversarial": MultimodalAdversarialAttack,
        "zero_shot_adversarial": ZeroShotAdversarialAttack,
        "hallucination_induction": HallucinationInductionAttack,
        "collaborative_attack": CollaborativeAttack,
        "knowledge_distillation": KnowledgeDistillationAttack,
        "evasion_attack": EvasionAttack,
    }
    return factory_map[attack_type](target_llm=llm, advanced_config=advanced_config)


CORE_ATTACK_FACTORIES: dict[str, AttackFactory] = {
    "prompt_injection": lambda llm, max_iterations: _build_basic_attack(
        PromptInjectionAttack, llm, max_iterations
    ),
    "jailbreak": lambda llm, max_iterations: _build_basic_attack(
        JailbreakAttack, llm, max_iterations
    ),
    "gcg": lambda llm, max_iterations: _build_basic_attack(GCGAttack, llm, max_iterations),
    "autodan": _build_autodan,
}

NOVEL_ATTACK_TYPES = {
    "token_level",
    "encoding",
    "policy_puppetry",
    "control_char",
    "distract_attack",
    "cascading",
    "rag_poisoning",
}

GRADIENT_ATTACK_TYPES = {"fgsm", "pgd", "gradient_optimization", "adversarial_suffix"}

ADVANCED_ATTACK_TYPES = {
    "multimodal_adversarial",
    "zero_shot_adversarial",
    "hallucination_induction",
    "collaborative_attack",
    "knowledge_distillation",
    "evasion_attack",
    "meta_adversarial",
}


def create_attack_instance(attack_type: str, llm: BaseLLM, max_iterations: int) -> object:
    """Build an attack implementation from a stable registry."""
    if attack_type in CORE_ATTACK_FACTORIES:
        return CORE_ATTACK_FACTORIES[attack_type](llm, max_iterations)
    if attack_type in NOVEL_ATTACK_TYPES:
        return _build_novel_attack(attack_type, llm)
    if attack_type in GRADIENT_ATTACK_TYPES:
        return _build_gradient_attack(attack_type, llm, max_iterations)
    if attack_type in ADVANCED_ATTACK_TYPES:
        return _build_advanced_attack(attack_type, llm, max_iterations)
    return CORE_ATTACK_FACTORIES["prompt_injection"](llm, max_iterations)
