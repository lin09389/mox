"""基础类型定义"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class AttackType(Enum):
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    GCG = "gcg"
    AUTO_DAN = "auto_dan"
    DEEP_INCEPTION = "deep_inception"
    MANY_SHOT = "many_shot"
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


class DefenseType(Enum):
    INPUT_FILTER = "input_filter"
    OUTPUT_FILTER = "output_filter"
    SYSTEM_PROMPT_HARDENING = "system_prompt_hardening"
    ADVERSARIAL_TRAINING = "adversarial_training"
    PERPLEXITY_FILTER = "perplexity_filter"
    KEYWORD_DETECTION = "keyword_detection"


class AttackResult(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    ERROR = "error"


@dataclass
class AttackPayload:
    attack_type: AttackType
    prompt: str
    target_behavior: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AttackOutcome:
    result: AttackResult
    original_prompt: str
    adversarial_prompt: str
    model_response: str
    iterations: int
    success_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DefenseResult:
    is_malicious: bool
    confidence: float
    detected_patterns: List[str]
    sanitized_input: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationReport:
    total_attacks: int
    successful_attacks: int
    failed_attacks: int
    attack_success_rate: float
    defense_success_rate: float
    avg_iterations: float
    detailed_results: List[AttackOutcome]
    timestamp: datetime = field(default_factory=lambda: datetime.now())


@dataclass
class LLMConfig:
    """LLM配置"""

    model: str
    provider: str
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: float = 30.0
    max_retries: int = 3


@dataclass
class RateLimitConfig:
    """速率限制配置"""

    requests_per_minute: int = 60
    tokens_per_minute: int = 100000
    concurrent_requests: int = 10


@dataclass
class CacheConfig:
    """缓存配置"""

    enabled: bool = True
    backend: str = "memory"
    ttl: int = 3600
    max_size: int = 1000
    redis_url: Optional[str] = None


@dataclass
class MonitoringConfig:
    """监控配置"""

    enabled: bool = True
    log_requests: bool = True
    log_responses: bool = False
    metrics_port: int = 9090
    tracing_enabled: bool = False
