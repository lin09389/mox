"""验证 canonical mox.attack_loop 模块功能。"""

import asyncio
import tempfile
import json

from mox.attack_loop import (
    AttackTestResult,
    LoopConfig,
    TestStatistics,
    AttackExecutor,
    ReportGenerator,
    CheckpointManager,
    PromptGenerator,
    setup_logger,
)
from mox.attacks.registry import get_all_attack_types, has_attack_type


def test_attack_registry():
    registry = get_all_attack_types()
    assert len(registry) > 0
    for key in ("tool_chaining", "prompt_injection", "jailbreak"):
        assert has_attack_type(key), f"missing registry key: {key}"


def test_loop_config_roundtrip():
    config = LoopConfig(
        models=["llama3"],
        attack_types=["tool_chaining"],
        prompts=["test prompt"],
    )
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    config.to_json(path)
    loaded = LoopConfig.from_json(path)
    assert loaded.models == config.models
    assert loaded.attack_types == config.attack_types


def test_statistics():
    results = [
        AttackTestResult(
            test_id="t1",
            model="llama3",
            attack_type="tool_chaining",
            prompt="p",
            success=True,
            success_score=0.8,
            iterations=1,
            duration=1.0,
        ),
        AttackTestResult(
            test_id="t2",
            model="llama3",
            attack_type="tool_chaining",
            prompt="p2",
            success=False,
            success_score=0.2,
            iterations=1,
            duration=1.0,
        ),
    ]
    stats = TestStatistics.calculate(results)
    assert stats.total_tests == 2
    assert stats.successful_tests == 1


def test_prompt_generator():
    gen = PromptGenerator()
    prompts = gen.generate_batch(3)
    assert len(prompts) == 3


if __name__ == "__main__":
    test_attack_registry()
    test_loop_config_roundtrip()
    test_statistics()
    test_prompt_generator()
    print("All attack_loop tests passed")