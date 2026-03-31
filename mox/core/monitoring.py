"""异常检测系统

提供:
1. Token 用量异常检测
2. 请求频率异常检测
3. 行为异常检测
4. 实时告警
5. 性能监控装饰器
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import statistics
import functools
from collections import deque


class AlertLevel(Enum):
    """告警级别"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Anomaly:
    """异常事件"""

    anomaly_id: str
    type: str
    level: AlertLevel
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class AlertRule:
    """告警规则"""

    name: str
    metric: str
    threshold: float
    operator: str = ">"
    level: AlertLevel = AlertLevel.WARNING


class AnomalyDetector:
    """异常检测器

    使用示例:
        detector = AnomalyDetector()

        # 添加规则
        detector.add_rule(AlertRule(
            name="high_latency",
            metric="latency.ms",
            threshold=5000,
            level=AlertLevel.WARNING
        ))

        # 检测
        anomaly = detector.detect(latency_ms=6000)
    """

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.rules: List[AlertRule] = []
        self.history: Dict[str, deque] = {}
        self.anomalies: List[Anomaly] = []
        self.alert_callbacks: List[Callable[[Anomaly], None]] = []

    def add_rule(self, rule: AlertRule):
        """添加规则"""
        self.rules.append(rule)

    def add_callback(self, callback: Callable[[Anomaly], None]):
        """添加告警回调"""
        self.alert_callbacks.append(callback)

    def record(self, metric: str, value: float):
        """记录指标值"""
        if metric not in self.history:
            self.history[metric] = deque(maxlen=self.window_size)

        self.history[metric].append(value)

    def detect(self, **metrics) -> Optional[Anomaly]:
        """检测异常"""

        for rule in self.rules:
            if rule.metric not in metrics:
                continue

            value = metrics[rule.metric]
            self.record(rule.metric, value)

            is_anomaly = self._check_rule(rule, value)

            if is_anomaly:
                anomaly = Anomaly(
                    anomaly_id=f"{rule.name}_{int(time.time())}",
                    type=rule.name,
                    level=rule.level,
                    message=f"{rule.name}: {value} {rule.operator} {rule.threshold}",
                    details={
                        "metric": rule.metric,
                        "value": value,
                        "threshold": rule.threshold,
                    },
                )

                self.anomalies.append(anomaly)

                for callback in self.alert_callbacks:
                    try:
                        callback(anomaly)
                    except Exception:
                        pass

                return anomaly

        return None

    def _check_rule(self, rule: AlertRule, value: float) -> bool:
        """检查规则"""

        if rule.operator == ">":
            return value > rule.threshold
        elif rule.operator == "<":
            return value < rule.threshold
        elif rule.operator == ">=":
            return value >= rule.threshold
        elif rule.operator == "<=":
            return value <= rule.threshold
        elif rule.operator == "==":
            return value == rule.threshold

        return False

    def detect_statistical(self, metric: str, value: float, std_threshold: float = 2.0) -> bool:
        """统计异常检测"""

        if metric not in self.history or len(self.history[metric]) < 10:
            return False

        values = list(self.history[metric])
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0

        if stdev == 0:
            return False

        z_score = abs((value - mean) / stdev)

        return z_score > std_threshold

    def get_anomalies(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取异常列表"""
        anomalies = sorted(self.anomalies, key=lambda x: x.timestamp, reverse=True)

        return [
            {
                "anomaly_id": a.anomaly_id,
                "type": a.type,
                "level": a.level.value,
                "message": a.message,
                "details": a.details,
                "timestamp": a.timestamp,
            }
            for a in anomalies[:limit]
        ]

    def clear_anomalies(self):
        """清除异常历史"""
        self.anomalies.clear()


class TokenUsageMonitor:
    """Token 使用监控"""

    def __init__(self, detector: AnomalyDetector):
        self.detector = detector
        self.daily_usage: Dict[str, int] = {}
        self.reset_date: Optional[str] = None

    def record_usage(self, user_id: str, tokens: int):
        """记录使用量"""
        today = time.strftime("%Y-%m-%d")

        if self.reset_date != today:
            self.daily_usage.clear()
            self.reset_date = today

        self.daily_usage[user_id] = self.daily_usage.get(user_id, 0) + tokens

        self.detector.record(f"tokens.{user_id}", tokens)
        self.detector.record("tokens.daily.total", tokens)

    def check_limit(self, user_id: str, limit: int) -> bool:
        """检查是否超限"""
        return self.daily_usage.get(user_id, 0) > limit


class RequestRateLimiter:
    """请求频率限制器"""

    def __init__(
        self,
        requests_per_minute: int = 60,
        detector: Optional[AnomalyDetector] = None,
    ):
        self.requests_per_minute = requests_per_minute
        self.detector = detector
        self.requests: Dict[str, deque] = {}

    def is_allowed(self, user_id: str) -> bool:
        """检查是否允许请求"""
        now = time.time()
        minute_ago = now - 60

        if user_id not in self.requests:
            self.requests[user_id] = deque()

        user_requests = self.requests[user_id]

        while user_requests and user_requests[0] < minute_ago:
            user_requests.popleft()

        if len(user_requests) >= self.requests_per_minute:
            if self.detector:
                self.detector.detect(
                    type="rate_limit",
                    metric="requests.rate",
                    value=len(user_requests),
                    threshold=self.requests_per_minute,
                )
            return False

        user_requests.append(now)
        return True

    def get_remaining(self, user_id: str) -> int:
        """获取剩余请求数"""
        now = time.time()
        minute_ago = now - 60

        if user_id not in self.requests:
            return self.requests_per_minute

        user_requests = self.requests[user_id]

        recent = sum(1 for t in user_requests if t >= minute_ago)

        return max(0, self.requests_per_minute - recent)


class SecurityMonitor:
    """安全监控"""

    def __init__(self, detector: AnomalyDetector):
        self.detector = detector
        self.blocked_ips: Dict[str, int] = {}
        self.failed_auth: Dict[str, List[float]] = {}

    def record_block(self, ip: str, reason: str):
        """记录拦截"""
        self.blocked_ips[ip] = self.blocked_ips.get(ip, 0) + 1

        if self.blocked_ips[ip] > 10:
            self.detector.detect(
                type="ddos",
                metric="security.blocks",
                value=self.blocked_ips[ip],
                threshold=10,
            )

    def record_failed_auth(self, identifier: str):
        """记录认证失败"""
        now = time.time()

        if identifier not in self.failed_auth:
            self.failed_auth[identifier] = deque(maxlen=10)

        self.failed_auth[identifier].append(now)

        if len(self.failed_auth[identifier]) >= 5:
            self.detector.detect(
                type="brute_force",
                metric="security.auth_failures",
                value=len(self.failed_auth[identifier]),
                threshold=5,
            )


class MonitoringDashboard:
    """监控面板数据聚合"""

    def __init__(self):
        self.detector = AnomalyDetector()
        self.token_monitor = TokenUsageMonitor(self.detector)
        self.rate_limiter = RequestRateLimiter(detector=self.detector)
        self.security = SecurityMonitor(self.detector)

        self._setup_default_rules()

    def _setup_default_rules(self):
        """设置默认规则"""
        self.detector.add_rule(
            AlertRule(
                name="high_latency",
                metric="latency.ms",
                threshold=5000,
                level=AlertLevel.WARNING,
            )
        )

        self.detector.add_rule(
            AlertRule(
                name="high_error_rate",
                metric="errors.rate",
                threshold=0.1,
                level=AlertLevel.ERROR,
            )
        )

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取面板数据"""
        metrics = self.detector.history

        dashboard_data = {
            "metrics": {},
            "anomalies": self.detector.get_anomalies(limit=10),
            "rate_limits": {},
            "timestamp": time.time(),
        }

        for metric, values in metrics.items():
            if values:
                vals = list(values)
                dashboard_data["metrics"][metric] = {
                    "current": vals[-1] if vals else 0,
                    "min": min(vals),
                    "max": max(vals),
                    "avg": statistics.mean(vals),
                    "count": len(vals),
                }

        return dashboard_data


__all__ = [
    "AnomalyDetector",
    "Anomaly",
    "AlertLevel",
    "AlertRule",
    "TokenUsageMonitor",
    "RequestRateLimiter",
    "SecurityMonitor",
    "MonitoringDashboard",
    "timed",
    "async_timed",
]


_metrics: Dict[str, deque] = {}


def timed(func: Callable) -> Callable:
    """同步函数性能监控装饰器"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        name = f"{func.__module__}.{func.__name__}"
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = (time.perf_counter() - start) * 1000
            if name not in _metrics:
                _metrics[name] = deque(maxlen=1000)
            _metrics[name].append(duration)

    return wrapper


def async_timed(func: Callable) -> Callable:
    """异步函数性能监控装饰器"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        name = f"{func.__module__}.{func.__name__}"
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = (time.perf_counter() - start) * 1000
            if name not in _metrics:
                _metrics[name] = deque(maxlen=1000)
            _metrics[name].append(duration)

    return wrapper


def get_metrics(name: Optional[str] = None) -> Dict[str, Any]:
    """获取性能指标"""
    if name:
        data = list(_metrics.get(name, []))
        if not data:
            return {}
        return {
            "name": name,
            "count": len(data),
            "mean_ms": statistics.mean(data),
            "min_ms": min(data),
            "max_ms": max(data),
            "p50_ms": statistics.median(data),
            "p95_ms": sorted(data)[int(len(data) * 0.95)] if len(data) > 20 else data[-1],
            "p99_ms": sorted(data)[int(len(data) * 0.99)] if len(data) > 100 else data[-1],
        }
    return {
        name: {
            "count": len(data),
            "mean_ms": statistics.mean(data),
        }
        for name, data in _metrics.items()
        if data
    }


def reset_metrics() -> None:
    """重置所有指标"""
    _metrics.clear()
