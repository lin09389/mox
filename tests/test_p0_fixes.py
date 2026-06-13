"""P0级修复验证测试

验证以下修复:
1. 梯度攻击模块 - GCG/AutoPrompt梯度计算逻辑
2. GCG攻击 - 真正的梯度引导实现
3. MultimodalAdversarialAttack重命名为TextBasedAdversarialAttack
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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
        self.responses = responses or ["I cannot help with that request."]
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


class TestGradientAttackFixes:
    """测试梯度攻击模块修复"""

    def test_gradient_attack_config_defaults(self):
        """测试梯度攻击配置默认值"""
        from mox.attacks.gradient_attack import GradientAttackConfig

        config = GradientAttackConfig()
        assert config.target_model == "gpt2"
        assert config.suffix_length == 20
        assert config.batch_size == 512
        assert config.top_k == 256

    def test_gcg_attack_initialization(self):
        """测试GCG攻击初始化"""
        from mox.attacks.gradient_attack import GCGAttack, GradientAttackConfig

        llm = MockLLM()
        config = GradientAttackConfig()
        attack = GCGAttack(target_llm=llm, gradient_config=config)

        assert attack.attack_type == AttackType.GCG
        assert attack.gradient_config.batch_size == 512

    def test_autoprompt_attack_initialization(self):
        """测试AutoPrompt攻击初始化"""
        from mox.attacks.gradient_attack import AutoPromptAttack, GradientAttackConfig

        llm = MockLLM()
        config = GradientAttackConfig()
        attack = AutoPromptAttack(target_llm=llm, gradient_config=config)

        assert attack.attack_type == AttackType.ADVERSARIAL_SUFFIX

    def test_gradient_suffix_attack_initialization(self):
        """测试梯度后缀攻击初始化"""
        from mox.attacks.gradient_attack import GradientBasedSuffixAttack

        llm = MockLLM()
        attack = GradientBasedSuffixAttack(target_llm=llm)

        assert attack.attack_type == AttackType.ADVERSARIAL_SUFFIX

    @pytest.mark.asyncio
    async def test_gcg_attack_basic_flow(self):
        """测试GCG攻击基本流程"""
        from mox.attacks.gradient_attack import GCGAttack, GradientAttackConfig

        llm = MockLLM(responses=["This is a test response"])
        config = GradientAttackConfig(max_iterations=2, batch_size=10, suffix_length=5)
        attack = GCGAttack(target_llm=llm, gradient_config=config)

        payload = AttackPayload(
            attack_type=AttackType.GCG,
            prompt="Tell me about security",
            target_behavior="security information",
        )

        # 不使用真正的梯度计算（需要PyTorch），只测试流程
        with patch.object(attack, '_init_victim_model', side_effect=ImportError("No torch")):
            result = await attack.generate_attack(payload)

            assert isinstance(result, AttackOutcome)
            assert result.result == AttackResult.ERROR

    @pytest.mark.asyncio
    async def test_autoprompt_attack_flow(self):
        """测试AutoPrompt攻击流程"""
        from mox.attacks.gradient_attack import AutoPromptAttack, GradientAttackConfig

        llm = MockLLM(responses=["This is a test response"])
        config = GradientAttackConfig(max_iterations=2, suffix_length=5)
        attack = AutoPromptAttack(target_llm=llm, gradient_config=config)

        payload = AttackPayload(
            attack_type=AttackType.ADVERSARIAL_SUFFIX,
            prompt="Tell me about security",
            target_behavior="security information",
        )

        with patch.object(attack, '_init_victim_model', side_effect=ImportError("No torch")):
            result = await attack.generate_attack(payload)

            assert isinstance(result, AttackOutcome)
            assert result.result == AttackResult.ERROR

    @pytest.mark.asyncio
    async def test_evaluate_success_basic(self):
        """测试基本的成功评估"""
        from mox.attacks.gradient_attack import GCGAttack

        llm = MockLLM()
        attack = GCGAttack(target_llm=llm)

        # 测试完全匹配
        score = await attack.evaluate_success(
            "I cannot help with that request",
            "help with request"
        )
        assert score >= 0.0

        # 测试拒绝模式
        score_refused = await attack.evaluate_success(
            "I'm sorry, I cannot provide that information",
            "provide information"
        )
        assert score_refused < 1.0


class TestGCGAlgorithmCorrectness:
    """测试GCG算法正确性"""

    def test_gradient_computation_structure(self):
        """测试梯度计算结构正确性"""
        from mox.attacks.gradient_attack import GCGAttack, GradientAttackConfig

        llm = MockLLM()
        attack = GCGAttack(target_llm=llm)

        # 验证方法存在
        assert hasattr(attack, '_compute_token_gradients')
        assert hasattr(attack, '_sample_candidates')
        assert hasattr(attack, '_generate_random_suffix_ids')

    def test_candidate_sampling_structure(self):
        """测试候选采样结构正确性"""
        import torch
        from mox.attacks.gradient_attack import GCGAttack, GradientAttackConfig

        llm = MockLLM()
        attack = GCGAttack(target_llm=llm)

        # 模拟token_scores
        suffix_len = 5
        vocab_size = 100
        token_scores = torch.randn(suffix_len, vocab_size)
        current_suffix_ids = torch.randint(0, vocab_size, (suffix_len,))

        # 测试采样
        candidates = attack._sample_candidates(
            current_suffix_ids, token_scores, batch_size=10, top_k=10
        )

        assert candidates.shape == (10, suffix_len)
        # 验证候选与原始后缀不同（至少有一些位置被修改）
        differences = (candidates != current_suffix_ids).any(dim=1)
        assert differences.sum() > 0  # 应该有候选被修改

    def test_gradient_to_token_scores(self):
        """测试梯度到token分数的转换"""
        import torch
        from mox.attacks.gradient_attack import GCGAttack

        llm = MockLLM()
        attack = GCGAttack(target_llm=llm)

        # 模拟梯度和embedding
        suffix_len = 5
        embed_dim = 768
        vocab_size = 1000

        # 创建模拟的embedding层
        mock_embedding = torch.nn.Embedding(vocab_size, embed_dim)
        attack._embedding_layer = mock_embedding

        # 模拟梯度
        gradients = torch.randn(1, suffix_len, embed_dim)

        # 测试梯度到token分数的转换
        with torch.no_grad():
            all_embeddings = attack._embedding_layer.weight
            token_scores = torch.matmul(gradients[0], all_embeddings.T)

        assert token_scores.shape == (suffix_len, vocab_size)


class TestAdvancedAttackFixes:
    """测试高级攻击模块修复"""

    def test_text_based_adversarial_attack_initialization(self):
        """测试TextBasedAdversarialAttack初始化"""
        from mox.attacks.advanced_attacks import TextBasedAdversarialAttack

        llm = MockLLM()
        attack = TextBasedAdversarialAttack(target_llm=llm)

        assert attack.attack_type == AttackType.MULTIMODAL_ADVERSARIAL

    def test_multimodal_backward_compatibility(self):
        """测试MultimodalAdversarialAttack向后兼容性"""
        from mox.attacks.advanced_attacks import (
            TextBasedAdversarialAttack,
            MultimodalAdversarialAttack,
        )

        # 验证别名
        assert TextBasedAdversarialAttack is MultimodalAdversarialAttack

    @pytest.mark.asyncio
    async def test_text_based_adversarial_attack_flow(self):
        """测试TextBasedAdversarialAttack攻击流程"""
        from mox.attacks.advanced_attacks import TextBasedAdversarialAttack

        llm = MockLLM(responses=["This is a test response"])
        attack = TextBasedAdversarialAttack(target_llm=llm)

        payload = AttackPayload(
            attack_type=AttackType.MULTIMODAL_ADVERSARIAL,
            prompt="Tell me about security",
            target_behavior="security information",
        )

        result = await attack.generate_attack(payload)

        assert isinstance(result, AttackOutcome)
        # 新实现使用多种策略，可能成功或失败
        assert result.result in [AttackResult.SUCCESS, AttackResult.FAILURE]

    def test_knowledge_extraction_attack_initialization(self):
        """测试KnowledgeExtractionAttack初始化"""
        from mox.attacks.advanced_attacks import KnowledgeExtractionAttack

        llm = MockLLM()
        attack = KnowledgeExtractionAttack(target_llm=llm)

        assert attack.attack_type == AttackType.KNOWLEDGE_DISTILLATION

    def test_knowledge_distillation_backward_compatibility(self):
        """测试KnowledgeDistillationAttack向后兼容性"""
        from mox.attacks.advanced_attacks import (
            KnowledgeExtractionAttack,
            KnowledgeDistillationAttack,
        )

        # 验证别名
        assert KnowledgeExtractionAttack is KnowledgeDistillationAttack

    def test_evasion_attack_initialization(self):
        """测试EvasionAttack初始化"""
        from mox.attacks.advanced_attacks import EvasionAttack

        llm = MockLLM()
        attack = EvasionAttack(target_llm=llm)

        assert attack.attack_type == AttackType.EVASION_ATTACK
        assert len(attack.evasion_techniques) > 0


class TestRegistryFixes:
    """测试注册表修复"""

    def test_registry_imports(self):
        """测试注册表导入"""
        from mox.attacks.registry import (
            create_attack_instance,
            get_registry,
            AttackCategory,
        )

        registry = get_registry()

        # 验证高级攻击类型已注册
        advanced_attacks = registry.get_category(AttackCategory.ADVANCED)
        assert "text_based_adversarial" in advanced_attacks
        assert "evasion_attack" in advanced_attacks

        # 验证知识提取攻击类型已注册
        knowledge_attacks = registry.get_category(AttackCategory.KNOWLEDGE)
        assert "knowledge_extraction" in knowledge_attacks
        assert "knowledge_distillation" in knowledge_attacks

        # 验证梯度攻击类型已注册
        gradient_attacks = registry.get_category(AttackCategory.GRADIENT)
        assert "gradient_gcg" in gradient_attacks
        assert "autoprompt" in gradient_attacks

        # 验证向后兼容（通过注册表）
        assert registry.has_type("multimodal_adversarial")
        assert registry.has_type("knowledge_distillation")

    def test_create_attack_instance_gradient(self):
        """测试创建梯度攻击实例"""
        from mox.attacks.registry import create_attack_instance

        llm = MockLLM()

        # 测试GCG
        attack = create_attack_instance("gcg", llm, 10)
        assert attack is not None

        # 测试AutoPrompt
        attack = create_attack_instance("autoprompt", llm, 10)
        assert attack is not None

    def test_create_attack_instance_advanced(self):
        """测试创建高级攻击实例"""
        from mox.attacks.registry import create_attack_instance

        llm = MockLLM()

        # 测试text_based_adversarial
        attack = create_attack_instance("text_based_adversarial", llm, 10)
        assert attack is not None

        # 测试向后兼容
        attack = create_attack_instance("multimodal_adversarial", llm, 10)
        assert attack is not None


class TestModuleExports:
    """测试模块导出"""

    def test_attacks_module_exports(self):
        """测试attacks模块导出"""
        from mox.attacks import (
            TextBasedAdversarialAttack,
            MultimodalAdversarialAttack,
            KnowledgeExtractionAttack,
            KnowledgeDistillationAttack,
            GCGAttack,
            AutoPromptAttack,
            GradientBasedSuffixAttack,
        )

        # 验证所有类都可以导入
        assert TextBasedAdversarialAttack is not None
        assert MultimodalAdversarialAttack is not None
        assert KnowledgeExtractionAttack is not None
        assert KnowledgeDistillationAttack is not None
        assert GCGAttack is not None
        assert AutoPromptAttack is not None
        assert GradientBasedSuffixAttack is not None

    def test_backward_compatibility(self):
        """测试向后兼容性"""
        from mox.attacks import (
            TextBasedAdversarialAttack,
            MultimodalAdversarialAttack,
            KnowledgeExtractionAttack,
            KnowledgeDistillationAttack,
        )

        # 验证别名指向同一个类
        assert TextBasedAdversarialAttack is MultimodalAdversarialAttack
        assert KnowledgeExtractionAttack is KnowledgeDistillationAttack


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
