"""高级限流模块

提供多种限流策略：
- 令牌桶算法
- 滑动窗口
- 漏桶算法
- 分布式限流
- 用户级限流
- IP 级限流
"""

import time
import asyncio
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime, timedelta

from mox.infrastructure.logging import get_logger

logger = get_logger("middleware.rate_limit")


class RateLimitStrategy(str, Enum):
    """限流策略"""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    LEAKY_BUCKET = "leaky_bucket"
    FIXED_WINDOW = "fixed_window"


@dataclass
class RateLimitConfig:
    """限流配置"""
    requests_per_second: float = 10.0
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    burst_size: int = 20
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    enabled: bool = True


@dataclass
class RateLimitResult:
    """限流结果"""
    allowed: bool
    remaining: int
    reset_at: float
    retry_after: Optional[float] = None
    limit: int = 0


class TokenBucket:
    """令牌桶算法实现"""

    def __init__(
        self,
        rate: float,
        capacity: int,
    ):
        self.rate = rate  # 令牌生成速率（令牌/秒）
        self.capacity = capacity  # 桶容量
        self.tokens = capacity  # 当前令牌数
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """消费令牌"""
        async with self._lock:
            now = time.time()
            # 计算新增令牌
            elapsed = now - self.last_update
            new_tokens = elapsed * self.rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def get_tokens(self) -> float:
        """获取当前令牌数"""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            new_tokens = elapsed * self.rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_update = now
            return self.tokens


class SlidingWindowCounter:
    """滑动窗口计数器"""

    def __init__(
        self,
        window_size: int,  # 窗口大小（秒）
        max_requests: int,  # 最大请求数
    ):
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests: Dict[float, int] = {}
        self._lock = asyncio.Lock()

    async def is_allowed(self) -> tuple[bool, int]:
        """检查是否允许请求"""
        async with self._lock:
            now = time.time()
            cutoff = now - self.window_size

            # 清理过期记录
            self.requests = {
                ts: count for ts, count in self.requests.items()
                if ts > cutoff
            }

            # 计算当前窗口内的请求数
            total = sum(self.requests.values())

            if total < self.max_requests:
                # 记录本次请求
                if now not in self.requests:
                    self.requests[now] = 0
                self.requests[now] += 1
                return True, self.max_requests - total - 1

            return False, 0

    async def get_count(self) -> int:
        """获取当前计数"""
        async with self._lock:
            now = time.time()
            cutoff = now - self.window_size
            self.requests = {
                ts: count for ts, count in self.requests.items()
                if ts > cutoff
            }
            return sum(self.requests.values())


class LeakyBucket:
    """漏桶算法实现"""

    def __init__(
        self,
        rate: float,  # 漏出速率（请求/秒）
        capacity: int,  # 桶容量
    ):
        self.rate = rate
        self.capacity = capacity
        self.water = 0  # 当前水量
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def add_drop(self, drops: int = 1) -> bool:
        """添加水滴"""
        async with self._lock:
            now = time.time()
            # 计算漏出的水
            elapsed = now - self.last_update
            leaked = elapsed * self.rate
            self.water = max(0, self.water - leaked)
            self.last_update = now

            if self.water + drops <= self.capacity:
                self.water += drops
                return True
            return False


class RateLimiter:
    """统一限流器"""

    def __init__(
        self,
        config: Optional[RateLimitConfig] = None,
    ):
        self.config = config or RateLimitConfig()
        self._buckets: Dict[str, TokenBucket] = {}
        self._windows: Dict[str, SlidingWindowCounter] = {}
        self._leaky_buckets: Dict[str, LeakyBucket] = {}
        self._lock = asyncio.Lock()

    async def check(
        self,
        key: str,
        cost: int = 1,
    ) -> RateLimitResult:
        """检查限流"""
        if not self.config.enabled:
            return RateLimitResult(
                allowed=True,
                remaining=9999,
                reset_at=time.time() + 60,
            )

        if self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._check_token_bucket(key, cost)
        elif self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._check_sliding_window(key)
        elif self.config.strategy == RateLimitStrategy.LEAKY_BUCKET:
            return await self._check_leaky_bucket(key, cost)
        else:
            return await self._check_fixed_window(key)

    async def _check_token_bucket(
        self,
        key: str,
        cost: int,
    ) -> RateLimitResult:
        """令牌桶检查"""
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(
                rate=self.config.requests_per_second,
                capacity=self.config.burst_size,
            )

        bucket = self._buckets[key]
        allowed = await bucket.consume(cost)
        tokens = await bucket.get_tokens()

        return RateLimitResult(
            allowed=allowed,
            remaining=int(tokens),
            reset_at=time.time() + (cost / self.config.requests_per_second),
            retry_after=None if allowed else 1.0 / self.config.requests_per_second,
            limit=self.config.burst_size,
        )

    async def _check_sliding_window(
        self,
        key: str,
    ) -> RateLimitResult:
        """滑动窗口检查"""
        if key not in self._windows:
            self._windows[key] = SlidingWindowCounter(
                window_size=60,
                max_requests=self.config.requests_per_minute,
            )

        window = self._windows[key]
        allowed, remaining = await window.is_allowed()

        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_at=time.time() + 60,
            retry_after=None if allowed else 60,
            limit=self.config.requests_per_minute,
        )

    async def _check_leaky_bucket(
        self,
        key: str,
        cost: int,
    ) -> RateLimitResult:
        """漏桶检查"""
        if key not in self._leaky_buckets:
            self._leaky_buckets[key] = LeakyBucket(
                rate=self.config.requests_per_second,
                capacity=self.config.burst_size,
            )

        bucket = self._leaky_buckets[key]
        allowed = await bucket.add_drop(cost)

        return RateLimitResult(
            allowed=allowed,
            remaining=self.config.burst_size - int(bucket.water),
            reset_at=time.time() + 60,
            retry_after=None if allowed else bucket.water / self.config.requests_per_second,
            limit=self.config.burst_size,
        )

    async def _check_fixed_window(
        self,
        key: str,
    ) -> RateLimitResult:
        """固定窗口检查"""
        # 简化实现，使用滑动窗口
        return await self._check_sliding_window(key)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "buckets": len(self._buckets),
            "windows": len(self._windows),
            "leaky_buckets": len(self._leaky_buckets),
            "strategy": self.config.strategy.value,
        }


class MultiLevelRateLimiter:
    """多级限流器

    支持全局、用户、IP 多级限流。
    """

    def __init__(
        self,
        global_limit: int = 10000,
        user_limit: int = 100,
        ip_limit: int = 200,
    ):
        self.global_limiter = RateLimiter(RateLimitConfig(
            requests_per_minute=global_limit,
            burst_size=global_limit // 10,
        ))
        self.user_limiter = RateLimiter(RateLimitConfig(
            requests_per_minute=user_limit,
            burst_size=user_limit // 5,
        ))
        self.ip_limiter = RateLimiter(RateLimitConfig(
            requests_per_minute=ip_limit,
            burst_size=ip_limit // 5,
        ))

    async def check(
        self,
        user_id: Optional[str] = None,
        ip: Optional[str] = None,
    ) -> RateLimitResult:
        """多级检查"""
        # 全局限流
        global_result = await self.global_limiter.check("global")
        if not global_result.allowed:
            return global_result

        # 用户限流
        if user_id:
            user_result = await self.user_limiter.check(f"user:{user_id}")
            if not user_result.allowed:
                return user_result

        # IP 限流
        if ip:
            ip_result = await self.ip_limiter.check(f"ip:{ip}")
            if not ip_result.allowed:
                return ip_result

        return RateLimitResult(
            allowed=True,
            remaining=min(
                global_result.remaining,
                user_result.remaining if user_id else 9999,
                ip_result.remaining if ip else 9999,
            ),
            reset_at=time.time() + 60,
        )


# ============ 导出 ============

__all__ = [
    "RateLimitStrategy",
    "RateLimitConfig",
    "RateLimitResult",
    "TokenBucket",
    "SlidingWindowCounter",
    "LeakyBucket",
    "RateLimiter",
    "MultiLevelRateLimiter",
]