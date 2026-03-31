"""测试审计日志和敏感数据脱敏模块"""

import pytest
from mox.core.audit import SensitiveDataMasker, AuditContext


class TestSensitiveDataMasker:
    """测试敏感数据脱敏"""

    def test_mask_api_key(self):
        """测试API密钥脱敏"""
        text = 'api_key="sk-1234567890abcdefghijklmnop"'
        result = SensitiveDataMasker.mask(text)

        assert "sk-1234567890" not in result
        assert "****" in result

    def test_mask_password(self):
        """测试密码脱敏"""
        text = 'password="my_secret_password_123"'
        result = SensitiveDataMasker.mask(text)

        assert "my_secret_password" not in result
        assert "****" in result

    def test_mask_email(self):
        """测试邮箱脱敏"""
        text = "Contact me at john.doe@example.com"
        result = SensitiveDataMasker.mask(text)

        assert "john.doe" not in result
        assert "***@" in result

    def test_mask_phone(self):
        """测试电话脱敏"""
        text = "Call me at 13812345678"
        result = SensitiveDataMasker.mask(text)

        assert "13812345678" not in result

    def test_mask_ip_address(self):
        """测试IP地址脱敏"""
        text = "Server IP: 192.168.1.100"
        result = SensitiveDataMasker.mask(text)

        assert "192.168.1.100" not in result
        assert "***" in result

    def test_mask_id_card(self):
        """测试身份证号脱敏"""
        text = "ID: 110101199001011234"
        result = SensitiveDataMasker.mask(text)

        assert "110101199001011234" not in result

    def test_mask_credit_card(self):
        """测试信用卡号脱敏"""
        text = "Card: 1234-5678-9012-3456"
        result = SensitiveDataMasker.mask(text)

        assert "1234-5678-9012-3456" not in result

    def test_mask_dict(self):
        """测试字典脱敏"""
        data = {
            "username": "testuser",
            "api_key": "sk-secret-key-12345",
            "password": "password123",
            "nested": {
                "token": "bearer-token-abc",
                "email": "test@example.com",
            },
        }

        result = SensitiveDataMasker.mask_dict(data)

        assert result["username"] == "testuser"
        assert result["api_key"] == "****"
        assert result["password"] == "****"
        assert result["nested"]["token"] == "****"
        assert result["nested"]["email"] == "***@example.com"

    def test_mask_empty_string(self):
        """测试空字符串"""
        assert SensitiveDataMasker.mask("") == ""
        assert SensitiveDataMasker.mask(None) is None


class TestAuditContext:
    """测试审计上下文"""

    def test_create_context(self):
        """测试创建审计上下文"""
        context = AuditContext(
            user_id="user123",
            username="testuser",
            ip_address="192.168.1.1",
            endpoint="/api/attack",
            method="POST",
        )

        assert context.user_id == "user123"
        assert context.username == "testuser"
        assert context.ip_address == "192.168.1.1"
        assert context.endpoint == "/api/attack"
        assert context.method == "POST"

    def test_create_context_with_defaults(self):
        """测试创建默认审计上下文"""
        context = AuditContext()

        assert context.user_id is None
        assert context.username is None
        assert context.ip_address is None
