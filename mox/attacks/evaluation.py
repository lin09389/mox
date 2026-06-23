"""Attack success evaluation — re-exports from mox.evaluation.attack_success."""

from mox.evaluation.attack_success import (
    AttackSuccessResult,
    AttackSuccessEvaluator,
    KeywordOverlapEvaluator,
    RefusalPatternEvaluator,
    SemanticEvaluator,
    LLMBasedEvaluator,
    CompositeEvaluator,
    get_default_evaluator,
    create_evaluator,
    evaluate_attack_success,
    is_attack_successful,
)

# Backward-compatible aliases (module-level only, not in attacks.__all__)
EvaluationResult = AttackSuccessResult
AttackEvaluator = AttackSuccessEvaluator

__all__ = [
    "AttackSuccessResult",
    "AttackSuccessEvaluator",
    "EvaluationResult",
    "AttackEvaluator",
    "KeywordOverlapEvaluator",
    "RefusalPatternEvaluator",
    "SemanticEvaluator",
    "LLMBasedEvaluator",
    "CompositeEvaluator",
    "get_default_evaluator",
    "create_evaluator",
    "evaluate_attack_success",
    "is_attack_successful",
]