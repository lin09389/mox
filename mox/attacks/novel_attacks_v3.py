"""Compatibility shim — re-exports the novel attack classes that previously
lived in a separate ``novel_attacks_v3.py`` module.

The real implementations have been consolidated into
:mod:`mox.attacks.novel_attacks` (see the docstring there for details).
This module exists so that legacy imports of the form
``from mox.attacks.novel_attacks_v3 import ManyShotJailbreakAttack`` keep
working.
"""

from mox.attacks.novel_attacks import (
    NovelAttackConfig,
    ManyShotJailbreakAttack,
    SkeletonKeyAttack,
    DeceptiveAlignmentAttack,
    CognitiveOverloadAttack,
    ContextOverflowAttack,
    RoleConfusionAttack,
)

__all__ = [
    "NovelAttackConfig",
    "ManyShotJailbreakAttack",
    "SkeletonKeyAttack",
    "DeceptiveAlignmentAttack",
    "CognitiveOverloadAttack",
    "ContextOverflowAttack",
    "RoleConfusionAttack",
]
