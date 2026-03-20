"""攻击基类"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from mox.core import (
    BaseLLM,
    Message,
    AttackType,
    AttackPayload,
    AttackOutcome,
    AttackResult,
    settings,
)


@dataclass
class AttackConfig:
    max_iterations: int = 100
    success_threshold: float = 0.8
    temperature: float = 0.7
    verbose: bool = False


class BaseAttack(ABC):
    """攻击基类"""

    attack_type: AttackType

    def __init__(
        self,
        target_llm: BaseLLM,
        config: Optional[AttackConfig] = None,
    ):
        self.target_llm = target_llm
        self.config = config or AttackConfig()
        self.history: List[AttackOutcome] = []

    @abstractmethod
    async def generate_attack(
        self,
        payload: AttackPayload,
    ) -> AttackOutcome:
        pass

    @abstractmethod
    async def evaluate_success(
        self,
        response: str,
        target_behavior: str,
    ) -> float:
        pass

    def _create_outcome(
        self,
        result: AttackResult,
        original_prompt: str,
        adversarial_prompt: str,
        model_response: str,
        iterations: int,
        success_score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AttackOutcome:
        outcome = AttackOutcome(
            result=result,
            original_prompt=original_prompt,
            adversarial_prompt=adversarial_prompt,
            model_response=model_response,
            iterations=iterations,
            success_score=success_score,
            metadata=metadata or {},
        )
        self.history.append(outcome)
        return outcome

    async def run_batch(
        self,
        payloads: List[AttackPayload],
    ) -> List[AttackOutcome]:
        results = []
        for payload in payloads:
            outcome = await self.generate_attack(payload)
            results.append(outcome)
        return results

    def get_statistics(self) -> Dict[str, Any]:
        if not self.history:
            return {"total": 0}

        successful = sum(1 for o in self.history if o.result == AttackResult.SUCCESS)
        total = len(self.history)

        return {
            "total": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total if total > 0 else 0,
            "avg_iterations": sum(o.iterations for o in self.history) / total,
        }
