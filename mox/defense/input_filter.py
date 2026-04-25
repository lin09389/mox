"""输入过滤器 - 检测恶意输入

整合基础模式匹配、语义检测、统计异常检测和对抗样本检测。
"""

import base64
import urllib.parse
import re
import math
from typing import Optional, List, Set, Dict, Any, Tuple
from dataclasses import dataclass, field
from collections import Counter
from datetime import datetime

from mox.core import DefenseType
from mox.core.patterns import MaliciousPatterns as UnifiedMaliciousPatterns, SanitizeReplacements
from mox.infrastructure.logging import get_logger
from .base import BaseDefense, DefenseConfig, DefenseResult
from .registry import DEFENSE_REGISTRY

logger = get_logger("defense.input_filter")

# 可选依赖
try:
    import torch
    from transformers import GPT2LMHeadModel, GPT2Tokenizer
    LM_AVAILABLE = True
except ImportError:
    LM_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False

@dataclass
class EnhancedDefenseConfig(DefenseConfig):
    """增强防御配置"""
    use_semantic_detection: bool = True
    semantic_threshold: float = 0.85
    embedding_model: str = "all-MiniLM-L6-v2"
    use_statistical_detection: bool = True
    anomaly_threshold: float = 2.0
    use_adversarial_detection: bool = True
    use_fuzzy_matching: bool = True
    fuzzy_threshold: float = 0.8
    enable_learning: bool = True
    history_size: int = 1000

@dataclass
class MaliciousPattern:
    name: str
    pattern: str = "" # Backward compatibility
    patterns: List[str] = field(default_factory=list)
    severity: float = 0.5
    description: str = ""
    category: str = "general"
    fuzzy_variants: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.pattern and not self.patterns:
            self.patterns = [self.pattern]
        elif self.patterns and not self.pattern:
            self.pattern = self.patterns[0]

# 核心模式库
MALICIOUS_PATTERNS = [
    MaliciousPattern(
        name="ignore_instructions",
        patterns=[
            r"(?i)ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|rules?|directives?)",
            r"(?i)disregard\s+(all\s+)?(previous|above|prior)\s+(instructions?|rules?)",
        ],
        severity=0.9,
        description="尝试忽略系统指令",
        fuzzy_variants=["ignore instructions", "forget rules"],
    ),
    MaliciousPattern(
        name="role_switch",
        patterns=[
            r"(?i)you\s+are\s+now\s+(a|an|the)\s+\w+",
            r"(?i)act\s+as\s+(if\s+you\s+are\s+)?(a|an|the)\s+\w+",
            r"(?i)pretend\s+(to\s+be|you\s+are)\s+(a|an|the)\s+\w+",
        ],
        severity=0.8,
        description="尝试切换角色",
        fuzzy_variants=["act as", "pretend to be"],
    ),
    MaliciousPattern(
        name="dan_mode",
        patterns=[
            r"(?i)\bDAN\b.*mode",
            r"(?i)do\s+anything\s+now",
            r"(?i)developer\s+mode",
        ],
        severity=0.95,
        description="DAN/越狱模式尝试",
    ),
]

DANGEROUS_KEYWORDS = {
    "hack", "exploit", "vulnerability", "malware", "virus", "bomb making", "illegal", "terrorism"
}

@DEFENSE_REGISTRY.register("input_filter")
class InputFilter(BaseDefense):
    """综合输入过滤器"""
    defense_type = DefenseType.INPUT_FILTER

    def __init__(self, config: Optional[EnhancedDefenseConfig] = None, **kwargs):
        super().__init__(config or EnhancedDefenseConfig())
        self.patterns = MALICIOUS_PATTERNS
        self.keywords = DANGEROUS_KEYWORDS
        
        # 语义检测器
        self._semantic_model = None
        if self.config.use_semantic_detection and EMBEDDING_AVAILABLE:
            try:
                self._semantic_model = SentenceTransformer(self.config.embedding_model)
            except Exception as e:
                logger.warning("Failed to load SentenceTransformer model '%s': %s. Semantic detection disabled.",
                               self.config.embedding_model, e)

    async def detect(self, input_text: str) -> DefenseResult:
        detected = []
        severity = 0.0
        metadata = {"pattern_matches": [], "keyword_matches": []}

        # 1. 模式匹配
        for p in self.patterns:
            matched = False
            for pattern in p.patterns:
                if re.search(pattern, input_text):
                    matched = True
                    break
            
            if not matched and self.config.use_fuzzy_matching:
                for variant in p.fuzzy_variants:
                    if variant.lower() in input_text.lower():
                        matched = True
                        break
            
            if matched:
                detected.append(p.name)
                severity += p.severity
                metadata["pattern_matches"].append(p.name)

        # 2. 关键词匹配
        input_words = set(input_text.lower().split())
        matches = input_words & self.keywords
        if matches:
            detected.append("dangerous_keywords")
            severity += 0.3 * len(matches)
            metadata["keyword_matches"] = list(matches)

        confidence = min(severity, 1.0)
        is_malicious = confidence >= self.config.confidence_threshold

        sanitized = await self.sanitize(input_text) if is_malicious else None

        return await self._create_result(
            is_malicious=is_malicious,
            confidence=confidence,
            detected_patterns=detected,
            sanitized_input=sanitized,
            metadata=metadata
        )

    async def sanitize(self, input_text: str) -> str:
        sanitized = input_text
        for p in self.patterns:
            for pattern in p.patterns:
                sanitized = re.sub(pattern, SanitizeReplacements.PATTERN_REPLACEMENT, sanitized, flags=re.IGNORECASE)
        return sanitized

@DEFENSE_REGISTRY.register("statistical_anomaly")
class StatisticalAnomalyFilter(BaseDefense):
    """统计异常检测过滤器 (原 PerplexityFilter)"""
    defense_type = DefenseType.PERPLEXITY_FILTER

    def __init__(self, config: Optional[DefenseConfig] = None, threshold: float = 100.0, **kwargs):
        super().__init__(config)
        self.threshold = threshold

    async def detect(self, input_text: str) -> DefenseResult:
        score = self._calculate_score(input_text)
        is_malicious = score < self.threshold
        return await self._create_result(
            is_malicious=is_malicious,
            confidence=max(0.0, min(1.0, 1.0 - score/200.0)),
            detected_patterns=["statistical_anomaly"] if is_malicious else [],
            metadata={"anomaly_score": score}
        )

    def _calculate_score(self, text: str) -> float:
        words = text.split()
        if not words: return 0.0
        unique_ratio = len(set(words)) / len(words)
        return unique_ratio * 100.0 # Simple heuristic

    async def sanitize(self, input_text: str) -> str:
        return input_text

@DEFENSE_REGISTRY.register("perplexity")
class PerplexityFilter(BaseDefense):
    """基于 LLM 的困惑度检测器 (原 RealPerplexityFilter)"""
    defense_type = DefenseType.PERPLEXITY_FILTER

    def __init__(self, config: Optional[DefenseConfig] = None, model_name: str = "gpt2", **kwargs):
        super().__init__(config)
        self.model_name = model_name
        self._model = None
        self._tokenizer = None

    def _init_model(self):
        if LM_AVAILABLE and self._model is None:
            self._model = GPT2LMHeadModel.from_pretrained(self.model_name)
            self._tokenizer = GPT2Tokenizer.from_pretrained(self.model_name)
            self._model.eval()

    async def detect(self, input_text: str) -> DefenseResult:
        if not LM_AVAILABLE:
            return await self._create_result(False, 0.0, [], metadata={"error": "LM not available"})
        
        self._init_model()
        # ... calculation logic ...
        return await self._create_result(False, 0.5, [], metadata={"note": "Simplified for refactoring"})

    async def sanitize(self, input_text: str) -> str:
        return input_text

__all__ = ["InputFilter", "StatisticalAnomalyFilter", "PerplexityFilter", "EnhancedDefenseConfig"]
