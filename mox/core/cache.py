"""缓存模块"""

import json
import hashlib
import pickle
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, TypeVar, Generic
from dataclasses import dataclass

from .logging import get_logger

logger = get_logger("cache")

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """缓存条目"""

    key: str
    value: T
    created_at: datetime
    expires_at: Optional[datetime]


class CacheBackend(ABC):
    """缓存后端抽象类"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass


class MemoryCache(CacheBackend):
    """内存缓存 - LRU策略"""

    def __init__(self, max_size: int = 1000):
        self._cache: dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._access_order: list[str] = []

    def get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if entry is None:
            return None

        if entry.expires_at and entry.expires_at < datetime.now():
            del self._cache[key]
            self._access_order.remove(key)
            return None

        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        logger.debug(f"Cache hit: {key}")
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if len(self._cache) >= self._max_size:
            oldest = self._access_order.pop(0)
            del self._cache[oldest]
            logger.debug(f"Cache evicted: {oldest}")

        expires_at = None
        if ttl:
            expires_at = datetime.now() + timedelta(seconds=ttl)

        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            expires_at=expires_at,
        )
        self._access_order.append(key)
        logger.debug(f"Cache set: {key} (ttl={ttl}s)")

    def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted: {key}")

    def clear(self) -> None:
        self._cache.clear()
        logger.info("Cache cleared")


class DiskCache(CacheBackend):
    """磁盘缓存"""

    def __init__(self, cache_dir: Path = Path(".cache/mox")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        hash_key = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{hash_key}.json"

    def get(self, key: str) -> Optional[Any]:
        path = self._get_path(key)
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            expires_at = (
                datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
            )
            if expires_at and expires_at < datetime.now():
                path.unlink()
                return None

            logger.debug(f"Disk cache hit: {key}")
            return data["value"]
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to load cache {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expires_at = None
        if ttl:
            expires_at = (datetime.now() + timedelta(seconds=ttl)).isoformat()

        data = {
            "key": key,
            "value": value,
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at,
        }

        try:
            with open(self._get_path(key), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Disk cache set: {key} (ttl={ttl}s)")
        except Exception as e:
            logger.warning(f"Failed to save cache {key}: {e}")

    def delete(self, key: str) -> None:
        path = self._get_path(key)
        if path.exists():
            path.unlink()
            logger.debug(f"Disk cache deleted: {key}")

    def clear(self) -> None:
        for file in self.cache_dir.glob("*.json"):
            file.unlink()
        logger.info("Disk cache cleared")


try:
    import redis

    class RedisCache(CacheBackend):
        """Redis 分布式缓存"""

        def __init__(self, url: str = "redis://localhost:6379/0", prefix: str = "mox:"):
            self._client: Optional[redis.Redis] = None
            self._url = url
            self._prefix = prefix

        def _get_client(self) -> redis.Redis:
            if self._client is None:
                self._client = redis.from_url(self._url, decode_responses=True)
            return self._client

        def get(self, key: str) -> Optional[Any]:
            client = self._get_client()
            data = client.get(f"{self._prefix}{key}")
            if data is None:
                return None
            return json.loads(data)

        def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
            client = self._get_client()
            data = json.dumps(value)
            if ttl:
                client.setex(f"{self._prefix}{key}", ttl, data)
            else:
                client.set(f"{self._prefix}{key}", data)

        def delete(self, key: str) -> None:
            client = self._get_client()
            client.delete(f"{self._prefix}{key}")

        def clear(self) -> None:
            client = self._get_client()
            client.flushdb()
            logger.info("Redis cache cleared")

except ImportError:
    RedisCache = None  # type: ignore


class LLMCache:
    """LLM 响应缓存"""

    def __init__(self, backend: Optional[CacheBackend] = None, default_ttl: int = 3600):
        self.backend = backend or MemoryCache()
        self.default_ttl = default_ttl

    def _make_key(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        content = json.dumps(
            {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            sort_keys=True,
        )
        return f"llm:{hashlib.sha256(content.encode()).hexdigest()}"

    def get(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Optional[dict]:
        key = self._make_key(model, messages, temperature, max_tokens)
        return self.backend.get(key)

    def set(
        self,
        model: str,
        messages: list[dict[str, str]],
        response: dict,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        ttl: Optional[int] = None,
    ) -> None:
        key = self._make_key(model, messages, temperature, max_tokens)
        self.backend.set(key, response, ttl or self.default_ttl)

    def clear(self) -> None:
        self.backend.clear()


class CacheManager:
    """缓存管理器"""

    def __init__(self):
        self.llm_cache = LLMCache()

    async def get_stats(self) -> dict:
        """获取缓存统计"""
        backend = self.llm_cache.backend
        if hasattr(backend, "size"):
            return {
                "backend": type(backend).__name__,
                "size": backend.size(),
                "hits": getattr(backend, "hits", 0),
                "misses": getattr(backend, "misses", 0),
            }
        return {"backend": type(backend).__name__, "size": 0, "hits": 0, "misses": 0}

    async def clear(self) -> None:
        """清空缓存"""
        self.llm_cache.clear()
