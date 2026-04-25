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
from mox.core.evaluation import (
    AttackEvaluator,
    EvaluationResult,
    get_default_evaluator,
)
from mox.infrastructure.logging import get_logger

logger = get_logger("attacks.base")


def _get_db():
    """延迟导入以避免循环依赖"""
    try:
        from mox.infrastructure.database import get_database
        return get_database()
    except Exception:
        return None


@dataclass
class AttackConfig:
    """攻击配置基类"""

    max_iterations: int = 100
    success_threshold: float = 0.8
    temperature: float = 0.7
    verbose: bool = False
    timeout: int = 300
    save_to_db: bool = False  # 默认不自动持久化，由调用方控制


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

        Uses the unified evaluator from mox.core.evaluation.
        Subclasses should NOT override this method with custom logic.
        If custom scoring is needed, create a custom AttackEvaluator subclass
        and pass it to the constructor.
        """
        try:
            result: EvaluationResult = await self.evaluator.evaluate(response, target_behavior)
            return result.score
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return 0.0

    async def _create_outcome(
        self,
        result: AttackResult,
        original_prompt: str,
        adversarial_prompt: str,
        model_response: str,
        iterations: int,
        success_score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AttackOutcome:
        """创建攻击结果并持久化到数据库"""
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

        # 自动持久化到数据库
        if self.config.save_to_db:
            db = _get_db()
            if db is not None:
                try:
                    await db.save_attack_record(
                        attack_type=self.attack_type.value if hasattr(self.attack_type, "value") else str(self.attack_type),
                        original_prompt=original_prompt,
                        adversarial_prompt=adversarial_prompt,
                        model_response=model_response,
                        result=result.value if hasattr(result, "value") else str(result),
                        success_score=success_score,
                        iterations=iterations,
                        model_name=getattr(self.target_llm, "model", None),
                        metadata=metadata or {},
                    )
                except Exception as e:
                    logger.warning(f"Failed to save attack record to DB: {e}")

        return outcome

    async def _generate_with_eval(
        self,
        payload: AttackPayload,
        adversarial_prompt: str,
        iterations: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AttackOutcome:
        """Helper to generate response and evaluate success.

        Encapsulates the common pattern of calling the LLM and evaluating the response.
        """
        from mox.core import Message

        try:
            messages = [Message(role="user", content=adversarial_prompt)]
            response = await self.target_llm.generate(messages)

            success_score = await self.evaluate_success(
                response.content, payload.target_behavior
            )

            result = (
                AttackResult.SUCCESS
                if success_score >= self.config.success_threshold
                else AttackResult.FAILURE
            )

            return await self._create_outcome(
                result=result,
                original_prompt=payload.prompt,
                adversarial_prompt=adversarial_prompt,
                model_response=response.content,
                iterations=iterations,
                success_score=success_score,
                metadata=metadata or {},
            )
        except Exception as e:
            logger.error(f"Generation or evaluation failed: {e}")
            return await self._create_outcome(
                result=AttackResult.ERROR,
                original_prompt=payload.prompt,
                adversarial_prompt=adversarial_prompt,
                model_response=str(e),
                iterations=iterations,
                success_score=0.0,
                metadata={"error": str(e)},
            )

    def get_statistics(self) -> Dict[str, Any]:
        """获取攻击统计"""
        if not self.history:
            return {"total": 0}

        successful = sum(1 for o in self.history if o.result == AttackResult.SUCCESS)
        total = len(self.history)

        return {
            "total": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total if total > 0 else 0,
            "avg_iterations": (sum(o.iterations for o in self.history) / total if total > 0 else 0),
        }

    def clear_history(self) -> None:
        """清除攻击历史"""
        self.history.clear()
