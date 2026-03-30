"""API 版本控制模块

提供 API 版本管理：
- URL 路径版本控制 (/v1/, /v2/)
- Header 版本控制 (Accept: application/json; version=1)
- 查询参数版本控制 (?version=1)
- 版本废弃管理
- 版本迁移辅助
"""

import re
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from mox.core.logging import get_logger

logger = get_logger("middleware.versioning")


class VersioningStrategy(str, Enum):
    """版本控制策略"""
    URL_PATH = "url_path"  # /v1/endpoint
    HEADER = "header"  # Accept: application/json; version=1
    QUERY_PARAM = "query_param"  # ?version=1


@dataclass
class APIVersion:
    """API 版本"""
    major: int
    minor: int = 0
    patch: int = 0

    @classmethod
    def parse(cls, version_str: str) -> "APIVersion":
        """解析版本字符串"""
        # 支持 v1, v1.0, v1.0.0, 1, 1.0, 1.0.0
        version_str = version_str.lstrip("v")
        parts = version_str.split(".")

        major = int(parts[0]) if len(parts) > 0 else 1
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0

        return cls(major=major, minor=minor, patch=patch)

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: "APIVersion") -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other: "APIVersion") -> bool:
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)

    def __gt__(self, other: "APIVersion") -> bool:
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __ge__(self, other: "APIVersion") -> bool:
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, APIVersion):
            return False
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    @property
    def short(self) -> str:
        """短版本号 (v1)"""
        return f"v{self.major}"


@dataclass
class VersionInfo:
    """版本信息"""
    version: APIVersion
    release_date: Optional[datetime] = None
    deprecation_date: Optional[datetime] = None
    sunset_date: Optional[datetime] = None
    description: str = ""
    changes: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)

    @property
    def is_deprecated(self) -> bool:
        if self.deprecation_date is None:
            return False
        return datetime.now() > self.deprecation_date

    @property
    def is_sunset(self) -> bool:
        if self.sunset_date is None:
            return False
        return datetime.now() > self.sunset_date

    @property
    def deprecation_status(self) -> str:
        if self.is_sunset:
            return "sunset"
        elif self.is_deprecated:
            return "deprecated"
        return "active"


@dataclass
class VersioningConfig:
    """版本控制配置"""
    strategy: VersioningStrategy = VersioningStrategy.URL_PATH
    default_version: APIVersion = field(default_factory=lambda: APIVersion(1))
    supported_versions: List[APIVersion] = field(default_factory=lambda: [APIVersion(1)])
    header_name: str = "Accept"
    query_param: str = "version"
    version_prefix: str = "v"


class VersionManager:
    """版本管理器"""

    def __init__(
        self,
        config: Optional[VersioningConfig] = None,
    ):
        self.config = config or VersioningConfig()
        self._versions: Dict[str, VersionInfo] = {}
        self._migrations: Dict[str, Callable] = {}

    def register_version(
        self,
        version: APIVersion,
        info: Optional[VersionInfo] = None,
    ) -> None:
        """注册版本"""
        key = version.short
        if info is None:
            info = VersionInfo(version=version)
        self._versions[key] = info

    def get_version_info(self, version: APIVersion) -> Optional[VersionInfo]:
        """获取版本信息"""
        return self._versions.get(version.short)

    def is_supported(self, version: APIVersion) -> bool:
        """检查版本是否支持"""
        return any(
            v.major == version.major and v.minor >= version.minor
            for v in self.config.supported_versions
        )

    def get_latest_version(self) -> APIVersion:
        """获取最新版本"""
        if not self.config.supported_versions:
            return self.config.default_version
        return max(self.config.supported_versions, key=lambda v: (v.major, v.minor, v.patch))

    def parse_version_from_request(
        self,
        path: str = "",
        headers: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
    ) -> APIVersion:
        """从请求解析版本"""
        headers = headers or {}
        query_params = query_params or {}

        # URL 路径版本
        if self.config.strategy == VersioningStrategy.URL_PATH:
            match = re.search(r"/v(\d+)(?:\.(\d+))?(?:\.(\d+))?/", path)
            if match:
                major = int(match.group(1))
                minor = int(match.group(2)) if match.group(2) else 0
                patch = int(match.group(3)) if match.group(3) else 0
                return APIVersion(major, minor, patch)

        # Header 版本
        elif self.config.strategy == VersioningStrategy.HEADER:
            accept = headers.get(self.config.header_name, "")
            match = re.search(r"version=(\d+(?:\.\d+)?)", accept)
            if match:
                return APIVersion.parse(match.group(1))

        # 查询参数版本
        elif self.config.strategy == VersioningStrategy.QUERY_PARAM:
            version_str = query_params.get(self.config.query_param)
            if version_str:
                return APIVersion.parse(version_str)

        return self.config.default_version

    def register_migration(
        self,
        from_version: APIVersion,
        to_version: APIVersion,
        migration_func: Callable,
    ) -> None:
        """注册版本迁移函数"""
        key = f"{from_version.short}->{to_version.short}"
        self._migrations[key] = migration_func

    async def migrate(
        self,
        data: Any,
        from_version: APIVersion,
        to_version: APIVersion,
    ) -> Any:
        """迁移数据到新版本"""
        if from_version == to_version:
            return data

        key = f"{from_version.short}->{to_version.short}"
        migration_func = self._migrations.get(key)

        if migration_func:
            if asyncio.iscoroutinefunction(migration_func):
                return await migration_func(data)
            return migration_func(data)

        logger.warning(f"No migration path from {from_version} to {to_version}")
        return data

    def get_deprecation_headers(
        self,
        version: APIVersion,
    ) -> Dict[str, str]:
        """获取废弃相关响应头"""
        info = self.get_version_info(version)
        headers = {}

        if info and info.is_deprecated:
            headers["Deprecation"] = "true"

            if info.sunset_date:
                headers["Sunset"] = info.sunset_date.strftime("%a, %d %b %Y %H:%M:%S GMT")

            # 建议升级到最新版本
            latest = self.get_latest_version()
            headers["Link"] = f'</v{latest.major}/>; rel="successor-version"'

        return headers

    def get_version_list(self) -> List[Dict[str, Any]]:
        """获取所有版本列表"""
        versions = []
        for key, info in sorted(self._versions.items()):
            versions.append({
                "version": str(info.version),
                "status": info.deprecation_status,
                "release_date": info.release_date.isoformat() if info.release_date else None,
                "deprecation_date": info.deprecation_date.isoformat() if info.deprecation_date else None,
                "sunset_date": info.sunset_date.isoformat() if info.sunset_date else None,
                "description": info.description,
                "changes": info.changes,
                "breaking_changes": info.breaking_changes,
            })
        return versions


# 需要导入 asyncio
import asyncio


class VersionedRouter:
    """版本化路由器"""

    def __init__(
        self,
        manager: Optional[VersionManager] = None,
    ):
        self.manager = manager or VersionManager()
        self._routes: Dict[str, Dict[str, Callable]] = {}

    def route(
        self,
        path: str,
        version: APIVersion,
        methods: List[str] = None,
    ):
        """注册版本化路由"""
        methods = methods or ["GET"]

        def decorator(func: Callable) -> Callable:
            version_key = version.short
            if path not in self._routes:
                self._routes[path] = {}
            self._routes[path][version_key] = {
                "handler": func,
                "methods": methods,
            }
            return func

        return decorator

    def get_handler(
        self,
        path: str,
        version: APIVersion,
        method: str = "GET",
    ) -> Optional[Callable]:
        """获取指定版本的处理函数"""
        path_routes = self._routes.get(path, {})

        # 精确匹配
        version_key = version.short
        if version_key in path_routes:
            route_info = path_routes[version_key]
            if method in route_info["methods"]:
                return route_info["handler"]

        # 回退到较低版本
        for v in sorted(
            self.manager.config.supported_versions,
            reverse=True
        ):
            key = v.short
            if key in path_routes and v <= version:
                route_info = path_routes[key]
                if method in route_info["methods"]:
                    return route_info["handler"]

        return None


# ============ 预定义版本 ============

# 初始化默认版本
DEFAULT_VERSION_MANAGER = VersionManager()
DEFAULT_VERSION_MANAGER.register_version(
    APIVersion(1, 0, 0),
    VersionInfo(
        version=APIVersion(1, 0, 0),
        release_date=datetime(2024, 1, 1),
        description="Initial API version",
    )
)
DEFAULT_VERSION_MANAGER.register_version(
    APIVersion(2, 0, 0),
    VersionInfo(
        version=APIVersion(2, 0, 0),
        release_date=datetime(2025, 1, 1),
        description="Enhanced API with new attack modules",
        changes=[
            "Added novel attack techniques",
            "Enhanced multimodal attacks",
            "New defense modules",
        ],
        breaking_changes=[
            "Response format changed",
            "Some endpoints renamed",
        ],
    )
)


# ============ 导出 ============

__all__ = [
    "VersioningStrategy",
    "APIVersion",
    "VersionInfo",
    "VersioningConfig",
    "VersionManager",
    "VersionedRouter",
    "DEFAULT_VERSION_MANAGER",
]