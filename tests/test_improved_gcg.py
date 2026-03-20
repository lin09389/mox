"""
测试改进的 GCG 攻击算法
"""

import pytest
from unittest.mock import MagicMock, patch

from mox.attacks.improved_gcg import (
    ImprovedGCGAttack,
    TransferGCGAttack,
    GCGConfig,
    Candidate,
    GradientOptimizer,
    SemanticDiversitySelector,
    AdaptiveSearchController,
)
from mox.core import AttackType, AttackPayload, AttackResult
from mox.attacks.base import AttackConfig


class TestGCGConfig:
    """测试 GCG 配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = GCGConfig()

        assert config.max_iterations == 500
        assert config.batch_size == 128
        assert config.use_gradient_guidance is True
        assert config.use_warm_start is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = GCGConfig(
            max_iterations=100,
            batch_size=64,
            use_gradient_guidance=False,
        )

        assert config.max_iterations == 100
        assert config.batch_size == 64
        assert config.use_gradient_guidance is False


class TestCandidate:
    """测试候选"""

    def test_candidate_creation(self):
        """测试候选创建"""
        candidate = Candidate(
            suffix=" ! ! ! !",
            score=0.5,
            generation=1,
        )

        assert candidate.suffix == " ! ! ! !"
        assert candidate.score == 0.5
        assert candidate.generation == 1

    def test_candidate_default_values(self):
        """测试候选默认值"""
        candidate = Candidate(suffix="test")

        assert candidate.score == 0.0
        assert candidate.generation == 0


class TestGradientOptimizer:
    """测试梯度优化器"""

    def test_optimizer_creation(self):
        """测试优化器创建"""
        optimizer = GradientOptimizer("gpt2")

        assert optimizer.model_name == "gpt2"

    def test_suggest_replacements_no_model(self):
        """测试无模型时的替换建议"""
        optimizer = GradientOptimizer("gpt2")

        # 如果模型不可用，返回空列表
        suggestions = optimizer.suggest_replacements("test suffix", num_suggestions=5)

        assert isinstance(suggestions, list)


class TestSemanticDiversitySelector:
    """测试语义多样性选择器"""

    def test_selector_creation(self):
        """测试选择器创建"""
        selector = SemanticDiversitySelector()
        assert selector is not None

    def test_select_diverse(self):
        """测试多样性选择"""
        selector = SemanticDiversitySelector()
        
        candidates = [
            Candidate(suffix="suffix1", score=0.8),
            Candidate(suffix="suffix2", score=0.7),
            Candidate(suffix="suffix3", score=0.6),
        ]

        selected = selector.select_diverse(candidates, num_select=2)

        assert len(selected) <= 2
        assert all(isinstance(c, Candidate) for c in selected)


class TestAdaptiveSearchController:
    """测试自适应搜索控制器"""

    def test_controller_creation(self):
        """测试控制器创建"""
        controller = AdaptiveSearchController(window_size=20)
        
        assert controller.window_size == 20
        assert controller.mutation_rate == 0.1

    def test_update(self):
        """测试更新"""
        controller = AdaptiveSearchController()
        
        params = controller.update(0.5)

        assert "mutation_rate" in params
        assert "exploration_factor" in params

    def test_stagnation_handling(self):
        """测试停滞处理"""
        controller = AdaptiveSearchController()

        # 模拟停滞
        for _ in range(25):
            controller.update(0.5)  # 没有改进

        # 变异率应该增加
        assert controller.mutation_rate >= 0.1

    def test_get_stats(self):
        """测试获取统计"""
        controller = AdaptiveSearchController()
        controller.update(0.5)
        controller.update(0.6)

        stats = controller.get_stats()

        assert "best_score" in stats
        assert "avg_score" in stats


class TestImprovedGCGAttack:
    """测试改进的 GCG 攻击"""

    def test_attack_creation(self):
        """测试攻击创建"""
        mock_llm = MagicMock()
        config = AttackConfig(success_threshold=0.6)
        gcg_config = GCGConfig(
            max_iterations=10,
            batch_size=8,
            use_gradient_guidance=False,
            use_semantic_diversity=False,
        )
        attack = ImprovedGCGAttack(mock_llm, config, gcg_config)

        assert attack.attack_type == AttackType.GCG
        assert attack.gcg_config.max_iterations == 10

    def test_init_candidate_tokens(self):
        """测试候选 token 初始化"""
        mock_llm = MagicMock()
        config = AttackConfig()
        gcg_config = GCGConfig()
        attack = ImprovedGCGAttack(mock_llm, config, gcg_config)

        tokens = attack._init_candidate_tokens()

        assert len(tokens) > 0
        assert " !" in tokens

    def test_mutate(self):
        """测试变异"""
        mock_llm = MagicMock()
        config = AttackConfig()
        gcg_config = GCGConfig()
        attack = ImprovedGCGAttack(mock_llm, config, gcg_config)

        suffix = "test suffix"
        mutated = attack._mutate(suffix)

        assert isinstance(mutated, str)

    def test_crossover(self):
        """测试交叉"""
        mock_llm = MagicMock()
        config = AttackConfig()
        gcg_config = GCGConfig()
        attack = ImprovedGCGAttack(mock_llm, config, gcg_config)

        parent1 = "suffix one"
        parent2 = "suffix two"
        child = attack._crossover(parent1, parent2)

        assert isinstance(child, str)

    def test_generate_random_suffix(self):
        """测试随机后缀生成"""
        mock_llm = MagicMock()
        config = AttackConfig()
        gcg_config = GCGConfig()
        attack = ImprovedGCGAttack(mock_llm, config, gcg_config)

        suffix = attack._generate_random_suffix(20)

        assert len(suffix) > 0


class TestTransferGCGAttack:
    """测试迁移 GCG 攻击"""

    def test_attack_creation(self):
        """测试攻击创建"""
        mock_llm = MagicMock()
        config = AttackConfig(success_threshold=0.6)
        gcg_config = GCGConfig(
            max_iterations=5,
            use_gradient_guidance=False,
            use_semantic_diversity=False,
        )
        attack = TransferGCGAttack(mock_llm, config, gcg_config)

        assert attack.surrogate_models == []


class TestCandidateGeneration:
    """测试候选生成"""

    def test_candidate_pool_initialization(self):
        """测试候选池初始化"""
        mock_llm = MagicMock()
        config = AttackConfig()
        gcg_config = GCGConfig(
            max_iterations=5,
            top_k=16,
            num_elite=4,
            use_gradient_guidance=False,
            use_semantic_diversity=False,
        )
        attack = ImprovedGCGAttack(mock_llm, config, gcg_config)

        assert attack.gcg_config.top_k == 16
        assert attack.gcg_config.num_elite == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])