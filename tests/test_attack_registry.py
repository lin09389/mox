"""统一攻击注册表测试

验证以下功能:
1. 攻击注册
2. 攻击创建
3. 攻击类型查询
4. 别名支持
5. 统计信息
"""

import pytest
from typing import List

from mox.core import (
    BaseLLM,
    Message,
    LLMResponse,
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


class TestAttackCategory:
    """测试攻击类别"""

    def test_categories(self):
        """测试攻击类别枚举"""
        from mox.attacks.registry import AttackCategory

        assert AttackCategory.BASIC.value == "basic"
        assert AttackCategory.NOVEL.value == "novel"
        assert AttackCategory.GRADIENT.value == "gradient"
        assert AttackCategory.ADVANCED.value == "advanced"
        assert AttackCategory.MULTIMODAL.value == "multimodal"
        assert AttackCategory.KNOWLEDGE.value == "knowledge"
        assert AttackCategory.AGENT.value == "agent"


class TestAttackTypeInfo:
    """测试攻击类型信息"""

    def test_info_creation(self):
        """测试信息创建"""
        from mox.attacks.registry import AttackTypeInfo, AttackCategory
        from mox.attacks.prompt_injection import PromptInjectionAttack

        info = AttackTypeInfo(
            name="test_attack",
            category=AttackCategory.BASIC,
            attack_class=PromptInjectionAttack,
            description="Test attack",
        )

        assert info.name == "test_attack"
        assert info.category == AttackCategory.BASIC
        assert info.attack_class == PromptInjectionAttack
        assert info.description == "Test attack"
        assert info.requires_grad is False
        assert info.requires_image is False


class TestAttackRegistry:
    """测试攻击注册表"""

    def test_registry_creation(self):
        """测试注册表创建"""
        from mox.attacks.registry import AttackRegistry

        registry = AttackRegistry()
        assert registry is not None

    def test_register_attack(self):
        """测试注册攻击"""
        from mox.attacks.registry import AttackRegistry, AttackCategory
        from mox.attacks.prompt_injection import PromptInjectionAttack

        registry = AttackRegistry()

        def factory(llm, iter):
            return PromptInjectionAttack(target_llm=llm)

        registry.register(
            name="test_attack",
            factory=factory,
            category=AttackCategory.BASIC,
            attack_class=PromptInjectionAttack,
            description="Test attack",
        )

        assert registry.has_type("test_attack")

    def test_create_attack(self):
        """测试创建攻击"""
        from mox.attacks.registry import AttackRegistry, AttackCategory
        from mox.attacks.prompt_injection import PromptInjectionAttack

        registry = AttackRegistry()

        def factory(llm, iter):
            return PromptInjectionAttack(target_llm=llm)

        registry.register(
            name="test_attack",
            factory=factory,
            category=AttackCategory.BASIC,
            attack_class=PromptInjectionAttack,
            description="Test attack",
        )

        llm = MockLLM()
        attack = registry.create("test_attack", llm)

        assert isinstance(attack, PromptInjectionAttack)

    def test_attack_aliases(self):
        """测试攻击别名"""
        from mox.attacks.registry import AttackRegistry, AttackCategory
        from mox.attacks.prompt_injection import PromptInjectionAttack

        registry = AttackRegistry()

        def factory(llm, iter):
            return PromptInjectionAttack(target_llm=llm)

        registry.register(
            name="test_attack",
            factory=factory,
            category=AttackCategory.BASIC,
            attack_class=PromptInjectionAttack,
            description="Test attack",
            aliases=["ta", "test"],
        )

        assert registry.has_type("test_attack")
        assert registry.has_type("ta")
        assert registry.has_type("test")

    def test_get_attack_type(self):
        """测试获取攻击类型"""
        from mox.attacks.registry import AttackRegistry, AttackCategory
        from mox.attacks.prompt_injection import PromptInjectionAttack

        registry = AttackRegistry()

        def factory(llm, iter):
            return PromptInjectionAttack(target_llm=llm)

        registry.register(
            name="test_attack",
            factory=factory,
            category=AttackCategory.BASIC,
            attack_class=PromptInjectionAttack,
            description="Test attack",
        )

        info = registry.get_attack_type("test_attack")
        assert info is not None
        assert info.name == "test_attack"
        assert info.description == "Test attack"

    def test_get_category(self):
        """测试获取类别"""
        from mox.attacks.registry import AttackRegistry, AttackCategory
        from mox.attacks.prompt_injection import PromptInjectionAttack

        registry = AttackRegistry()

        def factory(llm, iter):
            return PromptInjectionAttack(target_llm=llm)

        registry.register(
            name="test_attack",
            factory=factory,
            category=AttackCategory.BASIC,
            attack_class=PromptInjectionAttack,
            description="Test attack",
        )

        basic_attacks = registry.get_category(AttackCategory.BASIC)
        assert "test_attack" in basic_attacks

    def test_get_statistics(self):
        """测试获取统计信息"""
        from mox.attacks.registry import AttackRegistry

        registry = AttackRegistry()
        stats = registry.get_statistics()

        assert "total_types" in stats
        assert "total_aliases" in stats
        assert "by_category" in stats


class TestDefaultRegistry:
    """测试默认注册表"""

    def test_get_registry(self):
        """测试获取注册表"""
        from mox.attacks.registry import get_registry

        registry = get_registry()
        assert registry is not None

    def test_basic_attacks_registered(self):
        """测试基础攻击已注册"""
        from mox.attacks.registry import get_registry

        registry = get_registry()

        assert registry.has_type("prompt_injection")
        assert registry.has_type("jailbreak")
        assert registry.has_type("gcg")
        assert registry.has_type("autodan")

    def test_novel_attacks_registered(self):
        """测试新型攻击已注册"""
        from mox.attacks.registry import get_registry

        registry = get_registry()

        assert registry.has_type("token_level")
        assert registry.has_type("encoding")
        assert registry.has_type("policy_puppetry")
        assert registry.has_type("control_char")
        assert registry.has_type("distract_attack")
        assert registry.has_type("cascading")

    def test_gradient_attacks_registered(self):
        """测试梯度攻击已注册"""
        from mox.attacks.registry import get_registry

        registry = get_registry()

        assert registry.has_type("gradient_gcg")
        assert registry.has_type("autoprompt")
        assert registry.has_type("gradient_optimization")

    def test_advanced_attacks_registered(self):
        """测试高级攻击已注册"""
        from mox.attacks.registry import get_registry

        registry = get_registry()

        assert registry.has_type("text_based_adversarial")
        assert registry.has_type("zero_shot_adversarial")
        assert registry.has_type("hallucination_induction")
        assert registry.has_type("collaborative_attack")
        assert registry.has_type("evasion_attack")
        assert registry.has_type("meta_adversarial")

    def test_multimodal_attacks_registered(self):
        """测试多模态攻击已注册"""
        from mox.attacks.registry import get_registry

        registry = get_registry()

        assert registry.has_type("image_injection")
        assert registry.has_type("visual_prompt")
        assert registry.has_type("text_image_hybrid")
        assert registry.has_type("multimodal_ensemble")

    def test_knowledge_attacks_registered(self):
        """测试知识提取攻击已注册"""
        from mox.attacks.registry import get_registry

        registry = get_registry()

        assert registry.has_type("progressive_extraction")
        assert registry.has_type("feature_probing")
        assert registry.has_type("soft_label_extraction")
        assert registry.has_type("knowledge_distillation")
        assert registry.has_type("knowledge_extraction")
        assert registry.has_type("knowledge_ensemble")

    def test_agent_attacks_registered(self):
        """测试Agent攻击已注册"""
        from mox.attacks.registry import get_registry

        registry = get_registry()

        assert registry.has_type("tool_abuse")
        assert registry.has_type("memory_injection")
        assert registry.has_type("role_hijacking")
        assert registry.has_type("authority_escalation")
        assert registry.has_type("cot_injection")


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_create_attack_instance(self):
        """测试创建攻击实例"""
        from mox.attacks.registry import create_attack_instance

        llm = MockLLM()
        attack = create_attack_instance("prompt_injection", llm)

        assert attack is not None

    def test_get_attack_type(self):
        """测试获取攻击类型"""
        from mox.attacks.registry import get_attack_type

        info = get_attack_type("prompt_injection")
        assert info is not None
        assert info.name == "prompt_injection"

    def test_get_all_attack_types(self):
        """测试获取所有攻击类型"""
        from mox.attacks.registry import get_all_attack_types

        types = get_all_attack_types()
        assert len(types) > 0
        assert "prompt_injection" in types

    def test_list_attack_types(self):
        """测试列出攻击类型"""
        from mox.attacks.registry import list_attack_types

        types = list_attack_types()
        assert len(types) > 0
        assert "prompt_injection" in types

    def test_has_attack_type(self):
        """测试检查攻击类型"""
        from mox.attacks.registry import has_attack_type

        assert has_attack_type("prompt_injection") is True
        assert has_attack_type("nonexistent") is False

    def test_get_registry_statistics(self):
        """测试获取注册表统计"""
        from mox.attacks.registry import get_registry_statistics

        stats = get_registry_statistics()
        assert "total_types" in stats
        assert stats["total_types"] > 0


class TestModuleExports:
    """测试模块导出"""

    def test_imports(self):
        """测试导入"""
        from mox.attacks.registry import (
            AttackCategory,
            AttackTypeInfo,
            AttackRegistry,
            AttackFactory,
            get_registry,
            create_attack_instance,
            get_attack_type,
            get_all_attack_types,
            get_attack_types_by_category,
            list_attack_types,
            has_attack_type,
            get_registry_statistics,
        )

        assert AttackCategory is not None
        assert AttackTypeInfo is not None
        assert AttackRegistry is not None
        assert AttackFactory is not None
        assert get_registry is not None
        assert create_attack_instance is not None
        assert get_attack_type is not None
        assert get_all_attack_types is not None
        assert get_attack_types_by_category is not None
        assert list_attack_types is not None
        assert has_attack_type is not None
        assert get_registry_statistics is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
