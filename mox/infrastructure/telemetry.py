"""OpenTelemetry 集成 - 可观测性基础设施

提供:
1. 分布式追踪
2. 指标收集
3. 日志聚合
4. 自定义 span 属性
"""

import threading
import logging

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager
import time

from mox.infrastructure.logging import get_logger

logger = get_logger("telemetry")


try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.semconv.resource import ResourceAttributes
    from opentelemetry import metrics

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False


@dataclass
class TelemetryConfig:
    """遥测配置"""

    service_name: str = "mox"
    otlp_endpoint: str = "http://localhost:4317"
    log_level: str = "INFO"
    sample_rate: float = 1.0
    enable_traces: bool = True
    enable_metrics: bool = True
    enable_logs: bool = True


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}

    def increment(self, name: str, value: float = 1.0):
        """递增计数器"""
        self.counters[name] = self.counters.get(name, 0) + value

    def set_gauge(self, name: str, value: float):
        """设置仪表值"""
        self.gauges[name] = value

    def record_histogram(self, name: str, value: float):
        """记录直方图值"""
        if name not in self.histograms:
            self.histograms[name] = []
        self.histograms[name].append(value)
        if len(self.histograms[name]) > 1000:
            self.histograms[name] = self.histograms[name][-1000:]

    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        return {
            "counters": self.counters.copy(),
            "gauges": self.gauges.copy(),
            "histograms": {
                k: {
                    "count": len(v),
                    "min": min(v) if v else 0,
                    "max": max(v) if v else 0,
                    "avg": sum(v) / len(v) if v else 0,
                }
                for k, v in self.histograms.items()
            },
        }


class MoxTelemetry:
    """Mox 遥测系统

    使用示例:
        telemetry = MoxTelemetry()

        # 追踪 LLM 调用
        with telemetry.trace("llm.generate") as span:
            span.set_attribute("model", "gpt-4")
            response = await llm.generate(messages)

        # 记录指标
        telemetry.increment("request.count")
        telemetry.record_latency("latency.ms", 150)
    """

    def __init__(
        self,
        config: Optional[TelemetryConfig] = None,
    ):
        self.config = config or TelemetryConfig()
        self.metrics = MetricsCollector()
        self._tracer = None
        self._meter = None

        if OPENTELEMETRY_AVAILABLE:
            self._setup_opentelemetry()

    def _setup_opentelemetry(self):
        """设置 OpenTelemetry"""

        resource = Resource.create(
            {
                ResourceAttributes.SERVICE_NAME: self.config.service_name,
                ResourceAttributes.SERVICE_VERSION: "0.1.0",
            }
        )

        if self.config.enable_traces:
            provider = TracerProvider(resource=resource)

            try:
                exporter = OTLPSpanExporter(endpoint=self.config.otlp_endpoint)
                processor = BatchSpanProcessor(exporter)
                provider.add_span_processor(processor)
            except Exception as e:
                logger.warning(f"Failed to set up OTLP span exporter: {e}")

            trace.set_tracer_provider(provider)
            self._tracer = trace.get_tracer(__name__)

        if self.config.enable_metrics:
            try:
                self._meter = metrics.get_meter(__name__)
            except Exception as e:
                logger.warning(f"Failed to set up metrics meter: {e}")

    @asynccontextmanager
    def trace(self, name: str, **attributes):
        """追踪 span"""

        if self._tracer:
            with self._tracer.start_as_current_span(name) as span:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))

                start_time = time.time()
                try:
                    yield span
                except Exception as e:
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
                    raise
                finally:
                    duration = (time.time() - start_time) * 1000
                    span.set_attribute("duration.ms", duration)
                    self.metrics.record_histogram(f"{name}.duration_ms", duration)
        else:
            yield None

    def increment(self, name: str, value: float = 1.0):
        """递增指标"""
        self.metrics.increment(name, value)

        if self._meter and OPENTELEMETRY_AVAILABLE:
            try:
                counter = self._meter.create_counter(name)
                counter.add(value)
            except Exception as e:
                logger.debug(f"Failed to create OpenTelemetry counter: {e}")

    def record_latency(self, name: str, latency_ms: float):
        """记录延迟"""
        self.metrics.record_histogram(name, latency_ms)

    def set_gauge(self, name: str, value: float):
        """设置仪表"""
        self.metrics.set_gauge(name, value)

    def record_request(
        self,
        model: str,
        success: bool,
        latency_ms: float,
        tokens: int = 0,
    ):
        """记录请求"""
        self.increment("llm.requests.total")
        self.increment(f"llm.requests.{'success' if success else 'error'}")
        self.record_latency("llm.latency.ms", latency_ms)

        if tokens > 0:
            self.metrics.record_histogram("llm.tokens.total", tokens)

    def record_defense(
        self,
        defense_type: str,
        blocked: bool,
        confidence: float,
    ):
        """记录防御事件"""
        self.increment(f"defense.{defense_type}.total")
        if blocked:
            self.increment(f"defense.{defense_type}.blocked")

        self.metrics.record_histogram(f"defense.{defense_type}.confidence", confidence)

    def record_attack(
        self,
        attack_type: str,
        success: bool,
    ):
        """记录攻击事件"""
        self.increment(f"attack.{attack_type}.total")
        if success:
            self.increment(f"attack.{attack_type}.success")

    def get_summary(self) -> Dict[str, Any]:
        """获取遥测摘要"""
        return {
            "service": self.config.service_name,
            "metrics": self.metrics.get_metrics(),
            "timestamp": time.time(),
        }


class LLMObservable:
    """LLM 可观测性包装器"""

    def __init__(self, llm, telemetry: MoxTelemetry):
        self.llm = llm
        self.telemetry = telemetry

    async def generate(self, messages: List, **kwargs):
        """带追踪的生成"""

        model = kwargs.get("model", getattr(self.llm, "model", "unknown"))

        with self.telemetry.trace("llm.generate", model=model) as span:
            start = time.time()

            try:
                response = await self.llm.generate(messages, **kwargs)

                latency_ms = (time.time() - start) * 1000
                tokens = response.usage.get("total_tokens", 0) if response.usage else 0

                self.telemetry.record_request(
                    model=model,
                    success=True,
                    latency_ms=latency_ms,
                    tokens=tokens,
                )

                if span:
                    span.set_attribute("success", True)
                    span.set_attribute("tokens", tokens)

                return response

            except Exception as e:
                latency_ms = (time.time() - start) * 1000

                self.telemetry.record_request(
                    model=model,
                    success=False,
                    latency_ms=latency_ms,
                )

                if span:
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))

                raise


_global_telemetry: Optional[MoxTelemetry] = None
_telemetry_lock = threading.Lock()


def get_telemetry(config: Optional[TelemetryConfig] = None) -> MoxTelemetry:
    """获取全局遥测实例"""
    global _global_telemetry

    if _global_telemetry is None:
        with _telemetry_lock:
            if _global_telemetry is None:
                _global_telemetry = MoxTelemetry(config)

    return _global_telemetry


def observe_llm(llm, telemetry: Optional[MoxTelemetry] = None):
    """为 LLM 添加可观测性"""
    tel = telemetry or get_telemetry()
    return LLMObservable(llm, tel)


__all__ = [
    "MoxTelemetry",
    "LLMObservable",
    "MetricsCollector",
    "TelemetryConfig",
    "get_telemetry",
    "observe_llm",
    "OPENTELEMETRY_AVAILABLE",
]
