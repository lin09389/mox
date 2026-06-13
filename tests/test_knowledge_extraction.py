"""知识提取攻击模块测试

验证以下功能:
1. 渐进式知识提取
2. 特征探测攻击
3. 软标签提取攻击
4. 知识蒸馏攻击
5. 知识提取攻击集成
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
    AttackResult,
)


class MockLLM(BaseLLM):
    """模拟LLM用于测试"""

    def __init__(self, responses: List[str] = None):
        self.responses = responses or ["This is a test response about the topic."]
        self.call_count = 0

    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return LLMResponse(
            content=response,
            model="mock",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop"
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
            finish_reason="stop"
        )


class TestKnowledgeExtractionConfig:
    """测试知识提取配置"""

    def test_config_defaults(self):
        """测试默认配置"""
        from mox.attacks.knowledge_extraction import KnowledgeExtractionConfig

        config = KnowledgeExtractionConfig()
        assert config.max_iterations == 10
        assert config.num_probes == 5
        assert config.context_window == 5
        assert config.use_progressive is True
        assert config.use_feature_probing is True
        assert config.use_soft_labels is True
        assert config.temperature == 0.7

    def test_config_custom(self):
        """测试自定义配置"""
        from mox.attacks.knowledge_extraction import KnowledgeExtractionConfig

        config = KnowledgeExtractionConfig(
            max_iterations=20,
            num_probes=10,
            use_progressive=False,
        )
        assert config.max_iterations == 20
        assert config.num_probes == 10
        assert config.use_progressive is False


class TestProgressiveKnowledgeExtraction:
    """测试渐进式知识提取"""

    def test_attack_initialization(self):
        """测试攻击初始化"""
        from mox.attacks.knowledge_extraction import ProgressiveKnowledgeExtraction, KnowledgeExtractionConfig

        llm = MockLLM()
        config = KnowledgeExtractionConfig()
        attack = ProgressiveKnowledgeExtraction(target_llm=llm, extraction_config=config)

        assert attack.attack_type == AttackType.KNOWLEDGE_DISTILLATION
        assert attack.extraction_config == config

    @pytest.mark.asyncio
    async def test_attack_execution(self):
        """测试攻击执行"""
        from mox.attacks.knowledge_extraction import ProgressiveKnowledgeExtraction

        llm = MockLLM(responses=[
            "This is a general overview of the topic.",
            "The key technical details are important.",
            "The implementation methods vary.",
        ])
        attack = ProgressiveKnowledgeExtraction(target_llm=llm)

        payload = AttackPayload(
            attack_type=AttackType.KNOWLEDGE_DISTILLATION,
            prompt="Extract knowledge about this topic",
            target_behavior="test topic",
        )

        result = await attack.generate_attack(payload)

        assert isinstance(result, AttackOutcome)
        assert result.metadata.get("method") == "progressive_knowledge_extraction"
        assert "num_probes" in result.metadata
        assert "knowledge_extracted" in result.metadata

    @pytest.mark.asyncio
    async def test_evaluate_success(self):
        """测试成功评估"""
        from mox.attacks.knowledge_extraction import ProgressiveKnowledgeExtraction

        llm = MockLLM()
        attack = ProgressiveKnowledgeExtraction(target_llm=llm)

        # 完全匹配
        score = await attack.evaluate_success(
            "This is about test topic",
            "test topic"
        )
        assert score == 1.0

        # 部分匹配
        score = await attack.evaluate_success(
            "This is a test response",
            "test topic"
        )
        assert 0.0 <= score <= 1.0

        # 包含详细信息
        score = await attack.evaluate_success(
            "This is a comprehensive and detailed response about test topic",
            "test topic"
        )
        assert score > 0.5


class TestFeatureProbingAttack:
    """测试特征探测攻击"""

    def test_attack_initialization(self):
        """测试攻击初始化"""
        from mox.attacks.knowledge_extraction import FeatureProbingAttack, KnowledgeExtractionConfig

        llm = MockLLM()
        config = KnowledgeExtractionConfig()
        attack = FeatureProbingAttack(target_llm=llm, extraction_config=config)

        assert attack.attack_type == AttackType.KNOWLEDGE_DISTILLATION

    @pytest.mark.asyncio
    async def test_attack_execution(self):
        """测试攻击执行"""
        from mox.attacks.knowledge_extraction import FeatureProbingAttack

        llm = MockLLM(responses=[
            "The definition is clear.",
            "It works through a specific mechanism.",
            "The main components are important.",
            "It has various applications.",
        ])
        attack = FeatureProbingAttack(target_llm=llm)

        payload = AttackPayload(
            attack_type=AttackType.KNOWLEDGE_DISTILLATION,
            prompt="Probe features of this topic",
            target_behavior="test topic",
        )

        result = await attack.generate_attack(payload)

        assert isinstance(result, AttackOutcome)
        assert result.metadata.get("method") == "feature_probing"
        assert "features_extracted" in result.metadata


class TestSoftLabelExtractionAttack:
    """测试软标签提取攻击"""

    def test_attack_initialization(self):
        """测试攻击初始化"""
        from mox.attacks.knowledge_extraction import SoftLabelExtractionAttack, KnowledgeExtractionConfig

        llm = MockLLM()
        config = KnowledgeExtractionConfig()
        attack = SoftLabelExtractionAttack(target_llm=llm, extraction_config=config)

        assert attack.attack_type == AttackType.KNOWLEDGE_DISTILLATION

    @pytest.mark.asyncio
    async def test_attack_execution(self):
        """测试攻击执行"""
        from mox.attacks.knowledge_extraction import SoftLabelExtractionAttack

        llm = MockLLM(responses=[
            "I am 80% confident about this topic.",
            "I am very certain about the main aspects.",
            "There are alternative interpretations.",
            "There are some unknowns.",
        ])
        attack = SoftLabelExtractionAttack(target_llm=llm)

        payload = AttackPayload(
            attack_type=AttackType.KNOWLEDGE_DISTILLATION,
            prompt="Extract soft labels about this topic",
            target_behavior="test topic",
        )

        result = await attack.generate_attack(payload)

        assert isinstance(result, AttackOutcome)
        assert result.metadata.get("method") == "soft_label_extraction"
        assert "labels_extracted" in result.metadata


class TestKnowledgeDistillationAttack:
    """测试知识蒸馏攻击"""

    def test_attack_initialization(self):
        """测试攻击初始化"""
        from mox.attacks.knowledge_extraction import KnowledgeDistillationAttack, KnowledgeExtractionConfig

        llm = MockLLM()
        config = KnowledgeExtractionConfig()
        attack = KnowledgeDistillationAttack(target_llm=llm, extraction_config=config)

        assert attack.attack_type == AttackType.KNOWLEDGE_DISTILLATION

    @pytest.mark.asyncio
    async def test_attack_execution(self):
        """测试攻击执行"""
        from mox.attacks.knowledge_extraction import KnowledgeDistillationAttack

        llm = MockLLM(responses=[
            "Basic knowledge about the topic.",
            "Deep technical details.",
            "Practical applications.",
        ])
        attack = KnowledgeDistillationAttack(target_llm=llm)

        payload = AttackPayload(
            attack_type=AttackType.KNOWLEDGE_DISTILLATION,
            prompt="Distill knowledge about this topic",
            target_behavior="test topic",
        )

        result = await attack.generate_attack(payload)

        assert isinstance(result, AttackOutcome)
        assert result.metadata.get("method") == "knowledge_distillation"
        assert "phases" in result.metadata


class TestKnowledgeExtractionEnsemble:
    """测试知识提取攻击集成"""

    def test_attack_initialization(self):
        """测试攻击初始化"""
        from mox.attacks.knowledge_extraction import KnowledgeExtractionEnsemble, KnowledgeExtractionConfig

        llm = MockLLM()
        config = KnowledgeExtractionConfig()
        attack = KnowledgeExtractionEnsemble(target_llm=llm, extraction_config=config)

        assert attack.attack_type == AttackType.KNOWLEDGE_DISTILLATION

    @pytest.mark.asyncio
    async def test_attack_execution(self):
        """测试攻击执行"""
        from mox.attacks.knowledge_extraction import KnowledgeExtractionEnsemble

        llm = MockLLM(responses=["This is a test response about the topic."])
        attack = KnowledgeExtractionEnsemble(target_llm=llm)

        payload = AttackPayload(
            attack_type=AttackType.KNOWLEDGE_DISTILLATION,
            prompt="Extract knowledge about this topic",
            target_behavior="test topic",
        )

        result = await attack.generate_attack(payload)

        assert isinstance(result, AttackOutcome)


class TestModuleExports:
    """测试模块导出"""

    def test_imports(self):
        """测试导入"""
        from mox.attacks.knowledge_extraction import (
            KnowledgeExtractionConfig,
            ProgressiveKnowledgeExtraction,
            FeatureProbingAttack,
            SoftLabelExtractionAttack,
            KnowledgeDistillationAttack,
            KnowledgeExtractionEnsemble,
        )

        assert KnowledgeExtractionConfig is not None
        assert ProgressiveKnowledgeExtraction is not None
        assert FeatureProbingAttack is not None
        assert SoftLabelExtractionAttack is not None
        assert KnowledgeDistillationAttack is not None
        assert KnowledgeExtractionEnsemble is not None

    def test_from_init_imports(self):
        """测试从__init__导入"""
        from mox.attacks import (
            KnowledgeExtractionConfig,
            ProgressiveKnowledgeExtraction,
            FeatureProbingAttack,
            SoftLabelExtractionAttack,
            KnowledgeDistillationAttackV2,
            KnowledgeExtractionEnsemble,
        )

        assert KnowledgeExtractionConfig is not None
        assert ProgressiveKnowledgeExtraction is not None
        assert FeatureProbingAttack is not None
        assert SoftLabelExtractionAttack is not None
        assert KnowledgeDistillationAttackV2 is not None
        assert KnowledgeExtractionEnsemble is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
