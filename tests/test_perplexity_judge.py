"""
测试困惑度计算和 LLM Judge
"""

import pytest
from unittest.mock import MagicMock

from mox.evaluation.perplexity_judge import (
    AccuratePerplexityCalculator,
    PerplexityConfig,
    PerplexityResult,
    StableLLMJudge,
    LLMJudgeConfig,
    JudgeEvaluation,
    ComprehensiveEvaluator,
)


class TestPerplexityConfig:
    """测试困惑度配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = PerplexityConfig()

        assert config.model_name == "gpt2"
        assert config.max_length == 1024
        assert config.stride == 512
        assert config.normalize is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = PerplexityConfig(
            model_name="gpt2-medium",
            max_length=2048,
            stride=1024,
        )

        assert config.model_name == "gpt2-medium"
        assert config.max_length == 2048
        assert config.stride == 1024


class TestPerplexityResult:
    """测试困惑度结果"""

    def test_result_creation(self):
        """测试结果创建"""
        result = PerplexityResult(
            perplexity=50.0,
            log_perplexity=3.91,
            token_count=100,
            is_anomalous=False,
            anomaly_score=0.2,
        )

        assert result.perplexity == 50.0
        assert result.log_perplexity == 3.91
        assert result.token_count == 100
        assert result.is_anomalous is False

    def test_result_with_segment_scores(self):
        """测试带分段分数的结果"""
        result = PerplexityResult(
            perplexity=30.0,
            log_perplexity=3.4,
            token_count=50,
            is_anomalous=True,
            anomaly_score=0.8,
            segment_scores=[25.0, 35.0, 30.0],
        )

        assert len(result.segment_scores) == 3


class TestAccuratePerplexityCalculator:
    """测试准确困惑度计算器"""

    def test_calculator_creation(self):
        """测试计算器创建"""
        calculator = AccuratePerplexityCalculator()
        assert calculator.config.model_name == "gpt2"

    def test_detect_anomaly(self):
        """测试异常检测"""
        calculator = AccuratePerplexityCalculator()

        # 低困惑度
        is_anomalous, score = calculator._detect_anomaly(5.0, [5.0, 5.1, 4.9])
        assert is_anomalous is True

        # 正常困惑度
        is_anomalous, score = calculator._detect_anomaly(50.0, [45.0, 55.0, 50.0])
        assert is_anomalous is False

    def test_fallback_calculate(self):
        """测试回退计算方法"""
        calculator = AccuratePerplexityCalculator()

        result = calculator._fallback_calculate("Hello world this is a test")

        assert isinstance(result, PerplexityResult)
        assert result.perplexity > 0

    def test_fallback_empty_text(self):
        """测试空文本回退"""
        calculator = AccuratePerplexityCalculator()

        result = calculator._fallback_calculate("")

        assert isinstance(result, PerplexityResult)


class TestLLMJudgeConfig:
    """测试 LLM Judge 配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = LLMJudgeConfig()

        assert config.num_samples == 3
        assert config.temperature == 0.3
        assert config.consistency_threshold == 0.7

    def test_custom_config(self):
        """测试自定义配置"""
        config = LLMJudgeConfig(
            num_samples=5,
            temperature=0.1,
        )

        assert config.num_samples == 5
        assert config.temperature == 0.1


class TestJudgeEvaluation:
    """测试 Judge 评估结果"""

    def test_evaluation_creation(self):
        """测试结果创建"""
        result = JudgeEvaluation(
            overall_score=0.75,
            dimension_scores={"relevance": 0.8, "harmfulness": 0.3},
            confidence=0.9,
            consistency=0.85,
            reasoning="Test reasoning",
        )

        assert result.overall_score == 0.75
        assert result.confidence == 0.9
        assert result.consistency == 0.85

    def test_evaluation_with_raw_responses(self):
        """测试带原始响应的结果"""
        result = JudgeEvaluation(
            overall_score=0.5,
            dimension_scores={},
            confidence=0.8,
            consistency=0.7,
            reasoning="Test",
            raw_responses=["response1", "response2"],
        )

        assert len(result.raw_responses) == 2


class TestStableLLMJudge:
    """测试稳定 LLM Judge"""

    def test_judge_creation(self):
        """测试 Judge 创建"""
        mock_llm = MagicMock()
        config = LLMJudgeConfig(num_samples=2)
        judge = StableLLMJudge(mock_llm, config)

        assert judge.config.num_samples == 2

    def test_build_eval_prompt(self):
        """测试构建评估提示"""
        mock_llm = MagicMock()
        config = LLMJudgeConfig()
        judge = StableLLMJudge(mock_llm, config)

        prompt = judge._build_eval_prompt(
            "Test response",
            "Test target",
            "Original prompt",
        )

        assert "Test response" in prompt
        assert "Test target" in prompt
        assert "relevance" in prompt.lower()

    def test_parse_response_json(self):
        """测试 JSON 解析"""
        mock_llm = MagicMock()
        config = LLMJudgeConfig()
        judge = StableLLMJudge(mock_llm, config)

        response = '{"overall_score": 0.75, "relevance": 0.8}'

        result = judge._parse_response(response)

        assert result["overall_score"] == 0.75
        assert result["dimensions"]["relevance"] == 0.8

    def test_parse_response_number(self):
        """测试数字解析"""
        mock_llm = MagicMock()
        config = LLMJudgeConfig()
        judge = StableLLMJudge(mock_llm, config)

        response = "The score is 0.65"

        result = judge._parse_response(response)

        assert result["overall_score"] == 0.65

    def test_calculate_consistency(self):
        """测试一致性计算"""
        mock_llm = MagicMock()
        config = LLMJudgeConfig()
        judge = StableLLMJudge(mock_llm, config)

        # 高一致性
        consistency = judge._calculate_consistency([0.7, 0.71, 0.69])
        assert consistency > 0.8

        # 低一致性
        consistency = judge._calculate_consistency([0.3, 0.7, 0.5])
        assert consistency < 0.8

    def test_calculate_confidence(self):
        """测试置信度计算"""
        mock_llm = MagicMock()
        config = LLMJudgeConfig()
        judge = StableLLMJudge(mock_llm, config)

        confidence = judge._calculate_confidence([0.7, 0.7, 0.7], 0.9)

        assert 0 <= confidence <= 1

    def test_generate_reasoning(self):
        """测试推理生成"""
        mock_llm = MagicMock()
        config = LLMJudgeConfig()
        judge = StableLLMJudge(mock_llm, config)

        reasoning = judge._generate_reasoning(
            {"relevance": 0.8, "harmfulness": 0.3, "refusal": 0.2},
            0.9,
            0.85,
        )

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0


class TestComprehensiveEvaluator:
    """测试综合评估器"""

    def test_evaluator_creation(self):
        """测试评估器创建"""
        evaluator = ComprehensiveEvaluator(
            use_perplexity=False,
            use_llm_judge=False,
        )

        assert evaluator.perplexity_calculator is None
        assert evaluator.llm_judge is None

    def test_rule_based_evaluation(self):
        """测试规则评估"""
        evaluator = ComprehensiveEvaluator(
            use_perplexity=False,
            use_llm_judge=False,
        )

        result = evaluator._rule_based_evaluation(
            "Here is the harmful content",
            "harmful content",
        )

        assert result["target_match"] == 1.0
        assert result["harmful_detected"] is True

    def test_rule_based_refusal(self):
        """测试拒绝检测"""
        evaluator = ComprehensiveEvaluator(
            use_perplexity=False,
            use_llm_judge=False,
        )

        result = evaluator._rule_based_evaluation(
            "I cannot help with that request",
            "help",
        )

        assert result["refusal_detected"] is True

    def test_calculate_overall(self):
        """测试综合分数计算"""
        evaluator = ComprehensiveEvaluator(
            use_perplexity=False,
            use_llm_judge=False,
        )

        results = {
            "llm_judge": {"overall_score": 0.7},
            "rules": {"target_match": 0.8, "refusal_detected": False},
        }

        overall = evaluator._calculate_overall(results)

        assert 0 <= overall <= 1


class TestPerplexityAnomalyDetection:
    """测试困惑度异常检测"""

    def test_low_perplexity_anomaly(self):
        """测试低困惑度异常"""
        calculator = AccuratePerplexityCalculator()

        # 困惑度极低可能是对抗样本
        is_anomalous, score = calculator._detect_anomaly(3.0, [3.0, 3.1, 2.9])

        assert is_anomalous is True
        assert score > 0.5

    def test_high_variance_normal(self):
        """测试高方差正常"""
        calculator = AccuratePerplexityCalculator()

        # 方差大说明是正常文本
        is_anomalous, score = calculator._detect_anomaly(50.0, [30.0, 70.0, 50.0])

        assert is_anomalous is False


class TestLLMJudgeStability:
    """测试 LLM Judge 稳定性"""

    def test_consistency_calculation(self):
        """测试一致性计算"""
        mock_llm = MagicMock()
        config = LLMJudgeConfig()
        judge = StableLLMJudge(mock_llm, config)

        # 响应一致，一致性应该高
        scores = [0.7, 0.72, 0.68]
        consistency = judge._calculate_consistency(scores)

        assert consistency > 0.8

    def test_confidence_with_extreme_scores(self):
        """测试极端分数的置信度"""
        mock_llm = MagicMock()
        config = LLMJudgeConfig()
        judge = StableLLMJudge(mock_llm, config)

        # 极端分数（接近0或1）通常更可信
        confidence_high = judge._calculate_confidence([0.9, 0.9, 0.9], 0.9)
        confidence_mid = judge._calculate_confidence([0.5, 0.5, 0.5], 0.9)

        assert confidence_high > confidence_mid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])