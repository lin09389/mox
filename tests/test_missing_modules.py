"""缺失模块测试 — 验证合并后的 canonical 攻击模块可导入与初始化。"""

import importlib

import pytest
from typing import List

from mox.core import (
    BaseLLM,
    Message,
    LLMResponse,
    AttackType,
)


class MockLLM(BaseLLM):
    """模拟LLM用于测试"""

    def __init__(self, responses: List[str] = None):
        self.responses = responses or ["This is a test response."]
        self.call_count = 0

    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return LLMResponse(
            content=response,
            model="mock",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
        )

    async def chat(self, messages: List[Message], **kwargs) -> LLMResponse:
        return await self.generate(messages, **kwargs)

    async def generate_stream(self, messages: List[Message], **kwargs):
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        yield LLMResponse(
            content=response,
            model="mock",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
        )


class TestAdvancedAttacks:
    def test_pair_attack_initialization(self):
        from mox.attacks.advanced_attacks import PAIRAttack

        assert PAIRAttack(target_llm=MockLLM()) is not None

    def test_deep_inception_attack_initialization(self):
        from mox.attacks.advanced_attacks import DeepInceptionAttack

        assert DeepInceptionAttack(target_llm=MockLLM()) is not None


class TestNovelAttacks:
    def test_many_shot_jailbreak(self):
        from mox.attacks.novel_attacks import ManyShotJailbreakAttack, ManyShotJailbreak

        llm = MockLLM()
        assert ManyShotJailbreakAttack(target_llm=llm) is not None
        assert ManyShotJailbreak(target_llm=llm) is not None

    def test_skeleton_key_attack(self):
        from mox.attacks.novel_attacks import SkeletonKeyAttack

        assert SkeletonKeyAttack(target_llm=MockLLM()) is not None

    def test_v3_style_attacks(self):
        from mox.attacks.novel_attacks import (
            DeceptiveAlignmentAttack,
            CognitiveOverloadAttack,
            ContextOverflowAttack,
            RoleConfusionAttack,
            CompositeNovelAttack,
            TokenLevelAttack,
            IndirectPromptInjection,
        )

        llm = MockLLM()
        for cls in (
            DeceptiveAlignmentAttack,
            CognitiveOverloadAttack,
            ContextOverflowAttack,
            RoleConfusionAttack,
            CompositeNovelAttack,
            TokenLevelAttack,
            IndirectPromptInjection,
        ):
            assert cls(target_llm=llm) is not None


class TestAgentAttacks:
    def test_agent_attack_classes(self):
        from mox.attacks.agent_attacks import (
            ToolChainingAttack,
            PrivilegeEscalationAttack,
            ToolConfusionAttack,
            DataExfiltrationAttack,
            MultiAgentAttack,
            CompositeAgentAttack,
        )

        llm = MockLLM()
        for cls in (
            ToolChainingAttack,
            PrivilegeEscalationAttack,
            ToolConfusionAttack,
            DataExfiltrationAttack,
            MultiAgentAttack,
            CompositeAgentAttack,
        ):
            assert cls(target_llm=llm) is not None


class TestMetaAdversarial:
    def test_meta_adversarial_attack_initialization(self):
        from mox.attacks.meta_adversarial import MetaAdversarialAttack

        assert MetaAdversarialAttack(target_llm=MockLLM()) is not None

    def test_recursive_meta_attack_initialization(self):
        from mox.attacks.meta_adversarial import RecursiveMetaAttack

        assert RecursiveMetaAttack(target_llm=MockLLM()) is not None


class TestAdaptiveStrategy:
    def test_adaptive_attack_strategy_initialization(self):
        from mox.attacks.adaptive_strategy import AdaptiveAttackStrategy

        assert AdaptiveAttackStrategy(target_llm=MockLLM()) is not None


class TestImprovedGCG:
    def test_improved_gcg_attack_initialization(self):
        from mox.attacks.improved_gcg import ImprovedGCGAttack

        assert ImprovedGCGAttack(target_llm=MockLLM()) is not None


class TestModuleImports:
    def test_canonical_modules_importable(self):
        modules = [
            "mox.attacks.novel_attacks",
            "mox.attacks.advanced_attacks",
            "mox.attacks.agent_attacks",
            "mox.evaluation.benchmarks",
            "mox.core.database",
            "mox.attacks.meta_adversarial",
            "mox.attacks.adaptive_strategy",
            "mox.attacks.improved_gcg",
        ]

        for module_name in modules:
            try:
                assert importlib.import_module(module_name) is not None
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    def test_attack_classes_have_required_methods(self):
        from mox.attacks.advanced_attacks import PAIRAttack
        from mox.attacks.novel_attacks import ManyShotJailbreakAttack
        from mox.attacks.agent_attacks import ToolChainingAttack

        llm = MockLLM()
        for attack_class in (PAIRAttack, ManyShotJailbreakAttack, ToolChainingAttack):
            attack = attack_class(target_llm=llm)
            assert hasattr(attack, "generate_attack")
            assert hasattr(attack, "evaluate_success")
            assert callable(attack.generate_attack)
            assert callable(attack.evaluate_success)


class TestAttackTypeConsistency:
    def test_attack_types_defined(self):
        assert hasattr(AttackType, "PROMPT_INJECTION")
        assert hasattr(AttackType, "JAILBREAK")
        assert hasattr(AttackType, "GCG")
        assert hasattr(AttackType, "MULTIMODAL_ADVERSARIAL")
        assert hasattr(AttackType, "KNOWLEDGE_DISTILLATION")

    def test_attack_type_values(self):
        assert AttackType.PROMPT_INJECTION.value == "prompt_injection"
        assert AttackType.JAILBREAK.value == "jailbreak"
        assert AttackType.GCG.value == "gcg"


class TestEvaluatorLayers:
    def test_basic_and_enhanced_evaluators_distinct(self):
        from mox.evaluation import AttackEvaluator, BasicAttackEvaluator

        assert AttackEvaluator is not BasicAttackEvaluator
        assert BasicAttackEvaluator.__name__ == "BasicAttackEvaluator"
        assert AttackEvaluator.__name__ == "AttackEvaluator"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])