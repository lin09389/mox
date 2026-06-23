"""Prometheus business metrics for attack and defense operations."""

import time
from contextlib import contextmanager
from typing import Generator, Optional

from prometheus_client import Counter, Histogram

ATTACK_REQUESTS = Counter(
    "mox_attack_requests_total",
    "Total attack API requests",
    ["attack_type", "model", "result"],
)

ATTACK_DURATION = Histogram(
    "mox_attack_duration_seconds",
    "Attack execution duration in seconds",
    ["attack_type", "model"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

DEFENSE_REQUESTS = Counter(
    "mox_defense_requests_total",
    "Total defense API requests",
    ["defense_type", "scan_type", "detected"],
)

DEFENSE_DURATION = Histogram(
    "mox_defense_duration_seconds",
    "Defense scan duration in seconds",
    ["defense_type", "scan_type"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)


def record_attack(
    attack_type: str,
    model: str,
    result: str,
    duration_seconds: float,
) -> None:
    ATTACK_REQUESTS.labels(
        attack_type=attack_type,
        model=model,
        result=result,
    ).inc()
    ATTACK_DURATION.labels(attack_type=attack_type, model=model).observe(duration_seconds)


def record_defense(
    defense_type: str,
    scan_type: str,
    detected: bool,
    duration_seconds: float,
) -> None:
    DEFENSE_REQUESTS.labels(
        defense_type=defense_type,
        scan_type=scan_type,
        detected=str(detected).lower(),
    ).inc()
    DEFENSE_DURATION.labels(defense_type=defense_type, scan_type=scan_type).observe(
        duration_seconds
    )


@contextmanager
def track_attack(
    attack_type: str,
    model: str,
) -> Generator[None, None, None]:
    start = time.perf_counter()
    result = "failure"
    try:
        yield
        result = "success"
    except Exception:
        result = "error"
        raise
    finally:
        record_attack(attack_type, model, result, time.perf_counter() - start)


@contextmanager
def track_defense(
    defense_type: str,
    scan_type: str,
    detected: Optional[bool] = None,
) -> Generator[None, None, None]:
    start = time.perf_counter()
    is_detected = detected if detected is not None else False
    try:
        yield
    finally:
        record_defense(defense_type, scan_type, is_detected, time.perf_counter() - start)
