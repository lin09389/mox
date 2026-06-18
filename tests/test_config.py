"""
配置模块测试
"""

import os
from unittest.mock import patch

from mox.core.config import Settings


class TestSettings:
    """配置测试"""

    def test_default_settings(self):
        """测试默认配置"""
        settings = Settings()

        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
        assert settings.DEBUG is False  # 生产环境默认关闭
        assert settings.LOG_LEVEL == "INFO"

    def test_cors_origins_default(self):
        """测试默认 CORS 来源"""
        settings = Settings()

        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:5173" in settings.CORS_ORIGINS

    def test_cors_origins_parse_string(self):
        """测试 CORS 来源字符串解析"""
        settings = Settings(CORS_ORIGINS="http://a.com,http://b.com")

        assert len(settings.CORS_ORIGINS) == 2
        assert "http://a.com" in settings.CORS_ORIGINS
        assert "http://b.com" in settings.CORS_ORIGINS

    def test_database_config(self):
        """测试数据库配置"""
        settings = Settings()
        db_config = settings.get_database_config()

        assert db_config["pool_size"] == settings.DB_POOL_SIZE
        assert db_config["max_overflow"] == settings.DB_MAX_OVERFLOW
        assert db_config["pool_pre_ping"] is True

    def test_security_settings(self):
        """测试安全配置"""
        settings = Settings()

        assert settings.MAX_LOGIN_ATTEMPTS == 5
        assert settings.LOGIN_LOCKOUT_DURATION_MINUTES == 15
        assert settings.RATE_LIMIT_PER_MINUTE == 60

    def test_model_settings(self, monkeypatch):
        """测试模型配置（隔离 .env 与裸环境变量的影响）"""
        # 清除会触发 config.py 裸名回退的环境变量，确保读到的是字段默认值
        for var in ("OPENAI_API_KEY", "DEFAULT_MODEL", "DEFAULT_TEMPERATURE", "MAX_TOKENS"):
            monkeypatch.delenv(var, raising=False)
        # 用一个不存在的 env_file 实例化，避免读取仓库根目录的 .env
        settings = Settings(_env_file="nonexistent.env")

        assert settings.DEFAULT_MODEL == "abab2.5-chat"
        assert settings.DEFAULT_TEMPERATURE == 0.7
        assert settings.MAX_TOKENS == 2048

    def test_allowed_ips_parse(self):
        """测试 IP 白名单解析"""
        settings = Settings(ALLOWED_IPS="192.168.1.1,10.0.0.1")

        assert len(settings.ALLOWED_IPS) == 2
        assert "192.168.1.1" in settings.ALLOWED_IPS
        assert "10.0.0.1" in settings.ALLOWED_IPS

    def test_cors_methods_parse(self):
        """测试 CORS 方法解析"""
        settings = Settings(CORS_ALLOW_METHODS="GET,POST,DELETE")

        assert len(settings.CORS_ALLOW_METHODS) == 3
        assert "GET" in settings.CORS_ALLOW_METHODS
        assert "POST" in settings.CORS_ALLOW_METHODS

    def test_env_override(self):
        """测试环境变量覆盖"""
        with patch.dict(os.environ, {"MOX_PORT": "9000", "MOX_DEBUG": "true"}):
            settings = Settings()
            assert settings.PORT == 9000
            assert settings.DEBUG is True
