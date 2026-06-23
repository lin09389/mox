"""Attack success evaluation — re-exports from mox.evaluation.attack_success.

Canonical types live in ``mox.evaluation.attack_success`` to avoid naming
conflicts with ``mox.evaluation.framework.EvaluationResult`` and
``mox.evaluation.attack_evaluator.AttackEvaluator``.
"""

import warnings

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

warnings.warn(
    "Import attack-success evaluators from mox.evaluation.attack_success; "
    "mox.attacks.evaluation re-exports are deprecated.",
    DeprecationWarning,
    stacklevel=2,
)

# Backward-compatible aliases (remove in v0.7.0)
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