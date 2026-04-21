"""LLM统一网关 - 支持负载均衡和故障转移

修复：
- 缓存 LLM 实例，避免每次请求重建客户端
- RateLimiter token 使用量随请求窗口自动过期回收
- endpoint 键名统一使用 name（而非 model）
- 并发请求的限流 key 统一
"""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import random
from datetime import datetime, timedelta

from .llm import BaseLLM, LLMFactory, ModelProvider, Message, LLMResponse
from mox.infrastructure.logging import get_logger

logger = get_logger("llm_gateway")


class LoadBalancingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    RANDOM = "random"
    LEAST_LOADED = "least_loaded"


@dataclass
class LLMEndpoint:
    """LLM端点配置"""

    provider: ModelProvider
    model: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    weight: float = 1.0
    max_rpm: int = 100
    max_tpm: int = 100000
    enabled: bool = True
    health_status: str = "healthy"
    last_check: datetime = field(default_factory=datetime.now)
    request_count: int = 0
    error_count: int = 0
    avg_latency: float = 0.0


@dataclass
class GatewayConfig:
    """网关配置"""

    strategy: LoadBalancingStrategy = LoadBalancingStrategy.WEIGHTED
    max_retries: int = 3
    retry_delay: float = 1.0
    health_check_interval: int = 60
    timeout: float = 30.0
    fallback_enabled: bool = True


from collections import deque

class RateLimiter:
    """速率限制器 - 修复 token 使用量随窗口自动回收"""

    def __init__(self, rpm: int, tpm: int):
        self.rpm = rpm
        self.tpm = tpm
        self._request_timestamps: deque[datetime] = deque()
        self._token_bucket: deque[Tuple[datetime, int]] = deque()
        self._current_tokens = 0

    async def acquire(self, estimated_tokens: int = 0) -> bool:
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)

        while self._request_timestamps and self._request_timestamps[0] <= cutoff:
            self._request_timestamps.popleft()

        while self._token_bucket and self._token_bucket[0][0] <= cutoff:
            _, tokens = self._token_bucket.popleft()
            self._current_tokens -= tokens

        if len(self._request_timestamps) >= self.rpm:
            return False

        if self._current_tokens + estimated_tokens >= self.tpm:
            return False

        self._request_timestamps.append(now)
        self._token_bucket.append((now, estimated_tokens))
        self._current_tokens += estimated_tokens
        return True

    def reset(self):
        self._request_timestamps.clear()
        self._token_bucket.clear()
        self._current_tokens = 0


class ConcurrencyLimiter:
    """并发限制器 - 使用信号量控制并发数"""

    def __init__(self, max_concurrent: int = 10):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active = 0
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        await self._semaphore.acquire()
        async with self._lock:
            self._active += 1
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._semaphore.release()
        async with self._lock:
            self._active -= 1

    @property
    def active_count(self) -> int:
        return self._active


class LLMGateway:
    """LLM统一网关 - 支持多模型负载均衡

    修复：
    - 缓存 LLM 实例，复用连接
    - endpoint 键名统一使用 name
    - RateLimiter token 自动回收
    """

    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or GatewayConfig()
        self.endpoints: Dict[str, LLMEndpoint] = {}
        self._current_index = 0
        self._lock = asyncio.Lock()
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self._llm_cache: Dict[str, BaseLLM] = {}

    def _get_llm(self, endpoint: LLMEndpoint) -> BaseLLM:
        """获取或创建 LLM 实例（带缓存）"""
        cache_key = f"{endpoint.provider.value}:{endpoint.model}:{endpoint.base_url or ''}"
        if cache_key not in self._llm_cache:
            llm = LLMFactory.create(
                endpoint.provider,
                endpoint.model,
                base_url=endpoint.base_url,
                api_key=endpoint.api_key,
            )
            self._llm_cache[cache_key] = llm
            logger.debug(f"Created new LLM instance for {cache_key}")
        return self._llm_cache[cache_key]

    def add_endpoint(
        self,
        name: str,
        provider: ModelProvider,
        model: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        weight: float = 1.0,
        max_rpm: int = 100,
        max_tpm: int = 100000,
    ) -> None:
        endpoint = LLMEndpoint(
            provider=provider,
            model=model,
            base_url=base_url,
            api_key=api_key,
            weight=weight,
            max_rpm=max_rpm,
            max_tpm=max_tpm,
        )
        self.endpoints[name] = endpoint
        self.rate_limiters[name] = RateLimiter(max_rpm, max_tpm)
        logger.info(f"Added endpoint: {name} ({provider.value}/{model})")

    def remove_endpoint(self, name: str) -> None:
        if name in self.endpoints:
            ep = self.endpoints[name]
            cache_key = f"{ep.provider.value}:{ep.model}:{ep.base_url or ''}"
            self._llm_cache.pop(cache_key, None)
            del self.endpoints[name]
            del self.rate_limiters[name]
            logger.info(f"Removed endpoint: {name}")

    def get_available_endpoints(self) -> List[LLMEndpoint]:
        return [
            ep for ep in self.endpoints.values() if ep.enabled and ep.health_status == "healthy"
        ]

    def _select_endpoint_round_robin(self) -> Optional[LLMEndpoint]:
        available = self.get_available_endpoints()
        if not available:
            return None
        endpoint = available[self._current_index % len(available)]
        self._current_index += 1
        return endpoint

    def _select_endpoint_weighted(self) -> Optional[LLMEndpoint]:
        available = self.get_available_endpoints()
        if not available:
            return None
        weights = [ep.weight for ep in available]
        total = sum(weights)
        probs = [w / total for w in weights]
        return random.choices(available, weights=probs, k=1)[0]

    def _select_endpoint_least_loaded(self) -> Optional[LLMEndpoint]:
        available = self.get_available_endpoints()
        if not available:
            return None
        return min(available, key=lambda ep: ep.request_count / (ep.avg_latency + 1))

    def _select_endpoint_random(self) -> Optional[LLMEndpoint]:
        available = self.get_available_endpoints()
        if not available:
            return None
        return random.choice(available)

    def _select_endpoint(self) -> Optional[LLMEndpoint]:
        strategy_map = {
            LoadBalancingStrategy.ROUND_ROBIN: self._select_endpoint_round_robin,
            LoadBalancingStrategy.WEIGHTED: self._select_endpoint_weighted,
            LoadBalancingStrategy.LEAST_LOADED: self._select_endpoint_least_loaded,
            LoadBalancingStrategy.RANDOM: self._select_endpoint_random,
        }
        return strategy_map[self.config.strategy]()

    def _get_endpoint_name(self, endpoint: LLMEndpoint) -> Optional[str]:
        for name, ep in self.endpoints.items():
            if ep is endpoint:
                return name
        return None

    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        endpoint_name: Optional[str] = None,
    ) -> LLMResponse:
        if endpoint_name and endpoint_name in self.endpoints:
            endpoint = self.endpoints[endpoint_name]
        else:
            endpoint = self._select_endpoint()

        if not endpoint:
            raise RuntimeError("No available endpoints")

        ep_name = self._get_endpoint_name(endpoint) or endpoint_name or ""
        limiter = self.rate_limiters.get(ep_name)
        if limiter:
            await limiter.acquire(estimated_tokens=max_tokens or 500)

        llm = self._get_llm(endpoint)

        start_time = datetime.now()
        try:
            response = await llm.generate(messages, temperature, max_tokens)

            endpoint.request_count += 1
            latency = (datetime.now() - start_time).total_seconds()
            endpoint.avg_latency = (endpoint.avg_latency * 0.9) + (latency * 0.1)

            return response

        except Exception as e:
            endpoint.error_count += 1
            logger.error(f"Endpoint {endpoint.model} error: {e}")

            if self.config.fallback_enabled and endpoint_name is None:
                logger.warning("Attempting fallback to another endpoint")
                ep_name_key = self._get_endpoint_name(endpoint)
                if ep_name_key and ep_name_key in self.endpoints:
                    self.endpoints[ep_name_key].health_status = "unhealthy"
                return await self.generate(messages, temperature, max_tokens)

            raise

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        endpoint_name: Optional[str] = None,
        model: Optional[str] = None,
    ):
        if endpoint_name and endpoint_name in self.endpoints:
            endpoint = self.endpoints[endpoint_name]
        elif model:
            endpoint = next((ep for ep in self.endpoints.values() if ep.model == model), None)
        else:
            endpoint = self._select_endpoint()

        if not endpoint:
            raise RuntimeError("No available endpoints")

        llm = self._get_llm(endpoint)

        async for chunk in llm.generate_stream(messages, temperature, max_tokens):
            yield chunk

    async def health_check(self) -> Dict[str, Any]:
        results = {}
        for name, endpoint in self.endpoints.items():
            health = "healthy" if endpoint.error_count < 5 else "degraded"
            if endpoint.error_count > 10:
                health = "unhealthy"
            endpoint.health_status = health
            endpoint.last_check = datetime.now()
            results[name] = {
                "status": health,
                "requests": endpoint.request_count,
                "errors": endpoint.error_count,
                "avg_latency": endpoint.avg_latency,
            }
        return results

    def get_stats(self) -> Dict[str, Any]:
        available = self.get_available_endpoints()
        return {
            "total_endpoints": len(self.endpoints),
            "available_endpoints": len(available),
            "strategy": self.config.strategy.value,
            "cached_llm_instances": len(self._llm_cache),
            "endpoints": {
                name: {
                    "model": ep.model,
                    "status": ep.health_status,
                    "requests": ep.request_count,
                    "errors": ep.error_count,
                    "avg_latency": round(ep.avg_latency, 3),
                }
                for name, ep in self.endpoints.items()
            },
        }


_gateway: Optional[LLMGateway] = None


def get_llm_gateway() -> LLMGateway:
    global _gateway
    if _gateway is None:
        _gateway = LLMGateway()
    return _gateway
