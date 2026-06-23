"""Canonical evaluation orchestration types (single source of truth)."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict


class EvaluationType(Enum):
    """评估类型"""

    ATTACK = "attack"
    DEFENSE = "defense"
    REDTEAM = "redteam"
    BENCHMARK = "benchmark"
    JUDGE = "judge"


class EvaluationStatus(Enum):
    """评估状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EvaluationConfig:
    """评估配置"""

    evaluation_type: EvaluationType = EvaluationType.ATTACK
    parallel: bool = True
    max_concurrency: int = 5
    judge_mode: str = "pattern"
    generate_reports: bool = True
    output_format: str = "markdown"


@dataclass
class EvaluationScenario:
    """评估场景"""

    scenario_id: str
    name: str
    description: str
    evaluation_type: EvaluationType
    target: str
    payload: str
    expected_result: str
    difficulty: str = "medium"
    category: str = "general"


@dataclass
class EvaluationResult:
    """统一编排层评估结果（canonical）"""

    scenario: EvaluationScenario
    success: bool
    score: float
    details: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    timestamp: str = ""


__all__ = [
    "EvaluationType",
    "EvaluationStatus",
    "EvaluationConfig",
    "EvaluationScenario",
    "EvaluationResult",
]
