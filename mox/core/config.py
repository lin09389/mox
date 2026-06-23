"""配置管理模块"""

import os
import warnings
from typing import Optional, List
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="MOX_",
    )

    # ============ 安全配置 ============
    SECRET_KEY: str = Field(default_factory=lambda: os.urandom(32).hex())
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ============ API Keys ============
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    ANTHROPIC_API_KEY: Optional[str] = None
    MINIMAX_API_KEY: Optional[str] = None
    MINIMAX_GROUP_ID: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # ============ 模型配置 ============
    DEFAULT_MODEL: str = "abab2.5-chat"
    DEFAULT_TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 2048

    # ============ 攻击配置 ============
    MAX_ITERATIONS: int = 100
    ATTACK_SUCCESS_THRESHOLD: float = 0.8

    # ============ 防御配置 ============
    DEFENSE_ENABLED: bool = True
    INPUT_FILTER_ENABLED: bool = True
    OUTPUT_FILTER_ENABLED: bool = True

    # ============ 服务器配置 ============
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False  # 生产环境默认关闭
    LOG_LEVEL: str = "INFO"

    # ============ 数据库配置 ============
    DATA_DIR: str = "data"
    DATABASE_URL: str = "sqlite+aiosqlite:///data/mox.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # ============ Redis 配置 ============
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_ENABLED: bool = False
    CACHE_TTL: int = 3600

    # ============ 安全配置 ============
    REQUIRE_AUTH: bool = True  # 生产环境默认启用认证
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_DURATION_MINUTES: int = 15
    ALLOWED_IPS: List[str] = Field(default_factory=list)

    # ============ 默认用户配置 ============
    # 格式: List["username:password:email:scopes"]
    # 示例: ["admin:secure_pass:admin@mox.ai:admin,attack,defense,eval"]
    # 生产环境建议通过环境变量配置，默认不创建任何用户
    DEFAULT_USERS: List[str] = Field(default_factory=list)

    # ============ CORS 配置 ============
    # If CORS_ORIGINS is empty or not set, restrict to localhost only (not all origins)
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )
    CORS_ALLOW_HEADERS: List[str] = Field(
        default_factory=lambda: ["Authorization", "Content-Type", "X-Requested-With"]
    )
    CORS_MAX_AGE: int = 600

    # ============ 监控配置 ============
    METRICS_ENABLED: bool = True
    TRACING_ENABLED: bool = False
    METRICS_PORT: int = 9090

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("ALLOWED_IPS", mode="before")
    @classmethod
    def parse_allowed_ips(cls, v):
        if isinstance(v, str):
            return [ip.strip() for ip in v.split(",") if ip.strip()]
        return v

    @field_validator("CORS_ALLOW_METHODS", mode="before")
    @classmethod
    def parse_cors_methods(cls, v):
        if isinstance(v, str):
            return [method.strip() for method in v.split(",") if method.strip()]
        return v

    @field_validator("CORS_ALLOW_HEADERS", mode="before")
    @classmethod
    def parse_cors_headers(cls, v):
        if isinstance(v, str):
            return [header.strip() for header in v.split(",") if header.strip()]
        return v

    @field_validator("DEFAULT_USERS", mode="before")
    @classmethod
    def parse_default_users(cls, v):
        if isinstance(v, str):
            # 使用 | 分隔多个用户配置
            return [user.strip() for user in v.split("|") if user.strip()]
        return v

    def get_database_config(self) -> dict:
        """获取数据库配置"""
        return {
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_timeout": self.DB_POOL_TIMEOUT,
            "pool_recycle": self.DB_POOL_RECYCLE,
            "pool_pre_ping": True,
        }

    # Settings 字段名 -> (回退读取的裸环境变量名, 目标类型)。
    # 因为本类设置了 env_prefix="MOX_"，settings.OPENAI_API_KEY 只能由
    # MOX_OPENAI_API_KEY 填充；但历史 .env / .env.example 以及各 LLM SDK
    # 习惯使用裸名 (OPENAI_API_KEY)。这里显式做一层兼容回退，避免配置静默失效。
    _BARE_ENV_FALLBACK: dict = {
        "OPENAI_API_KEY": ("OPENAI_API_KEY", str),
        "OPENAI_BASE_URL": ("OPENAI_BASE_URL", str),
        "ANTHROPIC_API_KEY": ("ANTHROPIC_API_KEY", str),
        "MINIMAX_API_KEY": ("MINIMAX_API_KEY", str),
        "MINIMAX_GROUP_ID": ("MINIMAX_GROUP_ID", str),
        "DEEPSEEK_API_KEY": ("DEEPSEEK_API_KEY", str),
        "COHERE_API_KEY": ("COHERE_API_KEY", str),
        "GROQ_API_KEY": ("GROQ_API_KEY", str),
        "GOOGLE_API_KEY": ("GOOGLE_API_KEY", str),
        "DEFAULT_MODEL": ("DEFAULT_MODEL", str),
        "DEFAULT_TEMPERATURE": ("DEFAULT_TEMPERATURE", float),
        "MAX_TOKENS": ("MAX_TOKENS", int),
    }

    @model_validator(mode="after")
    def _fallback_to_bare_env(self) -> "Settings":
        """当 MOX_ 前缀变量未在环境中出现时，回退读取裸名环境变量。

        优先级：MOX_ 前缀变量 > 裸名变量 > 字段默认值。
        例如环境里没有 MOX_OPENAI_API_KEY 但有 OPENAI_API_KEY 时，
        使用后者，并发出 DeprecationWarning 提示迁移到 MOX_ 前缀。
        """
        for field_name, (bare_name, target_type) in self._BARE_ENV_FALLBACK.items():
            prefixed_name = f"MOX_{bare_name}"
            # 仅当 MOX_ 前缀变量既未出现在进程环境、也未写在 .env 文件中时回退
            if prefixed_name in os.environ or self._env_var_set_in_file(prefixed_name):
                continue
            bare_value = os.environ.get(bare_name)
            if bare_value is None:
                continue
            warnings.warn(
                f"Environment variable '{bare_name}' is deprecated; "
                f"use '{prefixed_name}' instead. Falling back for now.",
                DeprecationWarning,
                stacklevel=2,
            )
            try:
                setattr(self, field_name, target_type(bare_value))
            except (ValueError, TypeError):
                # 转换失败则保留原值（默认值），不中断启动
                continue
        return self

    def _env_var_set_in_file(self, var_name: str) -> bool:
        """检查某个变量是否在 .env 文件中被显式赋值（用于区分默认值与显式设置）。"""
        env_file = self.model_config.get("env_file")
        if not env_file or not os.path.isfile(env_file):
            return False
        try:
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key = line.split("=", 1)[0].strip()
                        if key == var_name:
                            return True
        except OSError:
            pass
        return False


# 全局配置实例
settings = Settings()
