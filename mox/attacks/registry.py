"""Attack registry for LLM adversarial implementations.

Backward-compatible thin wrapper around mox.core.registry.Registry.
"""

from __future__ import annotations

from typing import Optional, Any

from mox.core import BaseLLM
from mox.core.registry import Registry
from .base import BaseAttack, AttackConfig

# Global registry instance — delegates to the generic Registry[BaseAttack].
ATTACK_REGISTRY: Registry[BaseAttack] = Registry("attack")


def create_attack_instance(
    attack_type: str,
    llm: BaseLLM,
    config: Optional[AttackConfig] = None,
    **kwargs: Any,
) -> BaseAttack:
    """Build an attack implementation from the registry.

    Args:
        attack_type: The identifier of the attack.
        llm: The target LLM.
        config: Optional configuration object.
        **kwargs: Additional arguments passed to the attack constructor.

    Returns:
        An instance of BaseAttack.
    """
    attack_cls = ATTACK_REGISTRY.get(attack_type)
    if not attack_cls:
        raise ValueError(
            f"Attack type '{attack_type}' not found in registry. "
            f"Registered attacks: {ATTACK_REGISTRY.registered_names}"
        )

    return attack_cls(target_llm=llm, config=config, **kwargs)
