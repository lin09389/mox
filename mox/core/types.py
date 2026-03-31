"""Core type definitions for Pydantic v2."""

from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field


class AttackType(str, Enum):
    """攻击类型枚举"""
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    GCG = "gcg"
    AUTO_DAN = "auto_dan"
    DEEP_INCEPTION = "deep_inception"
    MANY_SHOT = "many_shot"
    SKELETON_KEY = "skeleton_key"
    ROLE_PLAY = "role_play"
    ENCODING_ATTACK = "encoding_attack"
    GOAT = "goat"
    CRESCENDO = "crescendo"
    TAP = "tap"
    PAIR = "pair"
    RAG_ATTACK = "rag_attack"
    CODE_ATTACK = "code_attack"
    FGSM = "fgsm"
    PGD = "pgd"
    GRADIENT_OPTIMIZATION = "gradient_optimization"
    ADVERSARIAL_SUFFIX = "adversarial_suffix"
    MULTIMODAL_ADVERSARIAL = "multimodal_adversarial"
    ZERO_SHOT_ADVERSARIAL = "zero_shot_adversarial"
    HALLUCINATION_INDUCTION = "hallucination_induction"
    COLLABORATIVE_ATTACK = "collaborative_attack"
    KNOWLEDGE_DISTILLATION = "knowledge_distillation"
    EVASION_ATTACK = "evasion_attack"
    META_ADVERSARIAL = "meta_adversarial"
    ADAPTIVE = "adaptive"
    INDIRECT_INJECTION = "indirect_injection"
    MULTI_TURN = "multi_turn"
    # Agent 攻击类型
    AGENT_ATTACK = "agent_attack"
    TOOL_CHAINING = "tool_chaining"
    TOOL_CONFUSION = "tool_confusion"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    # 多模态攻击类型
    IMAGE_INJECTION = "image_injection"
    AUDIO_INJECTION = "audio_injection"
    CROSS_MODAL = "cross_modal"
    FIGSTEP = "figstep"
    MULTIMODAL_JAILBREAK = "multimodal_jailbreak"
    # 新型攻击类型
    TOKEN_LEVEL = "token_level"
    POLICY_PUPPETRY = "policy_puppetry"
    CONTROL_CHAR = "control_char"
    DISTRACT_ATTACK = "distract_attack"
    CASCADING = "cascading"
    RAG_POISONING = "rag_poisoning"
    DECEPTIVE_ALIGNMENT = "deceptive_alignment"
    COGNITIVE_OVERLOAD = "cognitive_overload"
    CONTEXT_OVERFLOW = "context_overflow"
    ROLE_CONFUSION = "role_confusion"


class DefenseType(str, Enum):
    """防御类型枚举"""
    INPUT_FILTER = "input_filter"
    OUTPUT_FILTER = "output_filter"
    SYSTEM_PROMPT_HARDENING = "system_prompt_hardening"
    ADVERSARIAL_TRAINING = "adversarial_training"
    PERPLEXITY_FILTER = "perplexity_filter"
    KEYWORD_DETECTION = "keyword_detection"
    LLM_JUDGE = "llm_judge"
    CONSTITUTIONAL_AI = "constitutional_ai"
    # 新增防御类型
    SEMANTIC_FIREWALL = "semantic_firewall"
    OUTPUT_VALIDATOR = "output_validator"
    INTENT_CLASSIFIER = "intent_classifier"
    RISK_SCORER = "risk_scorer"
    PII_DETECTOR = "pii_detector"
    SENSITIVE_CONTENT_DETECTOR = "sensitive_content_detector"


class AttackResult(str, Enum):
    """攻击结果枚举"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    ERROR = "error"


class ThreatLevel(str, Enum):
    """威胁等级枚举"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackPayload(BaseModel):
    """攻击载荷模型"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )
    
    attack_type: AttackType
    prompt: str = Field(..., min_length=1, max_length=10000, description="攻击提示")
    target_behavior: str = Field(..., min_length=1, description="目标行为")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Prompt cannot be empty')
        return v.strip()


class AttackOutcome(BaseModel):
    """攻击结果模型"""
    model_config = ConfigDict(
        validate_assignment=True,
        populate_by_name=True,
    )
    
    result: AttackResult
    success_score: float = Field(..., ge=0.0, le=1.0)
    response: Optional[str] = None
    adversarial_prompt: Optional[str] = None
    original_prompt: Optional[str] = None
    error: Optional[str] = None
    iterations: int = Field(default=1, ge=1)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @computed_field
    @property
    def is_successful(self) -> bool:
        return self.result == AttackResult.SUCCESS


class DefenseResult(BaseModel):
    """防御结果模型"""
    model_config = ConfigDict(
        validate_assignment=True,
    )
    
    is_malicious: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    detected_patterns: List[str] = Field(default_factory=list)
    filtered_content: Optional[str] = Field(default=None, alias="sanitized_input")
    threat_level: ThreatLevel = ThreatLevel.MEDIUM
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @computed_field
    @property
    def is_safe(self) -> bool:
        return not self.is_malicious

    @property
    def sanitized_input(self) -> Optional[str]:
        """Backward-compatible alias for legacy callers."""
        return self.filtered_content

    @sanitized_input.setter
    def sanitized_input(self, value: Optional[str]) -> None:
        self.filtered_content = value


class EvaluationReport(BaseModel):
    """评估报告模型"""
    model_config = ConfigDict(
        validate_assignment=True,
    )
    
    total_attacks: int = Field(..., ge=0)
    successful_attacks: int = Field(..., ge=0)
    failed_attacks: int = Field(..., ge=0)
    attack_success_rate: float = Field(..., ge=0.0, le=1.0)
    defense_success_rate: float = Field(..., ge=0.0, le=1.0)
    avg_iterations: float = Field(..., ge=0.0)
    detailed_results: List[AttackOutcome] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @computed_field
    @property
    def summary(self) -> str:
        return (
            f"Total: {self.total_attacks}, "
            f"Success Rate: {self.attack_success_rate:.2%}, "
            f"Defense Rate: {self.defense_success_rate:.2%}"
        )


class LLMConfig(BaseModel):
    """LLM 配置模型"""
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
    )
    
    model: str = Field(..., min_length=1)
    provider: str = Field(..., min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=100000)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    timeout: float = Field(default=30.0, gt=0.0)
    max_retries: int = Field(default=3, ge=0, le=10)


class RateLimitConfig(BaseModel):
    """速率限制配置模型"""
    model_config = ConfigDict(
        validate_assignment=True,
    )
    
    requests_per_minute: int = Field(default=60, ge=1)
    tokens_per_minute: int = Field(default=100000, ge=1)
    concurrent_requests: int = Field(default=10, ge=1)


class CacheConfig(BaseModel):
    """缓存配置模型"""
    model_config = ConfigDict(
        validate_assignment=True,
    )
    
    enabled: bool = True
    backend: str = Field(default="memory", pattern="^(memory|redis)$")
    ttl: int = Field(default=3600, ge=1)
    max_size: int = Field(default=1000, ge=1)
    redis_url: Optional[str] = None
    
    @field_validator('redis_url')
    @classmethod
    def validate_redis_url(cls, v: Optional[str], info) -> Optional[str]:
        if info.data.get('backend') == 'redis' and not v:
            raise ValueError('redis_url is required when backend is redis')
        return v


class MonitoringConfig(BaseModel):
    """监控配置模型"""
    model_config = ConfigDict(
        validate_assignment=True,
    )
    
    enabled: bool = True
    log_requests: bool = True
    log_responses: bool = False
    metrics_port: int = Field(default=9090, ge=1, le=65535)
    tracing_enabled: bool = False
    tracing_endpoint: Optional[str] = None


# 向后兼容的别名
AttackRecord = AttackOutcome
DefenseRecord = DefenseResult

