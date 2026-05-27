"""防御基类"""

import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from mox.core import DefenseType, DefenseResult
from mox.core.events import event_bus
from mox.infrastructure.logging import get_logger

logger = get_logger("defense.base")


@dataclass
class DefenseConfig:
    enabled: bool = True
    confidence_threshold: float = 0.7
    sanitize_enabled: bool = True
    verbose: bool = False
    save_to_db: bool = False  # hint for event handlers; BaseDefense itself never touches the DB


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
        input_text: str = "",
        model_name: Optional[str] = None,
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

        # Emit event — persistence is handled by subscribers, not this class.
        await event_bus.emit(
            "defense_detected",
            result=result,
            defense=self,
            input_text=input_text,
            model_name=model_name,
            save_to_db=self.config.save_to_db,
        )

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

    async def run_scenario_test(
        self,
        test_input: str,
    ) -> Tuple[bool, bool, float, str, Dict[str, Any], Optional[str]]:
        """Unified scenario test interface used by DefenseOrchestrator.

        Returns:
            (detected, blocked, confidence, sanitized_output, details, error)

        Subclasses with non-standard detection APIs (e.g. HallucinationDetector)
        should override this method.
        """
        try:
            result = await self.detect(test_input)
            return (
                result.is_malicious,
                result.is_malicious,
                result.confidence,
                result.sanitized_input or test_input,
                {"patterns": result.detected_patterns},
                None,
            )
        except Exception as e:
            logger.error("%s error for input: %s", type(self).__name__, e, exc_info=True)
            return False, False, 0.0, test_input, {}, f"{type(self).__name__} error: {e}"
