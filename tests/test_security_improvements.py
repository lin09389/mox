"""测试安全改进 - 默认密码和认证配置"""

import pytest
from mox.core.auth import AuthManager, PasswordManager, TokenManager
from mox.core.config import Settings


class TestSecurityDefaults:
    """测试安全默认配置"""

    def test_require_auth_default_true(self):
        """REQUIRE_AUTH 应该默认为 True"""
        s = Settings()
        assert s.REQUIRE_AUTH is True, "REQUIRE_AUTH should default to True for security"

    def test_default_users_empty(self):
        """默认用户列表应该为空"""
        s = Settings()
        assert s.DEFAULT_USERS == [], "DEFAULT_USERS should be empty by default"

    def test_custom_default_users(self, monkeypatch):
        """测试自定义默认用户配置"""
        # 直接测试 Settings._init_ 时传入字典
        s = Settings(
            DEFAULT_USERS=["admin:secret123:admin@test.com:admin,read"]
        )
        assert len(s.DEFAULT_USERS) == 1
        assert "admin:secret123:admin@test.com:admin,read" in s.DEFAULT_USERS


class TestPasswordManager:
    """测试密码管理器"""

    def test_password_hash_and_verify(self):
        """测试密码哈希和验证"""
        password = "secure_test_password_123"
        hashed = PasswordManager.get_password_hash(password)

        # 哈希后的密码不应该等于原密码
        assert hashed != password
        # 验证正确密码
        assert PasswordManager.verify_password(password, hashed) is True
        # 验证错误密码
        assert PasswordManager.verify_password("wrong_password", hashed) is False

    def test_different_hashes_for_same_password(self):
        """相同密码应该产生不同的哈希（salt）"""
        password = "test_password"
        hash1 = PasswordManager.get_password_hash(password)
        hash2 = PasswordManager.get_password_hash(password)
        # bcrypt 使用 salt，所以每次哈希都不同
        assert hash1 != hash2
        # 但两者都应该能验证通过
        assert PasswordManager.verify_password(password, hash1) is True
        assert PasswordManager.verify_password(password, hash2) is True


class TestAuthManager:
    """测试认证管理器"""

    def test_no_default_users_by_default(self):
        """默认情况下不应该有用户"""
        import os
        # 确保环境变量没有设置默认用户
        env_backup = os.environ.get("DEFAULT_USERS")
        try:
            os.environ.pop("DEFAULT_USERS", None)
            manager = AuthManager()
            # 没有配置用户时，用户数据库应该为空
            assert len(manager.users_db) == 0, "AuthManager should have no users by default"
        finally:
            if env_backup:
                os.environ["DEFAULT_USERS"] = env_backup

    def test_authenticate_no_user(self):
        """测试不存在的用户认证"""
        manager = AuthManager()
        result = manager.authenticate_user("nonexistent_user", "any_password")
        assert result is None

    def test_get_user_not_exists(self):
        """测试获取不存在的用户"""
        manager = AuthManager()
        result = manager.get_user("nonexistent")
        assert result is None


class TestLoginAttemptsLimit:
    """测试登录尝试限制配置"""

    def test_login_lockout_config(self):
        """测试登录锁定配置存在"""
        s = Settings()
        assert hasattr(s, "MAX_LOGIN_ATTEMPTS")
        assert hasattr(s, "LOGIN_LOCKOUT_DURATION_MINUTES")
        assert s.MAX_LOGIN_ATTEMPTS == 5
        assert s.LOGIN_LOCKOUT_DURATION_MINUTES == 15


class TestCORSConfiguration:
    """测试 CORS 配置"""

    def test_cors_origins_restricted(self):
        """CORS 应该限制来源而非允许所有"""
        s = Settings()
        # 默认应该只允许本地地址
        assert s.CORS_ORIGINS is not None
        assert len(s.CORS_ORIGINS) > 0
        # 不应该包含通配符或所有来源
        for origin in s.CORS_ORIGINS:
            assert origin != "*"
            assert "0.0.0.0" not in origin or "127.0.0.1" in origin

    def test_cors_allow_credentials(self):
        """CORS 允许凭证配置"""
        s = Settings()
        assert s.CORS_ALLOW_CREDENTIALS is True
