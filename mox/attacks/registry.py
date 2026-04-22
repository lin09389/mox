"""Attack registry for LLM adversarial implementations."""
from __future__ import annotations

from typing import Dict, Type, Callable, Any, Optional
from mox.core import BaseLLM, AttackType
from .base import BaseAttack, AttackConfig

# Type alias for attack factory
AttackFactory = Callable[[BaseLLM, Any], BaseAttack]

class Registry:
    """Central registry for attack implementations."""

    def __init__(self):
        self._attacks: Dict[str, Type[BaseAttack]] = {}

    def register(self, name: str):
        """Decorator to register an attack class."""
        def decorator(cls: Type[BaseAttack]):
            self._attacks[name] = cls
            return cls
        return decorator

    def get(self, name: str) -> Optional[Type[BaseAttack]]:
        """Get an attack class by name."""
        return self._attacks.get(name)

    @property
    def registered_names(self) -> list[str]:
        """List of all registered attack names."""
        return list(self._attacks.keys())

# Global registry instance
ATTACK_REGISTRY = Registry()

def create_attack_instance(
    attack_type: str,
    llm: BaseLLM,
    config: Optional[AttackConfig] = None,
    **kwargs
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
        raise ValueError(f"Attack type '{attack_type}' not found in registry. "
                         f"Registered attacks: {ATTACK_REGISTRY.registered_names}")

    return attack_cls(target_llm=llm, config=config, **kwargs)
