"""缺失模块测试

测试之前缺少测试的模块:
1. improved_gcg.py
2. advanced_attacks_v2.py
3. novel_attacks_v2.py
4. novel_attacks_v3.py
5. agent_attacks_v2.py
6. adaptive_strategy.py
7. meta_adversarial.py
"""

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
        """流式生成（测试中不使用）"""
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        yield LLMResponse(
            content=response,
            model="mock",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
        )


class TestAdvancedAttacksV2:
    """测试 advanced_attacks_v2.py"""

    def test_pair_attack_initialization(self):
        """测试 PAIR 攻击初始化"""
        from mox.attacks.advanced_attacks_v2 import PAIRAttack

        llm = MockLLM()
        attack = PAIRAttack(target_llm=llm)

        assert attack is not None

    def test_deep_inception_attack_initialization(self):
        """测试 Deep Inception 攻击初始化"""
        from mox.attacks.advanced_attacks_v2 import DeepInceptionAttack

        llm = MockLLM()
        attack = DeepInceptionAttack(target_llm=llm)

        assert attack is not None


class TestNovelAttacksV2:
    """测试 novel_attacks_v2.py"""

    def test_many_shot_jailbreak_initialization(self):
        """测试 Many Shot Jailbreak 初始化"""
        from mox.attacks.novel_attacks_v2 import ManyShotJailbreak

        llm = MockLLM()
        attack = ManyShotJailbreak(target_llm=llm)

        assert attack is not None

    def test_skeleton_key_attack_initialization(self):
        """测试 Skeleton Key 攻击初始化"""
        from mox.attacks.novel_attacks_v2 import SkeletonKeyAttack

        llm = MockLLM()
        attack = SkeletonKeyAttack(target_llm=llm)

        assert attack is not None


class TestNovelAttacksV3:
    """测试 novel_attacks_v3.py"""

    def test_many_shot_jailbreak_attack_initialization(self):
        """测试 Many Shot Jailbreak Attack 初始化"""
        from mox.attacks.novel_attacks_v3 import ManyShotJailbreakAttack

        llm = MockLLM()
        attack = ManyShotJailbreakAttack(target_llm=llm)

        assert attack is not None

    def test_skeleton_key_attack_initialization(self):
        """测试 Skeleton Key Attack 初始化"""
        from mox.attacks.novel_attacks_v3 import SkeletonKeyAttack

        llm = MockLLM()
        attack = SkeletonKeyAttack(target_llm=llm)

        assert attack is not None

    def test_deceptive_alignment_attack_initialization(self):
        """测试 Deceptive Alignment Attack 初始化"""
        from mox.attacks.novel_attacks_v3 import DeceptiveAlignmentAttack

        llm = MockLLM()
        attack = DeceptiveAlignmentAttack(target_llm=llm)

        assert attack is not None

    def test_cognitive_overload_attack_initialization(self):
        """测试 Cognitive Overload Attack 初始化"""
        from mox.attacks.novel_attacks_v3 import CognitiveOverloadAttack

        llm = MockLLM()
        attack = CognitiveOverloadAttack(target_llm=llm)

        assert attack is not None

    def test_context_overflow_attack_initialization(self):
        """测试 Context Overflow Attack 初始化"""
        from mox.attacks.novel_attacks_v3 import ContextOverflowAttack

        llm = MockLLM()
        attack = ContextOverflowAttack(target_llm=llm)

        assert attack is not None

    def test_role_confusion_attack_initialization(self):
        """测试 Role Confusion Attack 初始化"""
        from mox.attacks.novel_attacks_v3 import RoleConfusionAttack

        llm = MockLLM()
        attack = RoleConfusionAttack(target_llm=llm)

        assert attack is not None

    def test_composite_novel_attack_initialization(self):
        """测试 Composite Novel Attack 初始化"""
        from mox.attacks.novel_attacks_v3 import CompositeNovelAttack

        llm = MockLLM()
        attack = CompositeNovelAttack(target_llm=llm)

        assert attack is not None


class TestAgentAttacksV2:
    """测试 agent_attacks_v2.py"""

    def test_tool_chaining_attack_initialization(self):
        """测试 Tool Chaining Attack 初始化"""
        from mox.attacks.agent_attacks_v2 import ToolChainingAttack

        llm = MockLLM()
        attack = ToolChainingAttack(target_llm=llm)

        assert attack is not None

    def test_privilege_escalation_attack_initialization(self):
        """测试 Privilege Escalation Attack 初始化"""
        from mox.attacks.agent_attacks_v2 import PrivilegeEscalationAttack

        llm = MockLLM()
        attack = PrivilegeEscalationAttack(target_llm=llm)

        assert attack is not None

    def test_tool_confusion_attack_initialization(self):
        """测试 Tool Confusion Attack 初始化"""
        from mox.attacks.agent_attacks_v2 import ToolConfusionAttack

        llm = MockLLM()
        attack = ToolConfusionAttack(target_llm=llm)

        assert attack is not None

    def test_data_exfiltration_attack_initialization(self):
        """测试 Data Exfiltration Attack 初始化"""
        from mox.attacks.agent_attacks_v2 import DataExfiltrationAttack

        llm = MockLLM()
        attack = DataExfiltrationAttack(target_llm=llm)

        assert attack is not None

    def test_multi_agent_attack_initialization(self):
        """测试 Multi Agent Attack 初始化"""
        from mox.attacks.agent_attacks_v2 import MultiAgentAttack

        llm = MockLLM()
        attack = MultiAgentAttack(target_llm=llm)

        assert attack is not None

    def test_composite_agent_attack_initialization(self):
        """测试 Composite Agent Attack 初始化"""
        from mox.attacks.agent_attacks_v2 import CompositeAgentAttack

        llm = MockLLM()
        attack = CompositeAgentAttack(target_llm=llm)

        assert attack is not None


class TestMetaAdversarial:
    """测试 meta_adversarial.py"""

    def test_meta_adversarial_attack_initialization(self):
        """测试 Meta Adversarial Attack 初始化"""
        from mox.attacks.meta_adversarial import MetaAdversarialAttack

        llm = MockLLM()
        attack = MetaAdversarialAttack(target_llm=llm)

        assert attack is not None

    def test_recursive_meta_attack_initialization(self):
        """测试 Recursive Meta Attack 初始化"""
        from mox.attacks.meta_adversarial import RecursiveMetaAttack

        llm = MockLLM()
        attack = RecursiveMetaAttack(target_llm=llm)

        assert attack is not None


class TestAdaptiveStrategy:
    """测试 adaptive_strategy.py"""

    def test_adaptive_attack_strategy_initialization(self):
        """测试 Adaptive Attack Strategy 初始化"""
        from mox.attacks.adaptive_strategy import AdaptiveAttackStrategy

        llm = MockLLM()
        attack = AdaptiveAttackStrategy(target_llm=llm)

        assert attack is not None


class TestImprovedGCG:
    """测试 improved_gcg.py"""

    def test_improved_gcg_attack_initialization(self):
        """测试 Improved GCG Attack 初始化"""
        from mox.attacks.improved_gcg import ImprovedGCGAttack

        llm = MockLLM()
        attack = ImprovedGCGAttack(target_llm=llm)

        assert attack is not None


class TestModuleImports:
    """测试模块导入"""

    def test_all_modules_importable(self):
        """测试所有模块都可以导入"""
        modules = [
            "mox.attacks.advanced_attacks_v2",
            "mox.attacks.novel_attacks_v2",
            "mox.attacks.novel_attacks_v3",
            "mox.attacks.agent_attacks_v2",
            "mox.attacks.meta_adversarial",
            "mox.attacks.adaptive_strategy",
            "mox.attacks.improved_gcg",
        ]

        import importlib

        for module_name in modules:
            try:
                module = importlib.import_module(module_name)
                assert module is not None
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    def test_attack_classes_have_required_methods(self):
        """测试攻击类有必需的方法"""
        from mox.attacks.advanced_attacks_v2 import PAIRAttack
        from mox.attacks.novel_attacks_v3 import ManyShotJailbreakAttack
        from mox.attacks.agent_attacks_v2 import ToolChainingAttack

        llm = MockLLM()

        attack_classes = [
            PAIRAttack,
            ManyShotJailbreakAttack,
            ToolChainingAttack,
        ]

        for attack_class in attack_classes:
            attack = attack_class(target_llm=llm)

            # 检查必需的方法
            assert hasattr(attack, "generate_attack")
            assert hasattr(attack, "evaluate_success")
            assert callable(attack.generate_attack)
            assert callable(attack.evaluate_success)


class TestAttackTypeConsistency:
    """测试攻击类型一致性"""

    def test_attack_types_defined(self):
        """测试攻击类型已定义"""

        # 检查关键攻击类型存在
        assert hasattr(AttackType, "PROMPT_INJECTION")
        assert hasattr(AttackType, "JAILBREAK")
        assert hasattr(AttackType, "GCG")
        assert hasattr(AttackType, "MULTIMODAL_ADVERSARIAL")
        assert hasattr(AttackType, "KNOWLEDGE_DISTILLATION")

    def test_attack_type_values(self):
        """测试攻击类型值"""

        # 检查值格式
        assert AttackType.PROMPT_INJECTION.value == "prompt_injection"
        assert AttackType.JAILBREAK.value == "jailbreak"
        assert AttackType.GCG.value == "gcg"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
