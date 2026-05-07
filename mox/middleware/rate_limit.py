"""API 限流中间件

提供请求速率限制功能，防止 DoS 攻击。
"""

import time
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio

from mox.infrastructure.logging import get_logger
from mox.infrastructure.config import settings

logger = get_logger("rate_limit")


class RateLimiter:
    """基于滑动窗口的速率限制器"""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        # 每个 IP 的请求时间戳队列
        self._ip_requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._lock = asyncio.Lock()

    def _cleanup_old_requests(self, ip: str, current_time: float) -> None:
        """清理过期的请求记录"""
        cutoff = current_time - 60  # 60秒窗口
        while self._ip_requests[ip] and self._ip_requests[ip][0] < cutoff:
            self._ip_requests[ip].popleft()

    async def is_allowed(self, ip: str) -> Tuple[bool, int, int]:
        """
        检查是否允许请求

        Returns:
            (is_allowed, remaining_requests, retry_after_seconds)
        """
        async with self._lock:
            current_time = time.time()
            self._cleanup_old_requests(ip, current_time)

            request_count = len(self._ip_requests[ip])
            remaining = self.requests_per_minute - request_count

            if remaining <= 0:
                # 计算需要等待的时间
                oldest = self._ip_requests[ip][0]
                retry_after = int(oldest + 60 - current_time) + 1
                return False, 0, max(retry_after, 1)

            # 记录这次请求
            self._ip_requests[ip].append(current_time)

            return True, remaining - 1, 0

    async def get_status(self, ip: str) -> Dict:
        """获取 IP 的限流状态"""
        async with self._lock:
            current_time = time.time()
            self._cleanup_old_requests(ip, current_time)

            return {
                "requests_in_window": len(self._ip_requests[ip]),
                "limit": self.requests_per_minute,
                "remaining": self.requests_per_minute - len(self._ip_requests[ip]),
            }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""

    # 公开端点（不需要限流）
    EXEMPT_PATHS = {
        "/",
        "/api/health",
        "/health",
        "/ready",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        enabled: bool = True,
    ):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute, burst_size)
        self.enabled = enabled

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端 IP"""
        if request.client:
            client_ip = request.client.host
        else:
            client_ip = "unknown"

        trust_proxies = settings.TRUSTED_PROXIES
        trust_all = "*" in trust_proxies

        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            first_ip = forwarded.split(",")[0].strip()
            if trust_all or client_ip in trust_proxies:
                return first_ip

        real_ip = request.headers.get("x-real-ip")
        if real_ip and (trust_all or client_ip in trust_proxies):
            return real_ip

        return client_ip

    def _is_exempt(self, path: str) -> bool:
        """检查路径是否豁免限流"""
        # 精确匹配
        if path in self.EXEMPT_PATHS:
            return True

        # 前缀匹配
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path.rstrip("/")) and exempt_path.endswith("/"):
                return True

        return False

    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 如果禁用或路径豁免，直接通过
        if not self.enabled or self._is_exempt(request.url.path):
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        try:
            is_allowed, remaining, retry_after = await self.limiter.is_allowed(client_ip)

            if not is_allowed:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": retry_after,
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(self.limiter.requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            # 处理请求
            response = await call_next(request)

            # 添加 rate limit 头
            response.headers["X-RateLimit-Limit"] = str(self.limiter.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(remaining)

            return response

        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # 限流出错时放行，避免影响服务
            return await call_next(request)


# 全局限流器实例（用于依赖注入）
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """获取全局限流器实例"""
    global _rate_limiter
    if _rate_limiter is None:
        from mox.infrastructure.config import settings
        _rate_limiter = RateLimiter(
            requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
            burst_size=settings.RATE_LIMIT_BURST,
        )
    return _rate_limiter
