"""Attack evaluation module — backward-compatible thin wrapper.

All implementations now live in mox.core.evaluation and mox.core.patterns.
This file re-exports them for backward compatibility.
"""

# Import from the unified core module
from mox.core.evaluation import (
    EvaluationResult,
    AttackEvaluator,
    KeywordOverlapEvaluator,
    RefusalPatternEvaluator,
    LLMBasedEvaluator,
    CompositeEvaluator,
    get_default_evaluator,
    create_evaluator,
)

# Also import patterns for backward compatibility with code that
# imported refusal patterns from this module
from mox.core.patterns import RefusalPatterns

__all__ = [
    "EvaluationResult",
    "AttackEvaluator",
    "KeywordOverlapEvaluator",
    "RefusalPatternEvaluator",
    "LLMBasedEvaluator",
    "CompositeEvaluator",
    "get_default_evaluator",
    "create_evaluator",
    # Backward compat re-exports
    "RefusalPatterns",
]
