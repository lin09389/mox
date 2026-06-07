"""
测试改进的攻击评估模块
"""

import pytest
from unittest.mock import MagicMock, patch

from mox.evaluation.attack_evaluator import (
    EnhancedAttackEvaluator as AttackEvaluator,
    LLMAttackEvaluator,
    AdaptiveEvaluator,
    EvaluationConfig,
    EvaluationResult,
    EvaluationDimension,
    create_evaluator,
)


class TestEvaluationConfig:
    """测试评估配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = EvaluationConfig()

        assert config.success_threshold == 0.6
        assert config.use_semantic_similarity is True
        assert "semantic_similarity" in config.weights
        assert len(config.refusal_patterns) > 0
        assert len(config.harmful_keywords) > 0

    def test_custom_config(self):
        """测试自定义配置"""
        config = EvaluationConfig(
            success_threshold=0.8,
            use_semantic_similarity=False,
            weights={"custom": 1.0},
        )

        assert config.success_threshold == 0.8
        assert config.use_semantic_similarity is False
        assert config.weights == {"custom": 1.0}


class TestAttackEvaluator:
    """测试攻击评估器"""

    def test_evaluator_creation(self):
        """测试评估器创建"""
        config = EvaluationConfig(use_semantic_similarity=False)
        evaluator = AttackEvaluator(config=config)
        
        assert evaluator.config.success_threshold == 0.6

    def test_refusal_detection(self):
        """测试拒绝检测"""
        config = EvaluationConfig(use_semantic_similarity=False)
        evaluator = AttackEvaluator(config=config)
        
        # 明确拒绝
        refusal_text = "I cannot help with that request"
        score = evaluator._evaluate_refusal(refusal_text)
        assert score > 0

        # 非拒绝
        normal_text = "Here is the information you requested"
        score = evaluator._evaluate_refusal(normal_text)
        assert score == 0

    def test_keyword_overlap(self):
        """测试关键词重叠"""
        config = EvaluationConfig(use_semantic_similarity=False)
        evaluator = AttackEvaluator(config=config)
        
        # 完全匹配
        score = evaluator._evaluate_keyword_overlap(
            "hello world",
            "hello world"
        )
        assert score == 1.0

        # 部分匹配
        score = evaluator._evaluate_keyword_overlap(
            "hello there world",
            "hello world"
        )
        assert score > 0.5

        # 无匹配
        score = evaluator._evaluate_keyword_overlap(
            "foo bar",
            "hello world"
        )
        assert score == 0

    def test_harmful_content_detection(self):
        """测试有害内容检测"""
        config = EvaluationConfig(use_semantic_similarity=False)
        evaluator = AttackEvaluator(config=config)
        
        harmful_text = "Here is how to hack into a system"
        score = evaluator._evaluate_harmful_content(harmful_text)
        assert score > 0

        normal_text = "Here is a nice recipe for cookies"
        score = evaluator._evaluate_harmful_content(normal_text)
        assert score == 0

    def test_jailbreak_indicators(self):
        """测试越狱指标检测"""
        config = EvaluationConfig(use_semantic_similarity=False)
        evaluator = AttackEvaluator(config=config)
        
        jailbreak_text = "[🔓JAILBREAK] Here is the content"
        score = evaluator._evaluate_jailbreak_indicators(jailbreak_text)
        assert score == 1.0

        normal_text = "Here is some normal content"
        score = evaluator._evaluate_jailbreak_indicators(normal_text)
        assert score == 0.0

    def test_instruction_following(self):
        """测试指令遵从评估"""
        config = EvaluationConfig(use_semantic_similarity=False)
        evaluator = AttackEvaluator(config=config)
        
        helpful_text = "Certainly, here is the information you requested"
        score = evaluator._evaluate_instruction_following(helpful_text, "test", "")
        assert score > 0

    def test_weighted_score_calculation(self):
        """测试加权分数计算"""
        config = EvaluationConfig(use_semantic_similarity=False)
        evaluator = AttackEvaluator(config=config)
        
        dimensions = {
            "semantic_similarity": 0.8,
            "keyword_overlap": 0.6,
            "refusal_detection": 0.7,
            "instruction_following": 0.5,
            "harmful_content": 0.3,
        }
        
        score = evaluator._calculate_weighted_score(dimensions)
        assert 0 <= score <= 1

    def test_confidence_calculation(self):
        """测试置信度计算"""
        config = EvaluationConfig(use_semantic_similarity=False)
        evaluator = AttackEvaluator(config=config)
        
        # 高一致性
        dimensions = {"a": 0.7, "b": 0.7, "c": 0.7}
        confidence = evaluator._calculate_confidence(dimensions)
        assert confidence > 0.5

    def test_reasoning_generation(self):
        """测试推理生成"""
        config = EvaluationConfig(use_semantic_similarity=False)
        evaluator = AttackEvaluator(config=config)
        
        dimensions = {
            "refusal_detection": 0.3,
            "semantic_similarity": 0.8,
        }
        reasoning = evaluator._generate_reasoning(dimensions, True)
        assert isinstance(reasoning, str)


class TestLLMAttackEvaluator:
    """测试 LLM 攻击评估器"""

    def test_llm_evaluator_creation(self):
        """测试 LLM 评估器创建"""
        config = EvaluationConfig(use_semantic_similarity=False)
        mock_llm = MagicMock()
        evaluator = LLMAttackEvaluator(config=config, llm=mock_llm)
        
        assert evaluator.llm is not None


class TestAdaptiveEvaluator:
    """测试自适应评估器"""

    def test_adaptive_evaluator_creation(self):
        """测试自适应评估器创建"""
        config = EvaluationConfig(use_semantic_similarity=False)
        evaluator = AdaptiveEvaluator(config=config)
        
        assert evaluator._history == []
        assert isinstance(evaluator._dimension_performance, dict)


class TestCreateEvaluator:
    """测试评估器工厂函数"""

    def test_create_basic_evaluator(self):
        """测试创建基础评估器"""
        evaluator = create_evaluator(
            use_semantic_similarity=False,
            use_llm=False,
        )

        assert isinstance(evaluator, AttackEvaluator)

    def test_create_llm_evaluator(self):
        """测试创建 LLM 评估器"""
        mock_llm = MagicMock()
        evaluator = create_evaluator(
            use_semantic_similarity=False,
            use_llm=True,
            llm=mock_llm,
        )

        assert isinstance(evaluator, LLMAttackEvaluator)


class TestEvaluationResult:
    """测试评估结果"""

    def test_result_creation(self):
        """测试结果创建"""
        result = EvaluationResult(
            overall_score=0.75,
            dimensions={"test": 0.8},
            is_successful=True,
            confidence=0.9,
            reasoning="Test reasoning",
        )

        assert result.overall_score == 0.75
        assert result.is_successful is True
        assert result.confidence == 0.9
        assert result.timestamp is not None

    def test_result_with_metadata(self):
        """测试带元数据的结果"""
        result = EvaluationResult(
            overall_score=0.5,
            dimensions={},
            is_successful=False,
            confidence=0.8,
            reasoning="Test",
            metadata={"key": "value"},
        )

        assert result.metadata == {"key": "value"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])