"""防御注册表模块

提供防御组件的统一注册和实例创建功能。
"""

from typing import Dict, Type, Optional, Any
from mox.infrastructure.logging import get_logger

logger = get_logger("defense.registry")

class DefenseRegistry:
    """防御组件注册中心"""

    def __init__(self):
        self._registry: Dict[str, Type] = {}

    def register(self, name: str):
        """注册装饰器"""
        def wrapper(cls):
            self._registry[name.lower()] = cls
            return cls
        return wrapper

    def get(self, name: str) -> Optional[Type]:
        """获取防御类"""
        return self._registry.get(name.lower())

    @property
    def registered_names(self) -> list:
        """获取所有已注册的防御名称"""
        return list(self._registry.keys())

# 全局单例
DEFENSE_REGISTRY = DefenseRegistry()

def create_defense_instance(defense_type: str, config: Optional[Any] = None, **kwargs) -> Any:
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
        raise ValueError(f"Defense type '{defense_type}' not found in registry. "
                         f"Registered defenses: {DEFENSE_REGISTRY.registered_names}")
    
    return defense_cls(config=config, **kwargs)
