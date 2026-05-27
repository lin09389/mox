"""防御注册表模块

Backward-compatible thin wrapper around mox.core.registry.Registry.
"""

from typing import Optional, Any

from mox.core.registry import Registry
from mox.infrastructure.logging import get_logger

logger = get_logger("defense.registry")

# Global registry instance — delegates to the generic Registry.
# Note: the type parameter is intentionally loose (Any) because BaseDefense
# is defined in defense.base and we avoid circular imports here.
DEFENSE_REGISTRY: Registry = Registry("defense")


def create_defense_instance(
    defense_type: str,
    config: Optional[Any] = None,
    **kwargs: Any,
) -> Any:
    """创建防御实例的工厂函数

    Args:
        defense_type: 防御类型名称
        config: 防御配置
        **kwargs: 其他初始化参数

    Returns:
        BaseDefense 的实例
    """
    defense_cls = DEFENSE_REGISTRY.get(defense_type)
    if not defense_cls:
        raise ValueError(
            f"Defense type '{defense_type}' not found in registry. "
            f"Registered defenses: {DEFENSE_REGISTRY.registered_names}"
        )

    return defense_cls(config=config, **kwargs)
