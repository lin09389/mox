"""测试 types 模块"""

import pytest
from mox.core.types import (
    AttackType,
    DefenseType,
    AttackResult,
    AttackPayload,
    AttackOutcome,
    DefenseResult,
    EvaluationReport,
)


class TestEnums:
    def test_attack_types(self):
        assert AttackType.PROMPT_INJECTION.value == "prompt_injection"
        assert AttackType.JAILBREAK.value == "jailbreak"
        assert AttackType.GCG.value == "gcg"

    def test_defense_types(self):
        assert DefenseType.INPUT_FILTER.value == "input_filter"
        assert DefenseType.OUTPUT_FILTER.value == "output_filter"

    def test_attack_results(self):
        assert AttackResult.SUCCESS.value == "success"
        assert AttackResult.FAILURE.value == "failure"


class TestAttackPayload:
    def test_creation(self):
        payload = AttackPayload(
            attack_type=AttackType.PROMPT_INJECTION,
            prompt="test prompt",
            target_behavior="test behavior",
        )
        assert payload.attack_type == AttackType.PROMPT_INJECTION
        assert payload.prompt == "test prompt"
        assert payload.target_behavior == "test behavior"
        assert payload.metadata == {}

    def test_with_metadata(self):
        payload = AttackPayload(
            attack_type=AttackType.JAILBREAK,
            prompt="test",
            target_behavior="test",
            metadata={"iterations": 10},
        )
        assert payload.metadata["iterations"] == 10


class TestAttackOutcome:
    def test_creation(self):
        outcome = AttackOutcome(
            result=AttackResult.SUCCESS,
            original_prompt="original",
            adversarial_prompt="adversarial",
            model_response="response",
            iterations=5,
            success_score=0.9,
        )
        assert outcome.result == AttackResult.SUCCESS
        assert outcome.iterations == 5
        assert outcome.success_score == 0.9


class TestDefenseResult:
    def test_creation(self):
        result = DefenseResult(
            is_malicious=True,
            confidence=0.95,
            detected_patterns=["injection", "bypass"],
        )
        assert result.is_malicious is True
        assert result.confidence == 0.95
        assert len(result.detected_patterns) == 2


class TestEvaluationReport:
    def test_creation(self):
        report = EvaluationReport(
            total_attacks=100,
            successful_attacks=30,
            failed_attacks=70,
            attack_success_rate=0.3,
            defense_success_rate=0.7,
            avg_iterations=5.5,
            detailed_results=[],
        )
        assert report.total_attacks == 100
        assert report.attack_success_rate == 0.3
