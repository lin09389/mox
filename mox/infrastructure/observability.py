"""增强的可观测性模块

提供:
1. 结构化 JSON 日志
2. OpenTelemetry 分布式追踪
3. Prometheus 指标导出
4. 健康检查端点
"""

import json
import time
import logging
import traceback
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import contextmanager
from functools import wraps


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """结构化日志条目"""

    timestamp: str
    level: str
    logger: str
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


class StructuredLogger:
    """结构化日志器"""

    _instance: Optional["StructuredLogger"] = None

    def __init__(
        self,
        name: str = "mox",
        log_level: str = "INFO",
        enable_console: bool = True,
        enable_file: bool = True,
        log_dir: str = "./logs",
        json_format: bool = True,
    ):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.json_format = json_format
        self._trace_id: Optional[str] = None
        self._user_id: Optional[str] = None
        self._session_id: Optional[str] = None

        if not self.logger.handlers:
            if enable_console:
                self._setup_console_handler()
            if enable_file:
                self._setup_file_handler(log_dir)

    @classmethod
    def get_instance(cls, **kwargs) -> "StructuredLogger":
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    def _setup_console_handler(self):
        handler = logging.StreamHandler()
        if self.json_format:
            handler.setFormatter(JsonFormatter())
        else:
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)-8s | %(name)s | %(trace_id)s | %(message)s"
                )
            )
        self.logger.addHandler(handler)

    def _setup_file_handler(self, log_dir: str):
        from pathlib import Path

        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        handler = logging.FileHandler(log_path / "mox.jsonl", encoding="utf-8")
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)

    def set_context(
        self,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """设置日志上下文"""
        if trace_id:
            self._trace_id = trace_id
        if user_id:
            self._user_id = user_id
        if session_id:
            self._session_id = session_id

    def clear_context(self):
        """清除日志上下文"""
        self._trace_id = None
        self._user_id = None
        self._session_id = None

    def _log(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ):
        extra = extra or {}

        extra_data = {
            "trace_id": self._trace_id,
            "user_id": self._user_id,
            "session_id": self._session_id,
            **extra,
        }

        log_func = getattr(self.logger, level.lower())

        if self.json_format:
            extra_data["message"] = message
            log_func(
                json.dumps(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                        "level": level,
                        "logger": self.name,
                        **extra_data,
                    }
                )
            )
        else:
            log_func(message, extra=extra_data)

        if exc_info:
            self.logger.error(traceback.format_exc())

    def debug(self, message: str, **extra):
        self._log("DEBUG", message, extra)

    def info(self, message: str, **extra):
        self._log("INFO", message, extra)

    def warning(self, message: str, **extra):
        self._log("WARNING", message, extra)

    def error(self, message: str, **extra):
        self._log("ERROR", message, extra, exc_info=True)

    def critical(self, message: str, **extra):
        self._log("CRITICAL", message, extra, exc_info=True)

    def log_attack(
        self,
        attack_type: str,
        success: bool,
        duration: float,
        model: str,
        **extra,
    ):
        """记录攻击事件"""
        self.info(
            f"Attack executed: {attack_type}",
            event_type="attack",
            attack_type=attack_type,
            success=success,
            duration_ms=duration * 1000,
            model=model,
            **extra,
        )

    def log_defense(
        self,
        defense_type: str,
        detected: bool,
        confidence: float,
        **extra,
    ):
        """记录防御事件"""
        self.info(
            f"Defense executed: {defense_type}",
            event_type="defense",
            defense_type=defense_type,
            detected=detected,
            confidence=confidence,
            **extra,
        )

    def log_llm_request(
        self,
        model: str,
        duration: float,
        tokens: int,
        success: bool,
        **extra,
    ):
        """记录 LLM 请求"""
        self.info(
            f"LLM request: {model}",
            event_type="llm_request",
            model=model,
            duration_ms=duration * 1000,
            tokens=tokens,
            success=success,
            **extra,
        )


class JsonFormatter(logging.Formatter):
    """JSON 格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        try:
            log_data = {
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }

            if hasattr(record, "trace_id") and record.trace_id:
                log_data["trace_id"] = record.trace_id
            if hasattr(record, "user_id") and record.user_id:
                log_data["user_id"] = record.user_id

            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)

            return json.dumps(log_data, ensure_ascii=False)
        except Exception:
            return json.dumps(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                    "level": "ERROR",
                    "message": "Log format error",
                }
            )


def get_structured_logger(name: str = "mox") -> StructuredLogger:
    """获取结构化日志器"""
    return StructuredLogger.get_instance(name=name)


# ============== OpenTelemetry 集成 ==============

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.trace import Status, StatusCode

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False


class ObservabilityManager:
    """可观测性管理器

    统一管理日志、追踪、指标
    """

    def __init__(
        self,
        service_name: str = "mox",
        enable_tracing: bool = True,
        enable_metrics: bool = True,
        enable_logging: bool = True,
        otlp_endpoint: Optional[str] = None,
    ):
        self.service_name = service_name
        self.enable_tracing = enable_tracing and OPENTELEMETRY_AVAILABLE
        self.enable_metrics = enable_metrics and OPENTELEMETRY_AVAILABLE
        self.enable_logging = enable_logging

        self._tracer = None
        self._meter = None
        self._structured_logger = None

        if self.enable_logging:
            self._structured_logger = StructuredLogger.get_instance(name=service_name)

        if self.enable_tracing:
            self._init_tracing(otlp_endpoint)

        if self.enable_metrics:
            self._init_metrics()

    def _init_tracing(self, otlp_endpoint: Optional[str]):
        if not OPENTELEMETRY_AVAILABLE:
            return

        resource = Resource.create({SERVICE_NAME: self.service_name})
        provider = TracerProvider(resource=resource)

        if otlp_endpoint:
            processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
            provider.add_span_processor(processor)
        else:
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer(self.service_name)

        if self.enable_logging:
            LoggingInstrumentor().instrument(set_logging_format=True)

    def _init_metrics(self):
        if not OPENTELEMETRY_AVAILABLE:
            return

        from opentelemetry import metrics
        from opentelemetry.sdk.metrics import MeterProvider

        provider = MeterProvider(resource=Resource.create({SERVICE_NAME: self.service_name}))
        metrics.set_meter_provider(provider)
        self._meter = metrics.get_meter(self.service_name)

        self._init_custom_metrics()

    def _init_custom_metrics(self):
        """初始化自定义指标"""
        if not self._meter:
            return

        self.attack_counter = self._meter.create_counter(
            "mox_attacks_total",
            description="Total number of attacks",
        )

        self.attack_duration = self._meter.create_histogram(
            "mox_attack_duration_seconds",
            description="Attack duration in seconds",
        )

        self.defense_counter = self._meter.create_counter(
            "mox_defenses_total",
            description="Total number of defense checks",
        )

        self.llm_request_counter = self._meter.create_counter(
            "mox_llm_requests_total",
            description="Total LLM API requests",
        )

        self.llm_tokens = self._meter.create_counter(
            "mox_llm_tokens_total",
            description="Total tokens used",
        )

        self.llm_duration = self._meter.create_histogram(
            "mox_llm_request_duration_seconds",
            description="LLM request duration",
        )

    def get_tracer(self):
        """获取追踪器"""
        return self._tracer

    def get_logger(self):
        """获取结构化日志器"""
        return self._structured_logger

    @contextmanager
    def span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """创建追踪 span"""
        if not self._tracer:
            yield None
            return

        with self._tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))

            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def record_attack(
        self,
        attack_type: str,
        success: bool,
        duration: float,
    ):
        """记录攻击指标"""
        if self.attack_counter:
            self.attack_counter.add(1, {"type": attack_type, "success": str(success)})
        if self.attack_duration:
            self.attack_duration.record(duration, {"type": attack_type})

    def record_defense(
        self,
        defense_type: str,
        detected: bool,
    ):
        """记录防御指标"""
        if self.defense_counter:
            self.defense_counter.add(1, {"type": defense_type, "detected": str(detected)})

    def record_llm_request(
        self,
        model: str,
        duration: float,
        tokens: int,
        success: bool,
    ):
        """记录 LLM 请求指标"""
        if self.llm_request_counter:
            self.llm_request_counter.add(1, {"model": model, "success": str(success)})
        if self.llm_tokens:
            self.llm_tokens.add(tokens, {"model": model})
        if self.llm_duration:
            self.llm_duration.record(duration, {"model": model})


# 全局可观测性管理器实例
_observability_manager: Optional[ObservabilityManager] = None


def get_observability_manager(
    service_name: str = "mox",
    **kwargs,
) -> ObservabilityManager:
    """获取可观测性管理器单例"""
    global _observability_manager
    if _observability_manager is None:
        _observability_manager = ObservabilityManager(service_name=service_name, **kwargs)
    return _observability_manager


def observability_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """追踪装饰器"""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            manager = get_observability_manager()
            with manager.span(name, attributes):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    if "attack" in name.lower():
                        manager.record_attack(name, True, duration)
                    return result
                except Exception:
                    duration = time.time() - start_time
                    if "attack" in name.lower():
                        manager.record_attack(name, False, duration)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            manager = get_observability_manager()
            with manager.span(name, attributes):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    if "attack" in name.lower():
                        manager.record_attack(name, True, duration)
                    return result
                except Exception:
                    duration = time.time() - start_time
                    if "attack" in name.lower():
                        manager.record_attack(name, False, duration)
                    raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ============== 健康检查 ==============


@dataclass
class HealthStatus:
    """健康状态"""

    status: str
    checks: Dict[str, Dict[str, Any]]
    timestamp: str


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self._checks: Dict[str, callable] = {}

    def register_check(self, name: str, check_func: callable):
        """注册健康检查"""
        self._checks[name] = check_func

    async def check_all(self) -> HealthStatus:
        """执行所有健康检查"""
        results = {}
        overall_healthy = True

        for name, check_func in self._checks.items():
            try:
                result = await check_func()
                results[name] = {
                    "status": "healthy" if result.get("healthy", False) else "unhealthy",
                    **result,
                }
                if not result.get("healthy", False):
                    overall_healthy = False
            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                overall_healthy = False

        return HealthStatus(
            status="healthy" if overall_healthy else "unhealthy",
            checks=results,
            timestamp=datetime.now(timezone.utc).isoformat() + "Z",
        )


# 全局健康检查器
_health_checker = HealthChecker()


def get_health_checker() -> HealthChecker:
    return _health_checker


def register_default_health_checks():
    """注册默认健康检查"""

    async def check_database():
        try:
            from mox.infrastructure.database import get_db_session

            async with get_db_session() as session:
                await session.execute("SELECT 1")
            return {"healthy": True}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def check_redis():
        try:
            from mox.infrastructure.cache import get_redis_client

            client = get_redis_client()
            client.ping()
            return {"healthy": True}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def check_llm_connection():
        try:
            from mox.core.llm import LLMFactory

            LLMFactory.create_from_model_name("gpt-3.5-turbo")
            return {"healthy": True, "model": "gpt-3.5-turbo"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    checker = get_health_checker()
    checker.register_check("database", check_database)
    checker.register_check("redis", check_redis)
    checker.register_check("llm", check_llm_connection)


__all__ = [
    "StructuredLogger",
    "LogLevel",
    "LogEntry",
    "get_structured_logger",
    "ObservabilityManager",
    "get_observability_manager",
    "observability_span",
    "HealthChecker",
    "HealthStatus",
    "get_health_checker",
    "register_default_health_checks",
]
