"""攻击基类"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from mox.core import (
    BaseLLM,
    AttackType,
    AttackPayload,
    AttackOutcome,
    AttackResult,
)
from mox.core.logging import get_logger
from mox.attacks.evaluation import (
    AttackEvaluator,
    EvaluationResult,
    get_default_evaluator,
)

logger = get_logger("attacks.base")


@dataclass
class AttackConfig:
    """攻击配置基类"""
    max_iterations: int = 100
    success_threshold: float = 0.8
    temperature: float = 0.7
    verbose: bool = False
    timeout: int = 300  # 超时时间（秒）


class BaseAttack(ABC):
    """攻击基类

    所有攻击实现应继承此类。
    提供统一的接口和通用功能。
    """

    attack_type: AttackType

    def __init__(
        self,
        target_llm: BaseLLM,
        config: Optional[AttackConfig] = None,
        evaluator: Optional[AttackEvaluator] = None,
    ):
        self.target_llm = target_llm
        self.config = config or AttackConfig()
        self.evaluator = evaluator or get_default_evaluator()
        self.history: List[AttackOutcome] = []

    @abstractmethod
    async def generate_attack(
        self,
        payload: AttackPayload,
    ) -> AttackOutcome:
        """执行攻击并返回结果"""
        pass

    async def evaluate_success(
        self,
        response: str,
        target_behavior: str,
    ) -> float:
        """评估攻击是否成功

        默认使用配置的评估器，可被子类重写
        """
        try:
            result: EvaluationResult = await self.evaluator.evaluate(
                response, target_behavior
            )
            return result.score
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return 0.0

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
        """创建攻击结果"""
        outcome = AttackOutcome(
            result=result,
            original_prompt=original_prompt,
            adversarial_prompt=adversarial_prompt,
            response=model_response,  # AttackOutcome 使用 response 属性
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
        """批量执行攻击"""
        results = []
        for payload in payloads:
            try:
                outcome = await self.generate_attack(payload)
                results.append(outcome)
            except Exception as e:
                logger.error(f"Attack failed for payload: {e}")
                # 创建失败结果
                outcome = self._create_outcome(
                    result=AttackResult.FAILURE,
                    original_prompt=payload.prompt,
                    adversarial_prompt="",
                    model_response="",
                    iterations=0,
                    success_score=0.0,
                    metadata={"error": str(e)},
                )
                results.append(outcome)
        return results

    def get_statistics(self) -> Dict[str, Any]:
        """获取攻击统计"""
        if not self.history:
            return {"total": 0}

        successful = sum(
            1 for o in self.history if o.result == AttackResult.SUCCESS
        )
        total = len(self.history)

        return {
            "total": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total if total > 0 else 0,
            "avg_iterations": (
                sum(o.iterations for o in self.history) / total if total > 0 else 0
            ),
        }

    def clear_history(self) -> None:
        """清除攻击历史"""
        self.history.clear()
