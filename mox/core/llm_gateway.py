"""LLM统一网关 - 支持负载均衡和故障转移"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import random
from datetime import datetime, timedelta

from .llm import BaseLLM, LLMFactory, ModelProvider, Message, LLMResponse
from .logging import get_logger

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


class RateLimiter:
    """速率限制器"""

    def __init__(self, rpm: int, tpm: int):
        self.rpm = rpm
        self.tpm = tpm
        self.requests: List[datetime] = []
        self.tokens_used: int = 0

    async def acquire(self, estimated_tokens: int = 0) -> bool:
        now = datetime.now()
        self.requests = [t for t in self.requests if now - t < timedelta(minutes=1)]

        # Check request rate limit
        if len(self.requests) >= self.rpm:
            return False

        # Check token rate limit - use estimated_tokens properly
        if self.tokens_used + estimated_tokens >= self.tpm:
            return False

        # Reserve tokens for this request
        self.tokens_used += estimated_tokens
        self.requests.append(now)
        return True

    def reset(self):
        self.requests = []
        self.tokens_used = 0


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


class BatchRequest:
    """批量请求处理"""

    def __init__(self, max_batch_size: int = 10, timeout: float = 1.0):
        self.max_batch_size = max_batch_size
        self.timeout = timeout
        self._pending: List[asyncio.Future] = []
        self._lock = asyncio.Lock()

    async def submit(self, coro) -> Any:
        """提交请求到批次"""
        future = asyncio.Future()
        async with self._lock:
            self._pending.append(future)

            if len(self._pending) >= self.max_batch_size:
                await self._flush()

        asyncio.create_task(self._wait_and_resolve(coro, future))
        return await future

    async def _wait_and_resolve(self, coro, future: asyncio.Future):
        try:
            result = await asyncio.wait_for(coro, timeout=self.timeout)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)

    async def _flush(self):
        if not self._pending:
            return
        # Actually await all pending futures before clearing
        for future in self._pending:
            if not future.done():
                try:
                    await asyncio.wait_for(future, timeout=self.timeout)
                except Exception:
                    pass
        self._pending.clear()


class LLMGateway:
    """LLM统一网关 - 支持多模型负载均衡"""

    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or GatewayConfig()
        self.endpoints: Dict[str, LLMEndpoint] = {}
        self._current_index = 0
        self._lock = asyncio.Lock()
        self.rate_limiters: Dict[str, RateLimiter] = {}

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

        limiter = self.rate_limiters.get(endpoint.model)
        if limiter:
            await limiter.acquire(estimated_tokens=max_tokens or 500)

        llm = LLMFactory.create(
            endpoint.provider,
            endpoint.model,
            base_url=endpoint.base_url,
            api_key=endpoint.api_key,
        )

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
                self.endpoints[endpoint.model].health_status = "unhealthy"
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

        llm = LLMFactory.create(
            endpoint.provider,
            endpoint.model,
            base_url=endpoint.base_url,
            api_key=endpoint.api_key,
        )

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
