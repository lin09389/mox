"""多级缓存模块

提供多级缓存策略：
- L1: 内存缓存（最快）
- L2: Redis 缓存（分布式）
- L3: 数据库缓存（持久化）
"""

import time
import asyncio
import hashlib
import json
from typing import Optional, Dict, Any, Generic, TypeVar, Callable
from dataclasses import dataclass, field
from collections import OrderedDict
from abc import ABC, abstractmethod

from mox.core.logging import get_logger

logger = get_logger("core.cache")

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """缓存条目"""

    key: str
    value: T
    created_at: float
    expires_at: Optional[float] = None
    hits: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


@dataclass
class CacheStats:
    """缓存统计"""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class CacheBackend(ABC, Generic[T]):
    """缓存后端抽象"""

    @abstractmethod
    async def get(self, key: str) -> Optional[CacheEntry[T]]:
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[float] = None,
    ) -> bool:
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    async def clear(self) -> bool:
        pass

    @abstractmethod
    def get_stats(self) -> CacheStats:
        pass


class MemoryCache(CacheBackend[T]):
    """内存缓存（LRU）"""

    def __init__(
        self,
        max_size: int = 10000,
        default_ttl: float = 300.0,  # 5分钟
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._stats = CacheStats(max_size=max_size)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[CacheEntry[T]]:
        async with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return None

            entry = self._cache[key]

            if entry.is_expired():
                del self._cache[key]
                self._stats.misses += 1
                self._stats.evictions += 1
                return None

            # LRU: 移到末尾
            self._cache.move_to_end(key)
            entry.hits += 1
            self._stats.hits += 1
            return entry

    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[float] = None,
    ) -> bool:
        async with self._lock:
            now = time.time()
            ttl = ttl or self.default_ttl

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=now + ttl if ttl else None,
            )

            # 如果已存在，先删除
            if key in self._cache:
                del self._cache[key]

            # LRU 淘汰
            while len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats.evictions += 1

            self._cache[key] = entry
            self._stats.size = len(self._cache)
            return True

    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.size = len(self._cache)
                return True
            return False

    async def clear(self) -> bool:
        async with self._lock:
            self._cache.clear()
            self._stats.size = 0
            return True

    def get_stats(self) -> CacheStats:
        self._stats.size = len(self._cache)
        return self._stats


class RedisCache(CacheBackend[T]):
    """Redis 缓存"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        prefix: str = "mox:",
        default_ttl: float = 3600.0,  # 1小时
    ):
        self.redis_url = redis_url
        self.prefix = prefix
        self.default_ttl = default_ttl
        self._redis = None
        self._stats = CacheStats()

    async def _get_redis(self):
        if self._redis is None:
            try:
                import redis.asyncio as redis

                self._redis = redis.from_url(self.redis_url)
            except ImportError:
                raise ImportError("redis package required. Install with: pip install redis")
        return self._redis

    def _make_key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[CacheEntry[T]]:
        try:
            redis = await self._get_redis()
            full_key = self._make_key(key)
            data = await redis.get(full_key)

            if data is None:
                self._stats.misses += 1
                return None

            # 反序列化
            entry_dict = json.loads(data)
            entry = CacheEntry(
                key=key,
                value=entry_dict["value"],
                created_at=entry_dict["created_at"],
                expires_at=entry_dict.get("expires_at"),
                hits=entry_dict.get("hits", 0) + 1,
            )

            self._stats.hits += 1
            return entry

        except Exception as e:
            logger.warning(f"Redis cache get failed: {e}")
            self._stats.misses += 1
            return None

    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[float] = None,
    ) -> bool:
        try:
            redis = await self._get_redis()
            full_key = self._make_key(key)
            ttl = ttl or self.default_ttl

            now = time.time()
            entry_dict = {
                "value": value,
                "created_at": now,
                "expires_at": now + ttl if ttl else None,
                "hits": 0,
            }

            await redis.setex(
                full_key,
                int(ttl),
                json.dumps(entry_dict),
            )
            return True

        except Exception as e:
            logger.warning(f"Redis cache set failed: {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            redis = await self._get_redis()
            full_key = self._make_key(key)
            await redis.delete(full_key)
            return True
        except Exception as e:
            logger.warning(f"Redis cache delete failed: {e}")
            return False

    async def clear(self) -> bool:
        try:
            redis = await self._get_redis()
            # 删除所有匹配前缀的键
            pattern = f"{self.prefix}*"
            keys = []
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await redis.delete(*keys)
            return True
        except Exception as e:
            logger.warning(f"Redis cache clear failed: {e}")
            return False

    def get_stats(self) -> CacheStats:
        return self._stats


class MultiLevelCache(Generic[T]):
    """多级缓存

    L1 (内存) -> L2 (Redis) -> L3 (数据库/源)
    """

    def __init__(
        self,
        l1_cache: Optional[MemoryCache[T]] = None,
        l2_cache: Optional[RedisCache[T]] = None,
        l1_ttl: float = 60.0,  # 1分钟
        l2_ttl: float = 3600.0,  # 1小时
    ):
        self.l1 = l1_cache or MemoryCache(default_ttl=l1_ttl)
        self.l2 = l2_cache
        self.l1_ttl = l1_ttl
        self.l2_ttl = l2_ttl

    async def get(
        self,
        key: str,
        loader: Optional[Callable[[], T]] = None,
    ) -> Optional[T]:
        """获取缓存值

        Args:
            key: 缓存键
            loader: 数据加载函数（当缓存未命中时调用）
        """
        # L1 查找
        entry = await self.l1.get(key)
        if entry is not None:
            logger.debug(f"Cache L1 hit: {key}")
            return entry.value

        # L2 查找
        if self.l2:
            entry = await self.l2.get(key)
            if entry is not None:
                logger.debug(f"Cache L2 hit: {key}")
                # 回填 L1
                await self.l1.set(key, entry.value, self.l1_ttl)
                return entry.value

        # 加载数据
        if loader:
            logger.debug(f"Cache miss, loading: {key}")
            value = await loader() if asyncio.iscoroutinefunction(loader) else loader()
            if value is not None:
                await self.set(key, value)
            return value

        return None

    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[float] = None,
    ) -> bool:
        """设置缓存值"""
        l1_ttl = min(ttl or self.l1_ttl, self.l1_ttl)
        l2_ttl = ttl or self.l2_ttl

        # 写入 L1
        await self.l1.set(key, value, l1_ttl)

        # 写入 L2
        if self.l2:
            await self.l2.set(key, value, l2_ttl)

        return True

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        await self.l1.delete(key)
        if self.l2:
            await self.l2.delete(key)
        return True

    async def clear(self) -> bool:
        """清空缓存"""
        await self.l1.clear()
        if self.l2:
            await self.l2.clear()
        return True

    def get_stats(self) -> Dict[str, CacheStats]:
        """获取统计信息"""
        stats = {
            "l1": self.l1.get_stats(),
        }
        if self.l2:
            stats["l2"] = self.l2.get_stats()
        return stats


class CacheManager:
    """缓存管理器

    提供统一的缓存管理接口。
    """

    _instance: Optional["CacheManager"] = None

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: float = 300.0,
    ):
        self.default_ttl = default_ttl

        # 创建多级缓存
        self._caches: Dict[str, MultiLevelCache] = {}

        # 默认缓存
        self._default_cache = MultiLevelCache(
            l1_cache=MemoryCache(default_ttl=default_ttl),
            l2_cache=RedisCache(redis_url=redis_url) if redis_url else None,
        )

    @classmethod
    def get_instance(cls, **kwargs) -> "CacheManager":
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    async def get(
        self,
        key: str,
        namespace: str = "default",
        loader: Optional[Callable[[], T]] = None,
    ) -> Optional[T]:
        """获取缓存"""
        cache = self._caches.get(namespace, self._default_cache)
        full_key = f"{namespace}:{key}"
        return await cache.get(full_key, loader)

    async def set(
        self,
        key: str,
        value: T,
        namespace: str = "default",
        ttl: Optional[float] = None,
    ) -> bool:
        """设置缓存"""
        cache = self._caches.get(namespace, self._default_cache)
        full_key = f"{namespace}:{key}"
        return await cache.set(full_key, value, ttl)

    async def delete(
        self,
        key: str,
        namespace: str = "default",
    ) -> bool:
        """删除缓存"""
        cache = self._caches.get(namespace, self._default_cache)
        full_key = f"{namespace}:{key}"
        return await cache.delete(full_key)

    async def clear(self, namespace: Optional[str] = None) -> bool:
        """清空缓存"""
        if namespace:
            cache = self._caches.get(namespace)
            if cache:
                return await cache.clear()
        else:
            await self._default_cache.clear()
            for cache in self._caches.values():
                await cache.clear()
        return True

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "default": self._default_cache.get_stats(),
        }
        for name, cache in self._caches.items():
            stats[name] = cache.get_stats()
        return stats

    def create_namespace(
        self,
        name: str,
        l1_size: int = 1000,
        l1_ttl: float = 60.0,
        l2_ttl: float = 3600.0,
    ) -> MultiLevelCache:
        """创建命名空间缓存"""
        cache = MultiLevelCache(
            l1_cache=MemoryCache(max_size=l1_size, default_ttl=l1_ttl),
            l2_cache=self._default_cache.l2,
            l1_ttl=l1_ttl,
            l2_ttl=l2_ttl,
        )
        self._caches[name] = cache
        return cache


def cache_key(*args, **kwargs) -> str:
    """生成缓存键"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)
    return hashlib.sha256(key_string.encode("utf-8")).hexdigest()


def cached(
    namespace: str = "default",
    ttl: Optional[float] = None,
    key_builder: Optional[Callable] = None,
):
    """缓存装饰器"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = CacheManager.get_instance()

            # 生成缓存键
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                key = f"{func.__name__}:{cache_key(*args, **kwargs)}"

            # 尝试从缓存获取
            result = await cache.get(key, namespace)
            if result is not None:
                return result

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            if result is not None:
                await cache.set(key, result, namespace, ttl)

            return result

        return wrapper

    return decorator


# ============ 导出 ============

__all__ = [
    "CacheEntry",
    "CacheStats",
    "CacheBackend",
    "MemoryCache",
    "RedisCache",
    "MultiLevelCache",
    "CacheManager",
    "cache_key",
    "cached",
]
