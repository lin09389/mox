"""统一错误处理模块

提供统一的异步错误处理机制:
1. 错误装饰器
2. 错误上下文管理器
3. 错误重试机制
4. 错误日志记录
5. 错误分类和处理

使用示例:
    from mox.core.error_handling import (
        async_error_handler,
        retry_on_error,
        ErrorContext,
        ErrorSeverity,
    )

    # 使用装饰器
    @async_error_handler(severity=ErrorSeverity.HIGH)
    async def risky_operation():
        pass

    # 使用上下文管理器
    async with ErrorContext("operation_name"):
        await risky_operation()

    # 使用重试机制
    @retry_on_error(max_retries=3)
    async def flaky_operation():
        pass
"""

import asyncio
import functools
import logging
import traceback
from typing import Optional, Callable, Any, Dict, List, Type, Union
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager

# 配置日志
logger = logging.getLogger("mox.core.error_handling")


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"  # 低：警告但继续执行
    MEDIUM = "medium"  # 中：可能影响结果
    HIGH = "high"  # 高：操作失败
    CRITICAL = "critical"  # 严重：系统级错误


class ErrorCategory(Enum):
    """错误类别"""
    VALIDATION = "validation"  # 验证错误
    NETWORK = "network"  # 网络错误
    TIMEOUT = "timeout"  # 超时错误
    AUTHENTICATION = "authentication"  # 认证错误
    AUTHORIZATION = "authorization"  # 授权错误
    RESOURCE = "resource"  # 资源错误
    LLM = "llm"  # LLM 相关错误
    ATTACK = "attack"  # 攻击相关错误
    EVALUATION = "evaluation"  # 评估相关错误
    UNKNOWN = "unknown"  # 未知错误


@dataclass
class ErrorInfo:
    """错误信息"""
    error: Exception
    severity: ErrorSeverity
    category: ErrorCategory
    context: str
    message: str
    traceback: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    retryable: bool = False
    retry_count: int = 0


class MoxError(Exception):
    """Mox 基础异常"""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.severity = severity
        self.category = category
        self.metadata = metadata or {}


class AttackError(MoxError):
    """攻击相关错误"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=kwargs.get("severity", ErrorSeverity.HIGH),
            category=ErrorCategory.ATTACK,
            **kwargs,
        )


class EvaluationError(MoxError):
    """评估相关错误"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=kwargs.get("severity", ErrorSeverity.MEDIUM),
            category=ErrorCategory.EVALUATION,
            **kwargs,
        )


class LLMError(MoxError):
    """LLM 相关错误"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=kwargs.get("severity", ErrorSeverity.MEDIUM),
            category=ErrorCategory.LLM,
            **kwargs,
        )


class TimeoutError(MoxError):
    """超时错误"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=kwargs.get("severity", ErrorSeverity.MEDIUM),
            category=ErrorCategory.TIMEOUT,
            **kwargs,
        )


class ErrorHandler:
    """错误处理器"""

    def __init__(self, log_errors: bool = True, raise_on_critical: bool = True):
        self.log_errors = log_errors
        self.raise_on_critical = raise_on_critical
        self._error_history: List[ErrorInfo] = []

    def handle_error(
        self,
        error: Exception,
        context: str = "",
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ErrorInfo:
        """处理错误

        Args:
            error: 异常对象
            context: 错误上下文
            severity: 错误严重程度
            category: 错误类别
            metadata: 额外元数据

        Returns:
            ErrorInfo: 错误信息
        """
        # 确定错误严重程度
        if severity is None:
            severity = self._determine_severity(error)

        # 确定错误类别
        if category is None:
            category = self._determine_category(error)

        # 构建错误信息
        error_info = ErrorInfo(
            error=error,
            severity=severity,
            category=category,
            context=context,
            message=str(error),
            traceback=traceback.format_exc(),
            metadata=metadata or {},
            retryable=self._is_retryable(error),
        )

        # 记录错误历史
        self._error_history.append(error_info)

        # 记录日志
        if self.log_errors:
            self._log_error(error_info)

        # 严重错误时抛出异常
        if self.raise_on_critical and severity == ErrorSeverity.CRITICAL:
            raise error

        return error_info

    def _determine_severity(self, error: Exception) -> ErrorSeverity:
        """确定错误严重程度"""
        if isinstance(error, MoxError):
            return error.severity

        if isinstance(error, (TimeoutError, asyncio.TimeoutError)):
            return ErrorSeverity.MEDIUM

        if isinstance(error, (ConnectionError, OSError)):
            return ErrorSeverity.HIGH

        if isinstance(error, (ValueError, TypeError)):
            return ErrorSeverity.MEDIUM

        if isinstance(error, (PermissionError, FileNotFoundError)):
            return ErrorSeverity.HIGH

        return ErrorSeverity.MEDIUM

    def _determine_category(self, error: Exception) -> ErrorCategory:
        """确定错误类别"""
        if isinstance(error, MoxError):
            return error.category

        if isinstance(error, (TimeoutError, asyncio.TimeoutError)):
            return ErrorCategory.TIMEOUT

        if isinstance(error, (ConnectionError, OSError)):
            return ErrorCategory.NETWORK

        if isinstance(error, (ValueError, TypeError)):
            return ErrorCategory.VALIDATION

        if isinstance(error, PermissionError):
            return ErrorCategory.AUTHORIZATION

        if isinstance(error, FileNotFoundError):
            return ErrorCategory.RESOURCE

        return ErrorCategory.UNKNOWN

    def _is_retryable(self, error: Exception) -> bool:
        """判断错误是否可重试"""
        if isinstance(error, MoxError):
            return error.category in [ErrorCategory.NETWORK, ErrorCategory.TIMEOUT]

        if isinstance(error, (TimeoutError, asyncio.TimeoutError)):
            return True

        if isinstance(error, ConnectionError):
            return True

        return False

    def _log_error(self, error_info: ErrorInfo):
        """记录错误日志"""
        log_message = (
            f"[{error_info.severity.value.upper()}] "
            f"[{error_info.category.value}] "
            f"{error_info.context}: {error_info.message}"
        )

        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)

    def get_error_history(self) -> List[ErrorInfo]:
        """获取错误历史"""
        return self._error_history.copy()

    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计"""
        if not self._error_history:
            return {"total": 0}

        by_severity = {}
        by_category = {}

        for error_info in self._error_history:
            # 按严重程度统计
            severity = error_info.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1

            # 按类别统计
            category = error_info.category.value
            by_category[category] = by_category.get(category, 0) + 1

        return {
            "total": len(self._error_history),
            "by_severity": by_severity,
            "by_category": by_category,
            "retryable_count": sum(1 for e in self._error_history if e.retryable),
        }

    def clear_history(self):
        """清除错误历史"""
        self._error_history.clear()


# 全局错误处理器
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def async_error_handler(
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: Optional[ErrorCategory] = None,
    reraise: bool = False,
    default_return: Any = None,
):
    """异步错误处理装饰器

    Args:
        severity: 错误严重程度
        category: 错误类别
        reraise: 是否重新抛出异常
        default_return: 默认返回值

    Usage:
        @async_error_handler(severity=ErrorSeverity.HIGH)
        async def risky_operation():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                handler = get_error_handler()
                error_info = handler.handle_error(
                    error=e,
                    context=func.__qualname__,
                    severity=severity,
                    category=category,
                )

                if reraise:
                    raise

                return default_return

        return wrapper
    return decorator


def sync_error_handler(
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: Optional[ErrorCategory] = None,
    reraise: bool = False,
    default_return: Any = None,
):
    """同步错误处理装饰器

    Args:
        severity: 错误严重程度
        category: 错误类别
        reraise: 是否重新抛出异常
        default_return: 默认返回值

    Usage:
        @sync_error_handler(severity=ErrorSeverity.HIGH)
        def risky_operation():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = get_error_handler()
                error_info = handler.handle_error(
                    error=e,
                    context=func.__qualname__,
                    severity=severity,
                    category=category,
                )

                if reraise:
                    raise

                return default_return

        return wrapper
    return decorator


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None,
):
    """重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟倍数
        exceptions: 需要重试的异常类型
        on_retry: 重试时的回调函数

    Usage:
        @retry_on_error(max_retries=3, delay=1.0)
        async def flaky_operation():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        if on_retry:
                            on_retry(attempt + 1, e)

                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__qualname__}: {e}"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_retries} retries failed for {func.__qualname__}: {e}"
                        )

            raise last_exception

        return wrapper
    return decorator


@asynccontextmanager
async def ErrorContext(
    context_name: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    reraise: bool = True,
):
    """异步错误上下文管理器

    Args:
        context_name: 上下文名称
        severity: 错误严重程度
        reraise: 是否重新抛出异常

    Usage:
        async with ErrorContext("my_operation"):
            await risky_operation()
    """
    try:
        yield
    except Exception as e:
        handler = get_error_handler()
        handler.handle_error(
            error=e,
            context=context_name,
            severity=severity,
        )

        if reraise:
            raise


def handle_llm_error(error: Exception, context: str = "") -> ErrorInfo:
    """处理 LLM 相关错误

    Args:
        error: 异常对象
        context: 错误上下文

    Returns:
        ErrorInfo: 错误信息
    """
    handler = get_error_handler()

    # 判断是否可重试
    retryable = isinstance(error, (TimeoutError, ConnectionError))

    return handler.handle_error(
        error=error,
        context=context or "LLM operation",
        severity=ErrorSeverity.MEDIUM,
        category=ErrorCategory.LLM,
        metadata={"retryable": retryable},
    )


def handle_attack_error(error: Exception, context: str = "") -> ErrorInfo:
    """处理攻击相关错误

    Args:
        error: 异常对象
        context: 错误上下文

    Returns:
        ErrorInfo: 错误信息
    """
    handler = get_error_handler()
    return handler.handle_error(
        error=error,
        context=context or "Attack operation",
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.ATTACK,
    )


def handle_evaluation_error(error: Exception, context: str = "") -> ErrorInfo:
    """处理评估相关错误

    Args:
        error: 异常对象
        context: 错误上下文

    Returns:
        ErrorInfo: 错误信息
    """
    handler = get_error_handler()
    return handler.handle_error(
        error=error,
        context=context or "Evaluation operation",
        severity=ErrorSeverity.MEDIUM,
        category=ErrorCategory.EVALUATION,
    )


def create_error_response(
    error: Exception,
    context: str = "",
    default_score: float = 0.0,
) -> Dict[str, Any]:
    """创建错误响应

    Args:
        error: 异常对象
        context: 错误上下文
        default_score: 默认分数

    Returns:
        Dict: 错误响应
    """
    handler = get_error_handler()
    error_info = handler.handle_error(
        error=error,
        context=context,
    )

    return {
        "success": False,
        "score": default_score,
        "error": str(error),
        "error_type": type(error).__name__,
        "error_category": error_info.category.value,
        "error_severity": error_info.severity.value,
        "retryable": error_info.retryable,
    }


__all__ = [
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorInfo",
    "MoxError",
    "AttackError",
    "EvaluationError",
    "LLMError",
    "TimeoutError",
    "ErrorHandler",
    "get_error_handler",
    "async_error_handler",
    "sync_error_handler",
    "retry_on_error",
    "ErrorContext",
    "handle_llm_error",
    "handle_attack_error",
    "handle_evaluation_error",
    "create_error_response",
]
