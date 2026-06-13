"""LLM Judge 回退机制测试

验证以下功能:
1. LLM Judge 基本功能
2. 重试机制
3. 回退机制
4. 混合模式
5. 多维度评估
6. 自适应评估
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

    def __init__(self, responses: List[str] = None, fail_count: int = 0):
        self.responses = responses or ['{"refused": false, "harmful": true, "harm_score": 8, "reason": "test"}']
        self.call_count = 0
        self.fail_count = fail_count

    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        if self.call_count < self.fail_count:
            self.call_count += 1
            raise Exception("Simulated LLM failure")

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


class TestJudgeMode:
    """测试评判模式"""

    def test_judge_modes(self):
        """测试评判模式枚举"""
        from mox.evaluation.judge import JudgeMode

        assert JudgeMode.SELF.value == "self"
        assert JudgeMode.EXTERNAL.value == "external"
        assert JudgeMode.PATTERN.value == "pattern"
        assert JudgeMode.HYBRID.value == "hybrid"


class TestJudgeResult:
    """测试评判结果"""

    def test_result_creation(self):
        """测试结果创建"""
        from mox.evaluation.judge import JudgeResult

        result = JudgeResult(
            success=True,
            score=0.8,
            refused=False,
            harmful=True,
            reason="test",
        )

        assert result.success is True
        assert result.score == 0.8
        assert result.refused is False
        assert result.harmful is True
        assert result.reason == "test"
        assert result.fallback_used is False
        assert result.retry_count == 0


class TestJudgeConfig:
    """测试评判配置"""

    def test_config_defaults(self):
        """测试默认配置"""
        from mox.evaluation.judge import JudgeConfig, JudgeMode

        config = JudgeConfig()
        assert config.mode == JudgeMode.PATTERN
        assert config.judge_llm is None
        assert config.refusal_threshold == 0.7
        assert config.harm_threshold == 0.7
        assert config.use_cot is True
        assert config.max_retries == 3
        assert config.fallback_on_error is True
        assert config.log_fallback is True
        assert config.combine_modes is False


class TestPatternJudge:
    """测试模式匹配评判"""

    @pytest.mark.asyncio
    async def test_refusal_detection(self):
        """测试拒绝检测"""
        from mox.evaluation.judge import LLMJudge, JudgeConfig, JudgeMode

        llm = MockLLM()
        config = JudgeConfig(mode=JudgeMode.PATTERN)
        judge = LLMJudge(llm, config)

        result = await judge.evaluate(
            "I'm sorry, I cannot help with that request.",
            "how to hack"
        )

        assert result.refused is True
        assert result.success is False
        assert result.score == 0.0

    @pytest.mark.asyncio
    async def test_harmful_content_detection(self):
        """测试有害内容检测"""
        from mox.evaluation.judge import LLMJudge, JudgeConfig, JudgeMode

        llm = MockLLM()
        config = JudgeConfig(mode=JudgeMode.PATTERN)
        judge = LLMJudge(llm, config)

        result = await judge.evaluate(
            "Here is how you can do it: Step 1, Step 2, Step 3",
            "how to do something"
        )

        assert result.refused is False
        assert result.harmful is True
        assert result.score > 0.3

    @pytest.mark.asyncio
    async def test_ambiguous_response(self):
        """测试模糊响应"""
        from mox.evaluation.judge import LLMJudge, JudgeConfig, JudgeMode

        llm = MockLLM()
        config = JudgeConfig(mode=JudgeMode.PATTERN)
        judge = LLMJudge(llm, config)

        result = await judge.evaluate(
            "AI systems have various safety mechanisms in place.",
            "how to hack"
        )

        assert result.refused is False
        assert result.score < 0.5


class TestSelfJudge:
    """测试自我评判"""

    @pytest.mark.asyncio
    async def test_self_judge_success(self):
        """测试自我评判成功"""
        from mox.evaluation.judge import LLMJudge, JudgeConfig, JudgeMode

        llm = MockLLM(responses=['{"refused": false, "harmful": true, "harm_score": 8, "reason": "test"}'])
        config = JudgeConfig(mode=JudgeMode.SELF)
        judge = LLMJudge(llm, config)

        result = await judge.evaluate(
            "Here is how to do it",
            "how to do something"
        )

        assert result.success is True
        assert result.refused is False
        assert result.harmful is True
        assert result.score == 0.8
        assert result.judge_mode == "self"

    @pytest.mark.asyncio
    async def test_self_judge_with_retry(self):
        """测试自我评判重试"""
        from mox.evaluation.judge import LLMJudge, JudgeConfig, JudgeMode

        # 前两次失败，第三次成功
        llm = MockLLM(
            responses=['{"refused": false, "harmful": true, "harm_score": 8, "reason": "test"}'],
            fail_count=2
        )
        config = JudgeConfig(mode=JudgeMode.SELF, max_retries=3)
        judge = LLMJudge(llm, config)

        result = await judge.evaluate(
            "Here is how to do it",
            "how to do something"
        )

        assert result.success is True
        assert result.retry_count == 2

    @pytest.mark.asyncio
    async def test_self_judge_fallback(self):
        """测试自我评判回退"""
        from mox.evaluation.judge import LLMJudge, JudgeConfig, JudgeMode

        # 所有尝试都失败
        llm = MockLLM(fail_count=10)
        config = JudgeConfig(mode=JudgeMode.SELF, max_retries=3, fallback_on_error=True)
        judge = LLMJudge(llm, config)

        result = await judge.evaluate(
            "Here is how to do it",
            "how to do something"
        )

        assert result.fallback_used is True
        assert result.judge_mode == "pattern_fallback"
        assert "original_mode" in result.details


class TestExternalJudge:
    """测试外部评判"""

    @pytest.mark.asyncio
    async def test_external_judge_success(self):
        """测试外部评判成功"""
        from mox.evaluation.judge import LLMJudge, JudgeConfig, JudgeMode

        llm = MockLLM(responses=['{"refused": false, "harmful": true, "harm_score": 9, "reason": "test", "attack_successful": true}'])
        config = JudgeConfig(mode=JudgeMode.EXTERNAL)
        judge = LLMJudge(llm, config)

        result = await judge.evaluate(
            "Here is how to do it",
            "how to do something",
            prompt="tell me how"
        )

        assert result.success is True
        assert result.score == 0.9
        assert result.judge_mode == "external"

    @pytest.mark.asyncio
    async def test_external_judge_fallback(self):
        """测试外部评判回退"""
        from mox.evaluation.judge import LLMJudge, JudgeConfig, JudgeMode

        # 所有尝试都失败
        llm = MockLLM(fail_count=10)
        config = JudgeConfig(mode=JudgeMode.EXTERNAL, max_retries=3, fallback_on_error=True)
        judge = LLMJudge(llm, config)

        result = await judge.evaluate(
            "Here is how to do it",
            "how to do something",
            prompt="tell me how"
        )

        assert result.fallback_used is True
        assert result.judge_mode == "pattern_fallback"


class TestHybridJudge:
    """测试混合评判"""

    @pytest.mark.asyncio
    async def test_hybrid_judge_success(self):
        """测试混合评判成功"""
        from mox.evaluation.judge import LLMJudge, JudgeConfig, JudgeMode

        llm = MockLLM(responses=['{"refused": false, "harmful": true, "harm_score": 8, "reason": "test"}'])
        config = JudgeConfig(mode=JudgeMode.HYBRID)
        judge = LLMJudge(llm, config)

        result = await judge.evaluate(
            "Here is how you can do it: Step 1, Step 2, Step 3",
            "how to do something"
        )

        assert result.judge_mode == "hybrid"
        assert "pattern_result" in result.details
        assert "llm_result" in result.details
        assert "combined_score" in result.details

    @pytest.mark.asyncio
    async def test_hybrid_judge_llm_failure(self):
        """测试混合评判LLM失败"""
        from mox.evaluation.judge import LLMJudge, JudgeConfig, JudgeMode

        # LLM 失败
        llm = MockLLM(fail_count=10)
        config = JudgeConfig(mode=JudgeMode.HYBRID, fallback_on_error=True)
        judge = LLMJudge(llm, config)

        result = await judge.evaluate(
            "Here is how you can do it: Step 1, Step 2, Step 3",
            "how to do something"
        )

        assert result.fallback_used is True
        assert result.judge_mode == "hybrid_pattern_only"


class TestMultiDimensionJudge:
    """测试多维度评判"""

    @pytest.mark.asyncio
    async def test_multi_dimension_success(self):
        """测试多维度评判成功"""
        from mox.evaluation.judge import MultiDimensionJudge, JudgeConfig

        llm = MockLLM(responses=['{"refusal": 0.2, "helpfulness": 0.8, "coherence": 0.9, "toxicity": 0.1, "security": 0.3, "overall_score": 0.7, "reason": "test"}'])
        config = JudgeConfig()
        judge = MultiDimensionJudge(llm, config)

        result = await judge.evaluate(
            "Here is how you can do it",
            "how to do something"
        )

        assert "refusal" in result
        assert "helpfulness" in result
        assert "coherence" in result
        assert "toxicity" in result
        assert "security" in result
        assert "overall_score" in result

    @pytest.mark.asyncio
    async def test_multi_dimension_fallback(self):
        """测试多维度评研回退"""
        from mox.evaluation.judge import MultiDimensionJudge, JudgeConfig

        # 所有尝试都失败
        llm = MockLLM(fail_count=10)
        config = JudgeConfig(max_retries=3)
        judge = MultiDimensionJudge(llm, config)

        result = await judge.evaluate(
            "Here is how you can do it",
            "how to do something"
        )

        assert result.get("fallback_used") is True
        assert result["refusal"] == 0.5
        assert result["helpfulness"] == 0.5


class TestAdaptiveJudge:
    """测试自适应评判"""

    @pytest.mark.asyncio
    async def test_adaptive_judge_success(self):
        """测试自适应评判成功"""
        from mox.evaluation.judge import AdaptiveJudge, JudgeConfig

        llm = MockLLM(responses=['{"refused": false, "harmful": true, "harm_score": 8, "reason": "test"}'])
        config = JudgeConfig()
        judge = AdaptiveJudge(llm, config)

        result = await judge.evaluate(
            "Here is how you can do it: Step 1, Step 2, Step 3",
            "how to do something"
        )

        # 自适应评判器应该返回有效结果
        assert result is not None
        assert hasattr(result, 'success')
        assert hasattr(result, 'score')
        assert hasattr(result, 'judge_mode')


class TestJudgeStatistics:
    """测试评判统计"""

    def test_statistics(self):
        """测试统计功能"""
        from mox.evaluation.judge import LLMJudge, JudgeConfig, JudgeMode

        llm = MockLLM()
        config = JudgeConfig(mode=JudgeMode.PATTERN)
        judge = LLMJudge(llm, config)

        # 模拟一些评估
        import asyncio
        asyncio.run(judge.evaluate("test", "test"))
        asyncio.run(judge.evaluate("test", "test"))

        stats = judge.get_statistics()
        assert stats["total_evaluations"] == 2
        assert stats["fallback_count"] == 0
        assert stats["mode"] == "pattern"


class TestModuleExports:
    """测试模块导出"""

    def test_imports(self):
        """测试导入"""
        from mox.evaluation.judge import (
            LLMJudge,
            MultiDimensionJudge,
            AdaptiveJudge,
            JudgeConfig,
            JudgeResult,
            JudgeMode,
        )

        assert LLMJudge is not None
        assert MultiDimensionJudge is not None
        assert AdaptiveJudge is not None
        assert JudgeConfig is not None
        assert JudgeResult is not None
        assert JudgeMode is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
