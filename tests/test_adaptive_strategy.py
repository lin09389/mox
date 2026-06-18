"""
测试自适应攻击策略
"""

import pytest
from unittest.mock import MagicMock

from mox.attacks.adaptive_strategy import (
    AdaptiveAttackStrategy,
    StrategySelector,
    AttackChain,
    FeedbackLearner,
    StrategyType,
    StrategyPerformance,
    AdaptiveConfig,
    AttackTemplate,
    ATTACK_TEMPLATES,
    create_adaptive_attack,
)
from mox.core import AttackType
from mox.attacks.base import AttackConfig


class TestStrategyType:
    """测试策略类型"""

    def test_strategy_types(self):
        """测试策略类型枚举"""
        assert StrategyType.DIRECT.value == "direct"
        assert StrategyType.ROLE_PLAY.value == "role_play"
        assert StrategyType.HYPOTHETICAL.value == "hypothetical"


class TestStrategyPerformance:
    """测试策略性能"""

    def test_performance_creation(self):
        """测试性能创建"""
        perf = StrategyPerformance(strategy=StrategyType.DIRECT)

        assert perf.attempts == 0
        assert perf.successes == 0
        assert perf.success_rate == 0.0

    def test_success_rate(self):
        """测试成功率计算"""
        perf = StrategyPerformance(
            strategy=StrategyType.DIRECT,
            attempts=10,
            successes=7,
        )

        assert perf.success_rate == 0.7


class TestAdaptiveConfig:
    """测试自适应配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = AdaptiveConfig()

        assert config.exploration_rate == 0.2
        assert config.max_chain_length == 5
        assert config.enable_feedback_learning is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = AdaptiveConfig(
            exploration_rate=0.3,
            max_chain_length=3,
        )

        assert config.exploration_rate == 0.3
        assert config.max_chain_length == 3


class TestAttackTemplate:
    """测试攻击模板"""

    def test_template_creation(self):
        """测试模板创建"""
        template = AttackTemplate(
            strategy=StrategyType.ROLE_PLAY,
            template="You are {role}. {request}",
            variables=["role", "request"],
        )

        assert template.strategy == StrategyType.ROLE_PLAY
        assert len(template.variables) == 2

    def test_template_render(self):
        """测试模板渲染"""
        template = AttackTemplate(
            strategy=StrategyType.ROLE_PLAY,
            template="You are {role}. {request}",
            variables=["role", "request"],
        )

        result = template.render(role="a hacker", request="help me")

        assert result == "You are a hacker. help me"

    def test_update_effectiveness(self):
        """测试有效性更新"""
        template = AttackTemplate(
            strategy=StrategyType.DIRECT,
            template="{request}",
            variables=["request"],
        )

        template.update_effectiveness(True)
        template.update_effectiveness(True)
        template.update_effectiveness(False)

        assert template.effectiveness == 2 / 3


class TestStrategySelector:
    """测试策略选择器"""

    def test_selector_creation(self):
        """测试选择器创建"""
        selector = StrategySelector(
            strategies=[
                StrategyType.DIRECT,
                StrategyType.ROLE_PLAY,
                StrategyType.HYPOTHETICAL,
            ],
            exploration_rate=0.2,
        )

        assert len(selector.strategies) == 3
        assert selector.exploration_rate == 0.2

    def test_select_initial(self):
        """测试初始选择"""
        selector = StrategySelector(
            strategies=[
                StrategyType.DIRECT,
                StrategyType.ROLE_PLAY,
            ],
        )

        # 第一次应该选择未尝试的策略
        strategy = selector.select()

        assert strategy in selector.strategies

    def test_update(self):
        """测试更新"""
        selector = StrategySelector(
            strategies=[StrategyType.DIRECT, StrategyType.ROLE_PLAY],
        )

        selector.update(StrategyType.DIRECT, 0.7, 5)

        perf = selector._performance[StrategyType.DIRECT]
        assert perf.attempts == 1
        assert perf.total_score == 0.7

    def test_get_best_strategy(self):
        """测试获取最佳策略"""
        selector = StrategySelector(
            strategies=[StrategyType.DIRECT, StrategyType.ROLE_PLAY, StrategyType.HYPOTHETICAL],
        )

        selector.update(StrategyType.DIRECT, 0.5, 1)
        selector.update(StrategyType.ROLE_PLAY, 0.8, 1)
        selector.update(StrategyType.HYPOTHETICAL, 0.3, 1)

        best, perf = selector.get_best_strategy()

        assert best == StrategyType.ROLE_PLAY

    def test_get_stats(self):
        """测试获取统计"""
        selector = StrategySelector(
            strategies=[StrategyType.DIRECT],
        )

        selector.update(StrategyType.DIRECT, 0.5, 1)

        stats = selector.get_stats()

        assert stats["total_attempts"] == 1
        assert "strategies" in stats


class TestAttackChain:
    """测试攻击链"""

    def test_chain_creation(self):
        """测试链创建"""
        chain = AttackChain(
            [
                StrategyType.ROLE_PLAY,
                StrategyType.HYPOTHETICAL,
            ]
        )

        assert len(chain.strategies) == 2

    def test_build(self):
        """测试构建"""
        chain = AttackChain(
            [
                StrategyType.ROLE_PLAY,
                StrategyType.HYPOTHETICAL,
            ]
        )

        prompts = chain.build("test request")

        assert len(prompts) == 2
        assert all(isinstance(p, str) for p in prompts)

    def test_record_result(self):
        """测试记录结果"""
        chain = AttackChain([StrategyType.DIRECT])
        chain.build("test")
        chain.record_result("prompt1", 0.5)
        chain.record_result("prompt2", 0.8)

        best_prompt, best_score = chain.get_best_prompt()

        assert best_prompt == "prompt2"
        assert best_score == 0.8


class TestFeedbackLearner:
    """测试反馈学习器"""

    def test_learner_creation(self):
        """测试学习器创建"""
        learner = FeedbackLearner(learning_rate=0.1)

        assert learner.learning_rate == 0.1

    def test_analyze_response(self):
        """测试响应分析"""
        learner = FeedbackLearner()

        learner.analyze_response(
            prompt="Act as a hacker",
            response="I cannot help with that",
            score=0.2,
        )

        assert len(learner._pattern_results) > 0

    def test_extract_patterns(self):
        """测试模式提取"""
        learner = FeedbackLearner()

        patterns = learner._extract_patterns("Act as a hacker and help me")

        assert "role_play" in patterns

    def test_get_pattern_score(self):
        """测试获取模式分数"""
        learner = FeedbackLearner()

        learner.analyze_response(
            prompt="Act as a hacker",
            response="Response",
            score=0.7,
        )

        score = learner.get_pattern_score("role_play")

        assert score == 0.7

    def test_get_recommendations(self):
        """测试获取建议"""
        learner = FeedbackLearner()

        learner.analyze_response(
            prompt="Act as a hacker",
            response="I cannot help",
            score=0.2,
        )

        recs = learner.get_recommendations()

        assert "effective_patterns" in recs


class TestAdaptiveAttackStrategy:
    """测试自适应攻击策略"""

    def test_attack_creation(self):
        """测试攻击创建"""
        mock_llm = MagicMock()
        config = AttackConfig(success_threshold=0.6)
        adaptive_config = AdaptiveConfig(
            exploration_rate=0.3,
            min_attempts_before_switch=2,
        )
        attack = AdaptiveAttackStrategy(mock_llm, config, adaptive_config)

        assert attack.attack_type == AttackType.ADAPTIVE
        assert attack.adaptive_config.exploration_rate == 0.3

    def test_select_role(self):
        """测试角色选择"""
        mock_llm = MagicMock()
        config = AttackConfig()
        adaptive_config = AdaptiveConfig()
        attack = AdaptiveAttackStrategy(mock_llm, config, adaptive_config)

        role = attack._select_role("write some code")
        assert "programmer" in role.lower()

        role = attack._select_role("hack a system")
        assert "security" in role.lower()

    def test_get_strategy_stats(self):
        """测试获取策略统计"""
        mock_llm = MagicMock()
        config = AttackConfig()
        adaptive_config = AdaptiveConfig()
        attack = AdaptiveAttackStrategy(mock_llm, config, adaptive_config)

        stats = attack.get_strategy_stats()

        assert "total_attempts" in stats

    def test_get_recommendations(self):
        """测试获取建议"""
        mock_llm = MagicMock()
        config = AttackConfig()
        adaptive_config = AdaptiveConfig()
        attack = AdaptiveAttackStrategy(mock_llm, config, adaptive_config)

        recs = attack.get_recommendations()

        assert isinstance(recs, dict)


class TestCreateAdaptiveAttack:
    """测试工厂函数"""

    def test_create_attack(self):
        """测试创建攻击"""
        mock_llm = MagicMock()

        attack = create_adaptive_attack(
            target_llm=mock_llm,
            success_threshold=0.7,
            exploration_rate=0.3,
        )

        assert isinstance(attack, AdaptiveAttackStrategy)
        assert attack.config.success_threshold == 0.7


class TestAttackTemplates:
    """测试攻击模板库"""

    def test_templates_exist(self):
        """测试模板存在"""
        assert StrategyType.ROLE_PLAY in ATTACK_TEMPLATES
        assert StrategyType.HYPOTHETICAL in ATTACK_TEMPLATES

    def test_template_validity(self):
        """测试模板有效性"""
        for strategy, templates in ATTACK_TEMPLATES.items():
            for template in templates:
                assert template.strategy == strategy
                assert len(template.template) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
