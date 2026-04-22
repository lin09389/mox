"""防御基类"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from mox.core import DefenseType, DefenseResult
from .registry import DEFENSE_REGISTRY


@dataclass
class DefenseConfig:
    enabled: bool = True
    confidence_threshold: float = 0.7
    sanitize_enabled: bool = True
    verbose: bool = False


class BaseDefense(ABC):
    """防御基类"""

    defense_type: DefenseType

    def __init__(self, config: Optional[DefenseConfig] = None):
        self.config = config or DefenseConfig()
        self.detection_history: List[DefenseResult] = []
        self._history_lock = asyncio.Lock()  # Thread-safety for shared list

    @abstractmethod
    async def detect(self, input_text: str) -> DefenseResult:
        pass

    @abstractmethod
    async def sanitize(self, input_text: str) -> str:
        pass

    async def _create_result(
        self,
        is_malicious: bool,
        confidence: float,
        detected_patterns: List[str],
        sanitized_input: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DefenseResult:
        result = DefenseResult(
            is_malicious=is_malicious,
            confidence=confidence,
            detected_patterns=detected_patterns,
            sanitized_input=sanitized_input,
            metadata=metadata or {},
        )
        async with self._history_lock:
            self.detection_history.append(result)
        return result

    def get_statistics(self) -> Dict[str, Any]:
        if not self.detection_history:
            return {"total": 0}

        total = len(self.detection_history)
        malicious = sum(1 for r in self.detection_history if r.is_malicious)

        return {
            "total": total,
            "malicious_detected": malicious,
            "clean": total - malicious,
            "detection_rate": malicious / total if total > 0 else 0,
            "avg_confidence": sum(r.confidence for r in self.detection_history) / total,
        }
