"""统一错误处理测试

验证以下功能:
1. 错误处理器
2. 错误装饰器
3. 错误上下文管理器
4. 重试机制
"""

import pytest
import asyncio

from mox.core.error_handling import (
    ErrorSeverity,
    ErrorCategory,
    ErrorInfo,
    MoxError,
    AttackError,
    EvaluationError,
    LLMError,
    TimeoutError,
    ErrorHandler,
    get_error_handler,
    async_error_handler,
    sync_error_handler,
    retry_on_error,
    ErrorContext,
    handle_llm_error,
    handle_attack_error,
    handle_evaluation_error,
    create_error_response,
)


class TestErrorSeverity:
    """测试错误严重程度"""

    def test_severity_levels(self):
        """测试严重程度级别"""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestErrorCategory:
    """测试错误类别"""

    def test_categories(self):
        """测试错误类别"""
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.TIMEOUT.value == "timeout"
        assert ErrorCategory.LLM.value == "llm"
        assert ErrorCategory.ATTACK.value == "attack"
        assert ErrorCategory.EVALUATION.value == "evaluation"


class TestMoxError:
    """测试 MoxError"""

    def test_basic_error(self):
        """测试基本错误"""
        error = MoxError("Test error")
        assert str(error) == "Test error"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.category == ErrorCategory.UNKNOWN

    def test_custom_error(self):
        """测试自定义错误"""
        error = MoxError(
            "Test error",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.ATTACK,
            metadata={"key": "value"},
        )
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.ATTACK
        assert error.metadata == {"key": "value"}


class TestAttackError:
    """测试 AttackError"""

    def test_attack_error(self):
        """测试攻击错误"""
        error = AttackError("Attack failed")
        assert str(error) == "Attack failed"
        assert error.severity == ErrorSeverity.HIGH
        assert error.category == ErrorCategory.ATTACK


class TestEvaluationError:
    """测试 EvaluationError"""

    def test_evaluation_error(self):
        """测试评估错误"""
        error = EvaluationError("Evaluation failed")
        assert str(error) == "Evaluation failed"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.category == ErrorCategory.EVALUATION


class TestLLMError:
    """测试 LLMError"""

    def test_llm_error(self):
        """测试 LLM 错误"""
        error = LLMError("LLM failed")
        assert str(error) == "LLM failed"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.category == ErrorCategory.LLM


class TestErrorHandler:
    """测试错误处理器"""

    def test_handler_creation(self):
        """测试处理器创建"""
        handler = ErrorHandler()
        assert handler.log_errors is True
        assert handler.raise_on_critical is True

    def test_handle_error(self):
        """测试处理错误"""
        handler = ErrorHandler(log_errors=False)

        error = ValueError("Test error")
        error_info = handler.handle_error(error, context="test")

        assert error_info.error == error
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.category == ErrorCategory.VALIDATION
        assert error_info.context == "test"
        assert error_info.retryable is False

    def test_handle_attack_error(self):
        """测试处理攻击错误"""
        handler = ErrorHandler(log_errors=False)

        error = AttackError("Attack failed")
        error_info = handler.handle_error(error, context="test")

        assert error_info.severity == ErrorSeverity.HIGH
        assert error_info.category == ErrorCategory.ATTACK

    def test_error_history(self):
        """测试错误历史"""
        handler = ErrorHandler(log_errors=False)

        handler.handle_error(ValueError("Error 1"))
        handler.handle_error(TypeError("Error 2"))

        history = handler.get_error_history()
        assert len(history) == 2

    def test_error_stats(self):
        """测试错误统计"""
        handler = ErrorHandler(log_errors=False)

        handler.handle_error(ValueError("Error 1"))
        handler.handle_error(AttackError("Error 2"))
        handler.handle_error(TimeoutError("Error 3"))

        stats = handler.get_error_stats()
        assert stats["total"] == 3
        assert "by_severity" in stats
        assert "by_category" in stats

    def test_clear_history(self):
        """测试清除历史"""
        handler = ErrorHandler(log_errors=False)

        handler.handle_error(ValueError("Error 1"))
        handler.clear_history()

        history = handler.get_error_history()
        assert len(history) == 0


class TestAsyncErrorHandler:
    """测试异步错误处理装饰器"""

    @pytest.mark.asyncio
    async def test_no_error(self):
        """测试无错误情况"""
        @async_error_handler()
        async def success_func():
            return "success"

        result = await success_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_with_error(self):
        """测试有错误情况"""
        @async_error_handler(default_return="default")
        async def error_func():
            raise ValueError("Test error")

        result = await error_func()
        assert result == "default"

    @pytest.mark.asyncio
    async def test_reraise(self):
        """测试重新抛出异常"""
        @async_error_handler(reraise=True)
        async def error_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await error_func()


class TestSyncErrorHandler:
    """测试同步错误处理装饰器"""

    def test_no_error(self):
        """测试无错误情况"""
        @sync_error_handler()
        def success_func():
            return "success"

        result = success_func()
        assert result == "success"

    def test_with_error(self):
        """测试有错误情况"""
        @sync_error_handler(default_return="default")
        def error_func():
            raise ValueError("Test error")

        result = error_func()
        assert result == "default"


class TestRetryOnError:
    """测试重试装饰器"""

    @pytest.mark.asyncio
    async def test_success_first_try(self):
        """测试首次成功"""
        call_count = 0

        @retry_on_error(max_retries=3)
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await success_func()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_success_after_retry(self):
        """测试重试后成功"""
        call_count = 0

        @retry_on_error(max_retries=3, delay=0.01)
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"

        result = await flaky_func()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_all_retries_fail(self):
        """测试所有重试失败"""
        @retry_on_error(max_retries=2, delay=0.01)
        async def always_fail():
            raise ValueError("Always fail")

        with pytest.raises(ValueError):
            await always_fail()


class TestErrorContext:
    """测试错误上下文管理器"""

    @pytest.mark.asyncio
    async def test_no_error(self):
        """测试无错误情况"""
        async with ErrorContext("test"):
            pass  # 无错误

    @pytest.mark.asyncio
    async def test_with_error(self):
        """测试有错误情况"""
        with pytest.raises(ValueError):
            async with ErrorContext("test"):
                raise ValueError("Test error")


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_handle_llm_error(self):
        """测试处理 LLM 错误"""
        error = ValueError("LLM error")
        error_info = handle_llm_error(error, "test")

        assert error_info.category == ErrorCategory.LLM

    def test_handle_attack_error(self):
        """测试处理攻击错误"""
        error = ValueError("Attack error")
        error_info = handle_attack_error(error, "test")

        assert error_info.category == ErrorCategory.ATTACK

    def test_handle_evaluation_error(self):
        """测试处理评估错误"""
        error = ValueError("Evaluation error")
        error_info = handle_evaluation_error(error, "test")

        assert error_info.category == ErrorCategory.EVALUATION

    def test_create_error_response(self):
        """测试创建错误响应"""
        error = ValueError("Test error")
        response = create_error_response(error, "test")

        assert response["success"] is False
        assert "error" in response
        assert "error_type" in response


class TestModuleExports:
    """测试模块导出"""

    def test_imports(self):
        """测试导入"""
        from mox.core.error_handling import (
            ErrorSeverity,
            ErrorCategory,
            ErrorInfo,
            MoxError,
            AttackError,
            EvaluationError,
            LLMError,
            TimeoutError,
            ErrorHandler,
            get_error_handler,
            async_error_handler,
            sync_error_handler,
            retry_on_error,
            ErrorContext,
            handle_llm_error,
            handle_attack_error,
            handle_evaluation_error,
            create_error_response,
        )

        assert ErrorSeverity is not None
        assert ErrorCategory is not None
        assert ErrorInfo is not None
        assert MoxError is not None
        assert AttackError is not None
        assert EvaluationError is not None
        assert LLMError is not None
        assert TimeoutError is not None
        assert ErrorHandler is not None
        assert get_error_handler is not None
        assert async_error_handler is not None
        assert sync_error_handler is not None
        assert retry_on_error is not None
        assert ErrorContext is not None
        assert handle_llm_error is not None
        assert handle_attack_error is not None
        assert handle_evaluation_error is not None
        assert create_error_response is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
