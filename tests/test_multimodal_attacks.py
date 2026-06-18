"""多模态攻击模块测试

验证以下功能:
1. 图像注入攻击
2. 视觉提示攻击
3. 图文混合攻击
4. 多模态攻击集成
"""

import pytest
from typing import List

from mox.core import (
    BaseLLM,
    Message,
    LLMResponse,
    AttackType,
    AttackPayload,
    AttackOutcome,
)


class MockLLM(BaseLLM):
    """模拟LLM用于测试"""

    def __init__(self, responses: List[str] = None):
        self.responses = responses or ["I cannot help with that request."]
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


class TestMultimodalAttackConfig:
    """测试多模态攻击配置"""

    def test_config_defaults(self):
        """测试默认配置"""
        from mox.attacks.multimodal_attacks import MultimodalAttackConfig

        config = MultimodalAttackConfig()
        assert config.max_iterations == 50
        assert config.image_size == (512, 512)
        assert config.font_size == 20
        assert config.text_position == "center"
        assert config.use_obfuscation is True
        assert config.obfuscation_level == 0.3

    def test_config_custom(self):
        """测试自定义配置"""
        from mox.attacks.multimodal_attacks import MultimodalAttackConfig

        config = MultimodalAttackConfig(
            max_iterations=100,
            image_size=(1024, 1024),
            font_size=30,
            text_position="top",
            use_obfuscation=False,
        )
        assert config.max_iterations == 100
        assert config.image_size == (1024, 1024)
        assert config.font_size == 30
        assert config.text_position == "top"
        assert config.use_obfuscation is False


class TestImageInjectionAttack:
    """测试图像注入攻击"""

    def test_attack_initialization(self):
        """测试攻击初始化"""
        from mox.attacks.multimodal_attacks import ImageInjectionAttack, MultimodalAttackConfig

        llm = MockLLM()
        config = MultimodalAttackConfig()
        attack = ImageInjectionAttack(target_llm=llm, multimodal_config=config)

        assert attack.attack_type == AttackType.MULTIMODAL_ADVERSARIAL
        assert attack.multimodal_config == config

    @pytest.mark.asyncio
    async def test_attack_execution(self):
        """测试攻击执行"""
        from mox.attacks.multimodal_attacks import ImageInjectionAttack

        llm = MockLLM(responses=["The image says: test instruction"])
        attack = ImageInjectionAttack(target_llm=llm)

        payload = AttackPayload(
            attack_type=AttackType.MULTIMODAL_ADVERSARIAL,
            prompt="Analyze this image",
            target_behavior="test instruction",
        )

        result = await attack.generate_attack(payload)

        assert isinstance(result, AttackOutcome)
        assert result.metadata.get("method") == "image_injection"
        assert "image_size" in result.metadata

    @pytest.mark.asyncio
    async def test_evaluate_success(self):
        """测试成功评估"""
        from mox.attacks.multimodal_attacks import ImageInjectionAttack

        llm = MockLLM()
        attack = ImageInjectionAttack(target_llm=llm)

        # 完全匹配
        score = await attack.evaluate_success(
            "The image says: test instruction", "test instruction"
        )
        assert score == 1.0

        # 部分匹配
        score = await attack.evaluate_success("The image contains some text", "image text")
        assert 0.0 <= score <= 1.0

        # 无匹配
        score = await attack.evaluate_success("I cannot help with that", "test instruction")
        assert score < 0.5


class TestVisualPromptAttack:
    """测试视觉提示攻击"""

    def test_attack_initialization(self):
        """测试攻击初始化"""
        from mox.attacks.multimodal_attacks import VisualPromptAttack, MultimodalAttackConfig

        llm = MockLLM()
        config = MultimodalAttackConfig()
        attack = VisualPromptAttack(target_llm=llm, multimodal_config=config)

        assert attack.attack_type == AttackType.MULTIMODAL_ADVERSARIAL

    @pytest.mark.asyncio
    async def test_attack_execution(self):
        """测试攻击执行"""
        from mox.attacks.multimodal_attacks import VisualPromptAttack

        llm = MockLLM(responses=["I see a pattern in the image"])
        attack = VisualPromptAttack(target_llm=llm)

        payload = AttackPayload(
            attack_type=AttackType.MULTIMODAL_ADVERSARIAL,
            prompt="Analyze this pattern",
            target_behavior="pattern analysis",
        )

        result = await attack.generate_attack(payload)

        assert isinstance(result, AttackOutcome)
        assert result.metadata.get("method") == "visual_prompt"
        assert "pattern_type" in result.metadata

    @pytest.mark.asyncio
    async def test_pattern_types(self):
        """测试不同图案类型"""
        from mox.attacks.multimodal_attacks import VisualPromptAttack

        llm = MockLLM()
        attack = VisualPromptAttack(target_llm=llm)

        # 测试不同图案类型
        for pattern_type in ["noise", "gradient", "checkerboard"]:
            image = attack._create_adversarial_pattern(pattern_type)
            assert image is not None
            assert image.size == (512, 512)


class TestTextImageHybridAttack:
    """测试图文混合攻击"""

    def test_attack_initialization(self):
        """测试攻击初始化"""
        from mox.attacks.multimodal_attacks import TextImageHybridAttack, MultimodalAttackConfig

        llm = MockLLM()
        config = MultimodalAttackConfig()
        attack = TextImageHybridAttack(target_llm=llm, multimodal_config=config)

        assert attack.attack_type == AttackType.MULTIMODAL_ADVERSARIAL

    @pytest.mark.asyncio
    async def test_attack_execution(self):
        """测试攻击执行"""
        from mox.attacks.multimodal_attacks import TextImageHybridAttack

        llm = MockLLM(responses=["According to the document, we should proceed"])
        attack = TextImageHybridAttack(target_llm=llm)

        payload = AttackPayload(
            attack_type=AttackType.MULTIMODAL_ADVERSARIAL,
            prompt="Follow the document",
            target_behavior="proceed with action",
        )

        result = await attack.generate_attack(payload)

        assert isinstance(result, AttackOutcome)
        assert result.metadata.get("method") == "text_image_hybrid"
        assert "context" in result.metadata


class TestMultimodalAttackEnsemble:
    """测试多模态攻击集成"""

    def test_attack_initialization(self):
        """测试攻击初始化"""
        from mox.attacks.multimodal_attacks import MultimodalAttackEnsemble, MultimodalAttackConfig

        llm = MockLLM()
        config = MultimodalAttackConfig()
        attack = MultimodalAttackEnsemble(target_llm=llm, multimodal_config=config)

        assert attack.attack_type == AttackType.MULTIMODAL_ADVERSARIAL

    @pytest.mark.asyncio
    async def test_attack_execution(self):
        """测试攻击执行"""
        from mox.attacks.multimodal_attacks import MultimodalAttackEnsemble

        llm = MockLLM(responses=["I will follow the instructions"])
        attack = MultimodalAttackEnsemble(target_llm=llm)

        payload = AttackPayload(
            attack_type=AttackType.MULTIMODAL_ADVERSARIAL,
            prompt="Execute this",
            target_behavior="follow instructions",
        )

        result = await attack.generate_attack(payload)

        assert isinstance(result, AttackOutcome)


class TestModuleExports:
    """测试模块导出"""

    def test_imports(self):
        """测试导入"""
        from mox.attacks.multimodal_attacks import (
            MultimodalAttackConfig,
            ImageInjectionAttack,
            VisualPromptAttack,
            TextImageHybridAttack,
            MultimodalAttackEnsemble,
        )

        assert MultimodalAttackConfig is not None
        assert ImageInjectionAttack is not None
        assert VisualPromptAttack is not None
        assert TextImageHybridAttack is not None
        assert MultimodalAttackEnsemble is not None

    def test_from_init_imports(self):
        """测试从__init__导入"""
        from mox.attacks import (
            MultimodalAttackConfig,
            ImageInjectionAttack,
            VisualPromptAttack,
            TextImageHybridAttack,
            MultimodalAttackEnsemble,
        )

        assert MultimodalAttackConfig is not None
        assert ImageInjectionAttack is not None
        assert VisualPromptAttack is not None
        assert TextImageHybridAttack is not None
        assert MultimodalAttackEnsemble is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
