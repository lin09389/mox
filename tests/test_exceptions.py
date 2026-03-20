"""
异常模块测试
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mox.core.exceptions import (
    MoxException,
    ErrorCode,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    AttackError,
    DefenseError,
    GatewayError,
    RateLimitError,
)


class TestExceptions:
    """异常类测试"""

    def test_mox_exception_basic(self):
        """测试基础异常"""
        exc = MoxException(
            code=ErrorCode.INTERNAL_ERROR,
            message="Test error",
        )
        assert exc.code == ErrorCode.INTERNAL_ERROR
        assert exc.message == "Test error"
        assert exc.status_code == 400

    def test_mox_exception_to_dict(self):
        """测试异常转字典"""
        exc = MoxException(
            code=ErrorCode.INVALID_REQUEST,
            message="Invalid request",
            details={"field": "name"},
        )
        result = exc.to_dict()
        assert result["error"] == "INVALID_REQUEST"
        assert result["message"] == "Invalid request"
        assert result["details"]["field"] == "name"

    def test_authentication_error(self):
        """测试认证错误"""
        exc = AuthenticationError(message="Invalid credentials")
        assert exc.code == ErrorCode.UNAUTHORIZED
        assert exc.status_code == 401

    def test_authorization_error(self):
        """测试授权错误"""
        exc = AuthorizationError(
            message="Access denied",
            required_scope="admin"
        )
        assert exc.code == ErrorCode.INSUFFICIENT_SCOPE
        assert exc.status_code == 403
        assert exc.details["required_scope"] == "admin"

    def test_not_found_error(self):
        """测试资源未找到错误"""
        exc = NotFoundError(resource="User", identifier="123")
        assert exc.code == ErrorCode.NOT_FOUND
        assert exc.status_code == 404
        assert "User" in exc.message
        assert "123" in exc.message

    def test_validation_error(self):
        """测试验证错误"""
        exc = ValidationError(
            message="Invalid email",
            field="email",
            value="invalid"
        )
        assert exc.code == ErrorCode.INVALID_REQUEST
        assert exc.status_code == 422
        assert exc.details["field"] == "email"

    def test_attack_error(self):
        """测试攻击错误"""
        exc = AttackError(
            message="Attack failed",
            attack_type="prompt_injection"
        )
        assert exc.code == ErrorCode.ATTACK_FAILED
        assert exc.status_code == 500
        assert exc.details["attack_type"] == "prompt_injection"

    def test_defense_error(self):
        """测试防御错误"""
        exc = DefenseError(
            message="Defense failed",
            defense_type="input_filter"
        )
        assert exc.code == ErrorCode.DEFENSE_FAILED
        assert exc.status_code == 500

    def test_gateway_error(self):
        """测试网关错误"""
        exc = GatewayError(
            message="Connection refused",
            endpoint="openai-gpt4"
        )
        assert exc.code == ErrorCode.GATEWAY_ERROR
        assert exc.status_code == 502

    def test_rate_limit_error(self):
        """测试速率限制错误"""
        exc = RateLimitError(retry_after=60, limit=100)
        assert exc.code == ErrorCode.RATE_LIMIT_EXCEEDED
        assert exc.status_code == 429
        assert exc.details["retry_after"] == 60
        assert exc.details["limit"] == 100


class TestExceptionHandling:
    """异常处理测试"""

    def test_exception_handler(self):
        """测试异常处理器"""
        app = FastAPI()

        @app.exception_handler(MoxException)
        async def mox_exception_handler(request, exc):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_dict(),
            )

        @app.get("/test-error")
        async def test_error():
            raise AuthenticationError("Test auth error")

        client = TestClient(app)
        response = client.get("/test-error")
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "UNAUTHORIZED"
        assert data["message"] == "Test auth error"