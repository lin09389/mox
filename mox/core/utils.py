"""工具函数模块"""

import asyncio
import hashlib
import json
import time
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Coroutine, List
from datetime import datetime, timedelta
from collections.abc import AsyncIterator


from .logging import get_logger

logger = get_logger("utils")


T = TypeVar("T")


def retry_on_api_error(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
):
    """API 调用重试装饰器

    Args:
        max_attempts: 最大重试次数
        min_wait: 最小等待时间（秒）
        max_wait: 最大等待时间（秒）
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except (ConnectionError, TimeoutError, asyncio.TimeoutError) as e:
                    last_exception = e
                    if attempt < max_attempts:
                        wait_time = min(min_wait * (2 ** (attempt - 1)), max_wait)
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt}/{max_attempts}), "
                            f"retrying in {wait_time}s: {e}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
            raise last_exception

        return wrapper

    return decorator


def hash_messages(messages: list[dict[str, str]]) -> str:
    """生成消息列表的哈希值，用于缓存键

    Args:
        messages: 消息列表

    Returns:
        SHA256 哈希字符串
    """
    content = json.dumps(messages, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def parse_timestamp(ts: Optional[datetime] = None) -> str:
    """解析时间戳为字符串

    Args:
        ts: 时间戳，默认当前时间

    Returns:
        ISO 格式时间字符串
    """
    return (ts or datetime.now()).isoformat()


def calculate_duration(start: datetime, end: Optional[datetime] = None) -> float:
    """计算持续时间（秒）

    Args:
        start: 开始时间
        end: 结束时间，默认当前时间

    Returns:
        持续时间（秒）
    """
    delta = (end or datetime.now()) - start
    return delta.total_seconds()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断文本

    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 超出长度时的后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_token_usage(usage: dict[str, int]) -> str:
    """格式化 token 使用量

    Args:
        usage: 包含 prompt_tokens, completion_tokens, total_tokens 的字典

    Returns:
        格式化的字符串
    """
    return (
        f"tokens: {usage.get('prompt_tokens', 0)} + "
        f"{usage.get('completion_tokens', 0)} = "
        f"{usage.get('total_tokens', 0)}"
    )


class RateLimiter:
    """简单速率限制器"""

    def __init__(self, max_calls: int, period: float):
        """初始化

        Args:
            max_calls: 时间周期内最大调用次数
            period: 时间周期（秒）
        """
        self.max_calls = max_calls
        self.period = period
        self.calls: list[datetime] = []

    async def acquire(self) -> None:
        """获取调用许可"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.period)

        self.calls = [call_time for call_time in self.calls if call_time > cutoff]

        if len(self.calls) >= self.max_calls:
            wait_time = (self.calls[0] - cutoff).total_seconds()
            logger.info(f"Rate limit reached, waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            await self.acquire()
            return

        self.calls.append(now)

    def reset(self) -> None:
        """重置限制器"""
        self.calls.clear()


class CircuitBreaker:
    """熔断器 - 防止级联故障"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = "closed"
        self._half_open_calls = 0

    @property
    def state(self) -> str:
        if self._state == "open" and self._last_failure_time:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = "half-open"
                self._half_open_calls = 0
        return self._state

    async def call(self, coro: Coroutine[Any, Any, T]) -> T:
        if self.state == "open":
            raise CircuitBreakerOpen(
                f"Circuit breaker is open, retry after {self.recovery_timeout}s"
            )

        try:
            result = await coro
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self):
        self._failure_count = 0
        if self._state == "half-open":
            self._half_open_calls += 1
            if self._half_open_calls >= self.half_open_max_calls:
                self._state = "closed"
                logger.info("Circuit breaker closed")

    def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == "half-open":
            self._state = "open"
            logger.warning("Circuit breaker opened from half-open")
        elif self._failure_count >= self.failure_threshold:
            self._state = "open"
            logger.warning(f"Circuit breaker opened after {self._failure_count} failures")

    def reset(self):
        self._failure_count = 0
        self._state = "closed"
        self._half_open_calls = 0


class CircuitBreakerOpen(Exception):
    pass


async def batch_process(
    items: List[T],
    processor: Callable[[T], Coroutine[Any, Any, Any]],
    batch_size: int = 10,
    concurrency: int = 5,
) -> List[Any]:
    """批量异步处理

    Args:
        items: 要处理的项目列表
        processor: 异步处理函数
        batch_size: 每批大小
        concurrency: 并发数

    Returns:
        处理结果列表
    """
    semaphore = asyncio.Semaphore(concurrency)

    async def process_with_limit(item: T) -> Any:
        async with semaphore:
            return await processor(item)

    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        batch_results = await asyncio.gather(*[process_with_limit(item) for item in batch])
        results.extend(batch_results)

    return results


async def async_generator_to_list(agen: AsyncIterator[T]) -> List[T]:
    """将异步生成器转换为列表"""
    result = []
    async for item in agen:
        result.append(item)
    return result


async def gather_with_limit(
    *coros: Coroutine,
    limit: int = 5,
) -> List[Any]:
    """限制并发数的 gather"""
    semaphore = asyncio.Semaphore(limit)

    async def bounded_coro(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*[bounded_coro(c) for c in coros])
