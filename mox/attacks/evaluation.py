"""Attack evaluation module — backward-compatible thin wrapper.

All implementations now live in mox.core.evaluation and mox.core.patterns.
This file re-exports them for backward compatibility.
"""

from mox.core.evaluation import (
    EvaluationResult,
    AttackEvaluator as BaseAttackEvaluator,
    KeywordOverlapEvaluator,
    RefusalPatternEvaluator,
    LLMBasedEvaluator,
    CompositeEvaluator,
    get_default_evaluator,
    create_evaluator,
)

from mox.core.patterns import RefusalPatterns


class AttackEvaluator(BaseAttackEvaluator):
    """Backward-compatible concrete AttackEvaluator.

    Previous versions allowed direct instantiation. This concrete subclass
    delegates to RefusalPatternEvaluator by default.
    """

    def __init__(self, config=None, **kwargs):
        self._delegate = RefusalPatternEvaluator()
        self.config = config

    async def evaluate(self, response: str, target_behavior: str) -> EvaluationResult:
        return await self._delegate.evaluate(response, target_behavior)


__all__ = [
    "EvaluationResult",
    "AttackEvaluator",
    "KeywordOverlapEvaluator",
    "RefusalPatternEvaluator",
    "LLMBasedEvaluator",
    "CompositeEvaluator",
    "get_default_evaluator",
    "create_evaluator",
    "RefusalPatterns",
]
