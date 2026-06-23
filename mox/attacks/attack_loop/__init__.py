"""Deprecated shim — use ``mox.attack_loop`` instead."""

import warnings

warnings.warn(
    "mox.attacks.attack_loop is deprecated; use mox.attack_loop instead.",
    DeprecationWarning,
    stacklevel=2,
)

from mox.attack_loop import (
    LoopConfig as AttackLoopConfig,
    AttackTestResult,
    TestStatistics,
    AttackExecutor,
    CheckpointManager,
    PromptGenerator,
    ReportGenerator,
    AttackLoopRunner,
    setup_logger,
    create_config_from_args,
    print_statistics,
)


async def run_attack_loop_async(config: AttackLoopConfig):
    runner = AttackLoopRunner(config)
    result = await runner.run()
    return result.get("results", [])


def run_attack_loop(config: AttackLoopConfig):
    import asyncio

    return asyncio.run(run_attack_loop_async(config))


__all__ = [
    "AttackLoopConfig",
    "AttackTestResult",
    "TestStatistics",
    "AttackExecutor",
    "CheckpointManager",
    "PromptGenerator",
    "ReportGenerator",
    "AttackLoopRunner",
    "run_attack_loop",
    "run_attack_loop_async",
    "setup_logger",
    "create_config_from_args",
    "print_statistics",
]