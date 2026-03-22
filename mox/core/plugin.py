"""插件系统模块"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar
import importlib
from pathlib import Path

from .logging import get_logger
from .types import AttackType, DefenseType
from mox.attacks.base import BaseAttack
from mox.defense.base import BaseDefense

logger = get_logger("plugin")

T = TypeVar("T", bound="BasePlugin")


@dataclass
class PluginMetadata:
    """插件元数据"""

    name: str
    version: str
    description: str
    author: str
    tags: List[str] = field(default_factory=list)


class BasePlugin(ABC):
    """插件基类"""

    metadata: PluginMetadata

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """初始化插件"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """清理插件资源"""
        pass


class PluginRegistry:
    """插件注册表"""

    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        self._attack_handlers: Dict[AttackType, Type["BaseAttack"]] = {}
        self._defense_handlers: Dict[DefenseType, Type["BaseDefense"]] = {}

    def register(self, name: str, plugin: BasePlugin) -> None:
        """注册插件"""
        self._plugins[name] = plugin
        logger.info(f"Registered plugin: {name}")

    def unregister(self, name: str) -> None:
        """注销插件"""
        if name in self._plugins:
            self._plugins[name].cleanup()
            del self._plugins[name]
            logger.info(f"Unregistered plugin: {name}")

    def get(self, name: str) -> Optional[BasePlugin]:
        """获取插件"""
        return self._plugins.get(name)

    def list_plugins(self) -> List[str]:
        """列出所有插件"""
        return list(self._plugins.keys())

    def register_attack(self, attack_type: AttackType, handler: Type["BaseAttack"]) -> None:
        """注册攻击处理器"""
        self._attack_handlers[attack_type] = handler
        logger.info(f"Registered attack handler: {attack_type.value}")

    def register_defense(self, defense_type: DefenseType, handler: Type["BaseDefense"]) -> None:
        """注册防御处理器"""
        self._defense_handlers[defense_type] = handler
        logger.info(f"Registered defense handler: {defense_type.value}")

    def get_attack_handler(self, attack_type: AttackType) -> Optional[Type["BaseAttack"]]:
        """获取攻击处理器"""
        return self._attack_handlers.get(attack_type)

    def get_defense_handler(self, defense_type: DefenseType) -> Optional[Type["BaseDefense"]]:
        """获取防御处理器"""
        return self._defense_handlers.get(defense_type)


class PluginLoader:
    """插件加载器"""

    def __init__(self, registry: PluginRegistry):
        self.registry = registry

    def load_from_directory(self, plugin_dir: Path) -> None:
        """从目录加载插件"""
        if not plugin_dir.exists():
            logger.warning(f"Plugin directory not found: {plugin_dir}")
            return

        for file in plugin_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
            self._load_from_file(file)

    def _load_from_file(self, file: Path) -> None:
        """从文件加载插件"""
        module_name = file.stem
        try:
            spec = importlib.util.spec_from_file_location(module_name, file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BasePlugin)
                        and attr != BasePlugin
                    ):
                        plugin = attr()
                        self.registry.register(attr.metadata.name, plugin)
                        logger.info(f"Loaded plugin: {attr.metadata.name} from {file.name}")

        except Exception as e:
            logger.error(f"Failed to load plugin from {file}: {e}")


class PluginContext:
    """插件上下文"""

    def __init__(self):
        self.registry = PluginRegistry()
        self.loader = PluginLoader(self.registry)

    def load_plugins(self, plugin_dir: Optional[Path] = None) -> None:
        """加载插件"""
        if plugin_dir is None:
            plugin_dir = Path("plugins")

        self.loader.load_from_directory(plugin_dir)

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """获取插件"""
        return self.registry.get(name)


global_plugin_context = PluginContext()


def get_plugin_context() -> PluginContext:
    """获取全局插件上下文"""
    return global_plugin_context
