"""日志配置模块"""

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import settings


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """配置日志系统

    Args:
        level: 日志级别，默认从配置读取
        log_file: 日志文件路径，可选
        format_string: 日志格式字符串

    Returns:
        配置好的 logger 实例
    """
    logger = logging.getLogger("mox")
    logger.setLevel(getattr(logging, level or settings.LOG_LEVEL or "INFO"))

    if logger.handlers:
        return logger

    default_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    formatter = logging.Formatter(format_string or default_format)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """获取子模块 logger

    Args:
        name: logger 名称，通常用 __name__

    Returns:
        Logger 实例
    """
    return logging.getLogger(f"mox.{name}")


def set_log_level(level: str) -> None:
    """动态设置日志级别

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.getLogger("mox").setLevel(getattr(logging, level.upper()))
