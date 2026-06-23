"""攻击基类

提供统一的攻击接口和错误处理机制。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass

from mox.core import (
    BaseLLM,
    AttackType,
    AttackPayload,
    AttackOutcome,
    AttackResult,
)
from mox.core.logging import get_logger
from mox.core.error_handling import (
    handle_attack_error,
    handle_evaluation_error,
)

if TYPE_CHECKING:
    pass


def _create_attack_evaluator(evaluator_type: str):
    from mox.evaluation.attack_success import create_evaluator

    return create_evaluator(evaluator_type)


logger = get_logger("attacks.base")


@dataclass
class AttackConfig:
    """攻击配置基类"""

    max_iterations: int = 100
    success_threshold: float = 0.8
    temperature: float = 0.7
    verbose: bool = False
    timeout: int = 300  # 超时时间（秒）
    evaluator_type: str = "default"  # 评估器类型


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
        evaluator: Optional[Any] = None,
    ):
        self.target_llm = target_llm
        self.config = config or AttackConfig()
        self.evaluator = evaluator or _create_attack_evaluator(self.config.evaluator_type)
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
        **kwargs,
    ) -> float:
        """评估攻击是否成功

        默认使用配置的评估器，可被子类重写

        Args:
            response: 模型响应
            target_behavior: 目标行为
            **kwargs: 额外参数（如原始提示、攻击类型等）

        Returns:
            float: 成功分数 0.0-1.0
        """
        try:
            result = await self.evaluator.evaluate(response, target_behavior, **kwargs)
            return result.score
        except Exception as e:
            handle_evaluation_error(e, f"Evaluating attack success for {self.__class__.__name__}")
            return 0.0

    async def evaluate_attack(
        self,
        response: str,
        target_behavior: str,
        **kwargs,
    ) -> Any:
        """评估攻击并返回详细结果"""
        from mox.evaluation.attack_success import AttackSuccessResult

        try:
            return await self.evaluator.evaluate(response, target_behavior, **kwargs)
        except Exception as e:
            handle_evaluation_error(e, f"Evaluating attack for {self.__class__.__name__}")
            return AttackSuccessResult(
                score=0.0,
                is_successful=False,
                confidence=0.0,
                reasoning=f"Evaluation error: {str(e)}",
                metadata={"error": str(e)},
            )

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

    def _create_error_outcome(
        self,
        error: Exception,
        payload: AttackPayload,
        iterations: int = 1,
    ) -> AttackOutcome:
        """创建错误结果

        Args:
            error: 异常对象
            payload: 攻击载荷
            iterations: 迭代次数

        Returns:
            AttackOutcome: 错误结果
        """
        # 记录错误
        error_info = handle_attack_error(
            error,
            f"{self.__class__.__name__}.generate_attack",
        )

        return self._create_outcome(
            result=AttackResult.ERROR,
            original_prompt=payload.prompt,
            adversarial_prompt="",
            model_response=str(error),
            iterations=iterations,
            success_score=0.0,
            metadata={
                "error": str(error),
                "error_type": type(error).__name__,
                "error_category": error_info.category.value,
                "error_severity": error_info.severity.value,
                "retryable": error_info.retryable,
            },
        )

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
                outcome = self._create_error_outcome(e, payload)
                results.append(outcome)
        return results

    async def run_batch_parallel(
        self,
        payloads: List[AttackPayload],
        max_concurrency: int = 5,
    ) -> List[AttackOutcome]:
        """并行批量执行攻击

        Args:
            payloads: 攻击载荷列表
            max_concurrency: 最大并发数

        Returns:
            List[AttackOutcome]: 攻击结果列表
        """
        import asyncio

        semaphore = asyncio.Semaphore(max_concurrency)

        async def run_with_limit(payload: AttackPayload) -> AttackOutcome:
            async with semaphore:
                try:
                    return await self.generate_attack(payload)
                except Exception as e:
                    logger.error(f"Attack failed for payload: {e}")
                    return self._create_error_outcome(e, payload)

        tasks = [run_with_limit(p) for p in payloads]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(self._create_error_outcome(result, payloads[i]))
            else:
                final_results.append(result)

        return final_results

    def get_statistics(self) -> Dict[str, Any]:
        """获取攻击统计"""
        if not self.history:
            return {"total": 0}

        successful = sum(1 for o in self.history if o.result == AttackResult.SUCCESS)
        failed = sum(1 for o in self.history if o.result == AttackResult.FAILURE)
        errors = sum(1 for o in self.history if o.result == AttackResult.ERROR)
        total = len(self.history)

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "errors": errors,
            "success_rate": successful / total if total > 0 else 0,
            "error_rate": errors / total if total > 0 else 0,
            "avg_iterations": (sum(o.iterations for o in self.history) / total if total > 0 else 0),
        }

    def clear_history(self) -> None:
        """清除攻击历史"""
        self.history.clear()
