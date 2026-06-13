"""弃用管理模块

提供统一的弃用管理机制:
1. 弃用装饰器 - 标记函数/类为已弃用
2. 弃用警告 - 发出弃用警告
3. 弃用日志 - 记录弃用使用
4. 版本管理 - 跟踪弃用版本
5. 迁移指南 - 提供迁移建议

使用示例:
    from mox.core.deprecation import deprecated, DeprecationManager

    # 使用装饰器
    @deprecated(since="0.2.0", removed_in="0.4.0", use_instead="new_function")
    def old_function():
        pass

    # 使用管理器
    manager = DeprecationManager()
    manager.register("old_feature", since="0.2.0", removed_in="0.4.0")
"""

import warnings
import functools
import logging
from typing import Optional, Callable, Any, Dict, List, Set
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum

# 配置日志
logger = logging.getLogger("mox.core.deprecation")


class DeprecationLevel(Enum):
    """弃用级别"""
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    REMOVED = "removed"  # 已移除


@dataclass
class DeprecationInfo:
    """弃用信息"""
    name: str
    since: str  # 弃用起始版本
    removed_in: Optional[str] = None  # 计划移除版本
    use_instead: Optional[str] = None  # 替代方案
    message: Optional[str] = None  # 自定义消息
    level: DeprecationLevel = DeprecationLevel.WARNING
    deprecation_date: Optional[date] = None
    removal_date: Optional[date] = None
    usage_count: int = 0
    last_used: Optional[datetime] = None


class DeprecationManager:
    """弃用管理器"""

    def __init__(self, current_version: str = "0.3.0"):
        self.current_version = current_version
        self._deprecations: Dict[str, DeprecationInfo] = {}
        self._usage_log: List[Dict[str, Any]] = []
        self._suppress_warnings: Set[str] = set()

    def register(
        self,
        name: str,
        since: str,
        removed_in: Optional[str] = None,
        use_instead: Optional[str] = None,
        message: Optional[str] = None,
        level: DeprecationLevel = DeprecationLevel.WARNING,
        deprecation_date: Optional[date] = None,
        removal_date: Optional[date] = None,
    ):
        """注册弃用项

        Args:
            name: 弃用项名称
            since: 弃用起始版本
            removed_in: 计划移除版本
            use_instead: 替代方案
            message: 自定义消息
            level: 弃用级别
            deprecation_date: 弃用日期
            removal_date: 移除日期
        """
        info = DeprecationInfo(
            name=name,
            since=since,
            removed_in=removed_in,
            use_instead=use_instead,
            message=message,
            level=level,
            deprecation_date=deprecation_date,
            removal_date=removal_date,
        )
        self._deprecations[name] = info

    def check(self, name: str) -> Optional[DeprecationInfo]:
        """检查是否已弃用

        Args:
            name: 检查的名称

        Returns:
            DeprecationInfo if deprecated, None otherwise
        """
        return self._deprecations.get(name)

    def warn(self, name: str, stacklevel: int = 3):
        """发出弃用警告

        Args:
            name: 弃用项名称
            stacklevel: 警告堆栈级别
        """
        info = self._deprecations.get(name)
        if info is None:
            return

        # 更新使用统计
        info.usage_count += 1
        info.last_used = datetime.now()

        # 检查是否抑制警告
        if name in self._suppress_warnings:
            return

        # 构建警告消息
        message = self._build_message(info)

        # 根据级别发出警告
        if info.level == DeprecationLevel.WARNING:
            warnings.warn(message, DeprecationWarning, stacklevel=stacklevel)
            logger.warning(f"Deprecation warning: {message}")
        elif info.level == DeprecationLevel.ERROR:
            logger.error(f"Deprecation error: {message}")
            raise DeprecationError(message)
        elif info.level == DeprecationLevel.REMOVED:
            logger.error(f"Feature removed: {message}")
            raise FeatureRemovedError(message)

        # 记录使用日志
        self._log_usage(name, info)

    def _build_message(self, info: DeprecationInfo) -> str:
        """构建警告消息"""
        if info.message:
            return info.message

        parts = [f"'{info.name}' is deprecated since version {info.since}"]

        if info.removed_in:
            parts.append(f"and will be removed in version {info.removed_in}")

        if info.use_instead:
            parts.append(f"Use '{info.use_instead}' instead")

        return ". ".join(parts) + "."

    def _log_usage(self, name: str, info: DeprecationInfo):
        """记录使用日志"""
        self._usage_log.append({
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "version": self.current_version,
            "since": info.since,
            "removed_in": info.removed_in,
        })

    def suppress(self, name: str):
        """抑制弃用警告

        Args:
            name: 要抑制的弃用项名称
        """
        self._suppress_warnings.add(name)

    def unsuppress(self, name: str):
        """取消抑制弃用警告

        Args:
            name: 要取消抑制的弃用项名称
        """
        self._suppress_warnings.discard(name)

    def get_all_deprecations(self) -> Dict[str, DeprecationInfo]:
        """获取所有弃用项"""
        return self._deprecations.copy()

    def get_active_deprecations(self) -> Dict[str, DeprecationInfo]:
        """获取活跃的弃用项（未移除）"""
        return {
            name: info
            for name, info in self._deprecations.items()
            if info.level != DeprecationLevel.REMOVED
        }

    def get_removed_features(self) -> Dict[str, DeprecationInfo]:
        """获取已移除的功能"""
        return {
            name: info
            for name, info in self._deprecations.items()
            if info.level == DeprecationLevel.REMOVED
        }

    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return {
            "total_deprecations": len(self._deprecations),
            "active_deprecations": len(self.get_active_deprecations()),
            "removed_features": len(self.get_removed_features()),
            "total_usage": sum(info.usage_count for info in self._deprecations.values()),
            "usage_log_count": len(self._usage_log),
        }

    def get_usage_log(self) -> List[Dict[str, Any]]:
        """获取使用日志"""
        return self._usage_log.copy()

    def check_version_compatibility(self, version: str) -> List[str]:
        """检查版本兼容性

        Args:
            version: 要检查的版本

        Returns:
            List of warnings
        """
        warnings_list = []

        for name, info in self._deprecations.items():
            if info.removed_in and self._compare_versions(version, info.removed_in) >= 0:
                warnings_list.append(
                    f"Feature '{name}' was removed in version {info.removed_in}. "
                    f"Use '{info.use_instead or 'alternative'}' instead."
                )

        return warnings_list

    def _compare_versions(self, v1: str, v2: str) -> int:
        """比较版本号

        Returns:
            -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
        """
        def parse_version(v: str) -> List[int]:
            return [int(x) for x in v.split(".")]

        parts1 = parse_version(v1)
        parts2 = parse_version(v2)

        for p1, p2 in zip(parts1, parts2):
            if p1 < p2:
                return -1
            elif p1 > p2:
                return 1

        return 0


class DeprecationError(Exception):
    """弃用错误"""
    pass


class FeatureRemovedError(Exception):
    """功能已移除错误"""
    pass


# 全局弃用管理器
_manager: Optional[DeprecationManager] = None


def get_deprecation_manager() -> DeprecationManager:
    """获取全局弃用管理器"""
    global _manager
    if _manager is None:
        from .version import PACKAGE_VERSION
        _manager = DeprecationManager(current_version=PACKAGE_VERSION)
        _register_default_deprecations(_manager)
    return _manager


def _register_default_deprecations(manager: DeprecationManager):
    """注册默认弃用项"""
    # 攻击模块弃用
    manager.register(
        name="MultimodalAdversarialAttack",
        since="0.3.0",
        removed_in="0.5.0",
        use_instead="TextBasedAdversarialAttack",
        message="MultimodalAdversarialAttack has been renamed to TextBasedAdversarialAttack. "
                "The old name is kept as an alias for backward compatibility.",
    )

    manager.register(
        name="KnowledgeDistillationAttack",
        since="0.3.0",
        removed_in="0.5.0",
        use_instead="KnowledgeExtractionAttack",
        message="KnowledgeDistillationAttack has been renamed to KnowledgeExtractionAttack. "
                "The old name is kept as an alias for backward compatibility.",
    )

    manager.register(
        name="FGSMAttack",
        since="0.3.0",
        removed_in="0.4.0",
        use_instead="GradientBasedSuffixAttack",
        message="FGSMAttack has been replaced by GradientBasedSuffixAttack with improved gradient computation.",
    )

    manager.register(
        name="PGDAttack",
        since="0.3.0",
        removed_in="0.4.0",
        use_instead="GradientBasedSuffixAttack",
        message="PGDAttack has been replaced by GradientBasedSuffixAttack with improved gradient computation.",
    )

    manager.register(
        name="AdversarialSuffixAttack",
        since="0.3.0",
        removed_in="0.4.0",
        use_instead="GradientBasedSuffixAttack",
        message="AdversarialSuffixAttack has been replaced by GradientBasedSuffixAttack.",
    )


def deprecated(
    since: str,
    removed_in: Optional[str] = None,
    use_instead: Optional[str] = None,
    message: Optional[str] = None,
    level: DeprecationLevel = DeprecationLevel.WARNING,
):
    """弃用装饰器

    Args:
        since: 弃用起始版本
        removed_in: 计划移除版本
        use_instead: 替代方案
        message: 自定义消息
        level: 弃用级别

    Usage:
        @deprecated(since="0.2.0", removed_in="0.4.0", use_instead="new_function")
        def old_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        # 注册到管理器
        manager = get_deprecation_manager()
        manager.register(
            name=func.__qualname__,
            since=since,
            removed_in=removed_in,
            use_instead=use_instead,
            message=message,
            level=level,
        )

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            manager.warn(func.__qualname__, stacklevel=2)
            return func(*args, **kwargs)

        # 添加弃用信息到函数属性
        wrapper._deprecated = True
        wrapper._deprecation_info = DeprecationInfo(
            name=func.__qualname__,
            since=since,
            removed_in=removed_in,
            use_instead=use_instead,
            message=message,
            level=level,
        )

        return wrapper

    return decorator


def deprecated_class(
    since: str,
    removed_in: Optional[str] = None,
    use_instead: Optional[str] = None,
    message: Optional[str] = None,
    level: DeprecationLevel = DeprecationLevel.WARNING,
):
    """弃用类装饰器

    Args:
        since: 弃用起始版本
        removed_in: 计划移除版本
        use_instead: 替代方案
        message: 自定义消息
        level: 弃用级别

    Usage:
        @deprecated_class(since="0.2.0", removed_in="0.4.0", use_instead="NewClass")
        class OldClass:
            pass
    """
    def decorator(cls: type) -> type:
        # 注册到管理器
        manager = get_deprecation_manager()
        manager.register(
            name=cls.__qualname__,
            since=since,
            removed_in=removed_in,
            use_instead=use_instead,
            message=message,
            level=level,
        )

        # 保存原始 __init__
        original_init = cls.__init__

        @functools.wraps(original_init)
        def new_init(self, *args, **kwargs):
            manager.warn(cls.__qualname__, stacklevel=2)
            original_init(self, *args, **kwargs)

        cls.__init__ = new_init

        # 添加弃用信息到类属性
        cls._deprecated = True
        cls._deprecation_info = DeprecationInfo(
            name=cls.__qualname__,
            since=since,
            removed_in=removed_in,
            use_instead=use_instead,
            message=message,
            level=level,
        )

        return cls

    return decorator


def check_deprecation(name: str) -> Optional[DeprecationInfo]:
    """检查是否已弃用

    Args:
        name: 检查的名称

    Returns:
        DeprecationInfo if deprecated, None otherwise
    """
    manager = get_deprecation_manager()
    return manager.check(name)


def warn_deprecation(name: str, stacklevel: int = 2):
    """发出弃用警告

    Args:
        name: 弃用项名称
        stacklevel: 警告堆栈级别
    """
    manager = get_deprecation_manager()
    manager.warn(name, stacklevel=stacklevel + 1)


def get_deprecation_stats() -> Dict[str, Any]:
    """获取弃用统计"""
    manager = get_deprecation_manager()
    return manager.get_usage_stats()


def get_all_deprecations() -> Dict[str, DeprecationInfo]:
    """获取所有弃用项"""
    manager = get_deprecation_manager()
    return manager.get_all_deprecations()


__all__ = [
    "DeprecationLevel",
    "DeprecationInfo",
    "DeprecationManager",
    "DeprecationError",
    "FeatureRemovedError",
    "get_deprecation_manager",
    "deprecated",
    "deprecated_class",
    "check_deprecation",
    "warn_deprecation",
    "get_deprecation_stats",
    "get_all_deprecations",
]
