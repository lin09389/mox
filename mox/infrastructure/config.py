"""配置管理模块"""

import os
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

    # ============ 本地模型配置 ============
    LOCAL_MODEL_PATH: Optional[str] = None
    LORA_ADAPTER_PATH: Optional[str] = None
    LOAD_IN_4BIT: bool = False
    LOAD_IN_8BIT: bool = False
    DEVICE_MAP: str = "auto"
    TORCH_DTYPE: str = "bfloat16"

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
    TRUSTED_PROXIES: List[str] = Field(default_factory=list)

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

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v

    @field_validator('ALLOWED_IPS', mode='before')
    @classmethod
    def parse_allowed_ips(cls, v):
        if isinstance(v, str):
            return [ip.strip() for ip in v.split(',') if ip.strip()]
        return v

    @field_validator('TRUSTED_PROXIES', mode='before')
    @classmethod
    def parse_trusted_proxies(cls, v):
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(',') if p.strip()]
            if parts == ["*"]:
                return ["*"]
            return parts
        return v

    @field_validator('CORS_ALLOW_METHODS', mode='before')
    @classmethod
    def parse_cors_methods(cls, v):
        if isinstance(v, str):
            return [method.strip() for method in v.split(',') if method.strip()]
        return v

    @field_validator('CORS_ALLOW_HEADERS', mode='before')
    @classmethod
    def parse_cors_headers(cls, v):
        if isinstance(v, str):
            return [header.strip() for header in v.split(',') if header.strip()]
        return v

    @field_validator('DEFAULT_USERS', mode='before')
    @classmethod
    def parse_default_users(cls, v):
        if isinstance(v, str):
            return [user.strip() for user in v.split('|') if user.strip()]
        return v

    @model_validator(mode='after')
    def validate_production_security(self):
        if self.REQUIRE_AUTH and not os.environ.get('MOX_SECRET_KEY'):
            raise ValueError(
                "MOX_SECRET_KEY must be explicitly set when REQUIRE_AUTH=True. "
                "Auto-generated keys are not allowed in production."
            )
        return self


    def get_database_config(self) -> dict:
        """获取数据库配置"""
        return {
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_timeout": self.DB_POOL_TIMEOUT,
            "pool_recycle": self.DB_POOL_RECYCLE,
            "pool_pre_ping": True,
        }


# 全局配置实例
settings = Settings()