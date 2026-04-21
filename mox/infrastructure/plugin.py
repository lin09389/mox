"""插件系统模块 - 增强版

支持:
- 本地插件目录加载
- pip 包式插件
- 插件配置管理
- 插件 API 端点
"""

import os
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar
import importlib
from pathlib import Path

from .logging import get_logger
from mox.core.types import AttackType, DefenseType
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
    entry_point: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    checksum: Optional[str] = None


@dataclass
class PluginConfig:
    """插件配置"""

    enabled: bool = True
    priority: int = 0
    settings: Dict[str, Any] = field(default_factory=dict)


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

    def validate(self) -> bool:
        """验证插件配置"""
        return True


class PluginRegistry:
    """插件注册表"""

    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        self._attack_handlers: Dict[AttackType, Type["BaseAttack"]] = {}
        self._defense_handlers: Dict[DefenseType, Type["BaseDefense"]] = {}
        self._plugin_configs: Dict[str, PluginConfig] = {}

    def register(
        self, name: str, plugin: BasePlugin, config: Optional[PluginConfig] = None
    ) -> None:
        """注册插件"""
        if name in self._plugins:
            logger.warning(f"Plugin {name} already registered, replacing")
        self._plugins[name] = plugin
        self._plugin_configs[name] = config or PluginConfig()
        logger.info(f"Registered plugin: {name}")

    def unregister(self, name: str) -> None:
        """注销插件"""
        if name in self._plugins:
            self._plugins[name].cleanup()
            del self._plugins[name]
            if name in self._plugin_configs:
                del self._plugin_configs[name]
            logger.info(f"Unregistered plugin: {name}")

    def get(self, name: str) -> Optional[BasePlugin]:
        """获取插件"""
        return self._plugins.get(name)

    def get_config(self, name: str) -> Optional[PluginConfig]:
        """获取插件配置"""
        return self._plugin_configs.get(name)

    def is_enabled(self, name: str) -> bool:
        """检查插件是否启用"""
        config = self._plugin_configs.get(name)
        return config.enabled if config else True

    def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件"""
        return [
            {
                "name": name,
                "metadata": {
                    "name": p.metadata.name,
                    "version": p.metadata.version,
                    "description": p.metadata.description,
                    "author": p.metadata.author,
                    "tags": p.metadata.tags,
                },
                "config": {
                    "enabled": self._plugin_configs.get(name, PluginConfig()).enabled,
                    "priority": self._plugin_configs.get(name, PluginConfig()).priority,
                },
            }
            for name, p in self._plugins.items()
        ]

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
        self._loaded_sources: Dict[str, str] = {}

    def load_from_directory(self, plugin_dir: Path, auto_enable: bool = True) -> List[str]:
        """从目录加载插件"""
        if not plugin_dir.exists():
            logger.warning(f"Plugin directory not found: {plugin_dir}")
            return []

        loaded = []
        for file in plugin_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
            if self._load_from_file(file):
                loaded.append(file.stem)

        config_file = plugin_dir / "plugins.json"
        if config_file.exists():
            self._load_config(config_file)

        logger.info(f"Loaded {len(loaded)} plugins from {plugin_dir}")
        return loaded

    def _load_config(self, config_file: Path) -> None:
        """加载插件配置"""
        try:
            with open(config_file) as f:
                configs = json.load(f)
                for name, config in configs.items():
                    if name in self.registry.list_plugins():
                        self.registry._plugin_configs[name] = PluginConfig(
                            enabled=config.get("enabled", True),
                            priority=config.get("priority", 0),
                            settings=config.get("settings", {}),
                        )
        except Exception as e:
            logger.error(f"Failed to load plugin config: {e}")

    def _load_from_file(self, file: Path) -> bool:
        """从文件加载插件"""
        module_name = f"mox_plugins_{file.stem}"
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
                        if hasattr(attr, "metadata"):
                            self.registry.register(attr.metadata.name, plugin)
                            self._loaded_sources[attr.metadata.name] = str(file)
                            logger.info(f"Loaded plugin: {attr.metadata.name} from {file.name}")
                        return True

        except Exception as e:
            logger.error(f"Failed to load plugin from {file}: {e}")
        return False

    def save_config(self, plugin_dir: Path) -> None:
        """保存插件配置"""
        config_file = plugin_dir / "plugins.json"
        configs = {}
        for name in self.registry._plugins.keys():
            config = self.registry.get_config(name)
            if config:
                configs[name] = {
                    "enabled": config.enabled,
                    "priority": config.priority,
                    "settings": config.settings,
                }
        try:
            with open(config_file, "w") as f:
                json.dump(configs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save plugin config: {e}")


class PluginContext:
    """插件上下文"""

    def __init__(self):
        self.registry = PluginRegistry()
        self.loader = PluginLoader(self.registry)
        self._initialized = False

    def initialize(self, plugin_dir: Optional[Path] = None) -> None:
        """初始化并加载插件"""
        if self._initialized:
            return

        if plugin_dir is None:
            plugin_dir = Path("plugins")

        os.makedirs(plugin_dir, exist_ok=True)
        self.loader.load_from_directory(plugin_dir)
        self._initialized = True
        logger.info(f"Plugin context initialized with {len(self.registry.list_plugins())} plugins")

    def load_plugins(self, plugin_dir: Optional[Path] = None) -> None:
        """加载插件"""
        self.initialize(plugin_dir)

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """获取插件"""
        if not self._initialized:
            self.initialize()
        return self.registry.get(name)

    def enable_plugin(self, name: str) -> bool:
        """启用插件"""
        config = self.registry.get_config(name)
        if config:
            config.enabled = True
            return True
        return False

    def disable_plugin(self, name: str) -> bool:
        """禁用插件"""
        config = self.registry.get_config(name)
        if config:
            config.enabled = False
            return True
        return False

    def configure_plugin(self, name: str, settings: Dict[str, Any]) -> bool:
        """配置插件"""
        config = self.registry.get_config(name)
        if config:
            config.settings.update(settings)
            plugin = self.registry.get(name)
            if plugin:
                try:
                    plugin.initialize(config.settings)
                    return True
                except Exception as e:
                    logger.error(f"Failed to reinitialize plugin {name}: {e}")
        return False


global_plugin_context = PluginContext()


def get_plugin_context() -> PluginContext:
    """获取全局插件上下文"""
    return global_plugin_context
