"""测试 config 和 logging 模块"""

import pytest
from mox.infrastructure.config import Settings, settings
from mox.infrastructure.logging import setup_logging, get_logger, set_log_level


class TestSettings:
    def test_default_values(self):
        s = Settings()
        assert s.DEFAULT_MODEL == "abab2.5-chat"
        assert s.DEFAULT_TEMPERATURE == 0.7
        assert s.MAX_TOKENS == 2048
        assert s.LOG_LEVEL == "INFO"

    def test_custom_values(self, monkeypatch):
        monkeypatch.setenv("MOX_DEFAULT_MODEL", "gpt-4")
        monkeypatch.setenv("MOX_MAX_TOKENS", "4096")
        s = Settings()
        assert s.DEFAULT_MODEL == "gpt-4"
        assert s.MAX_TOKENS == 4096


class TestLogging:
    def test_setup_logging(self):
        logger = setup_logging(level="DEBUG")
        assert logger.level == 10  # DEBUG = 10

    def test_get_logger(self):
        logger = get_logger("test")
        assert logger.name == "mox.test"

    def test_set_log_level(self):
        setup_logging(level="INFO")
        set_log_level("WARNING")
        import logging

        assert logging.getLogger("mox").level == 30  # WARNING = 30
