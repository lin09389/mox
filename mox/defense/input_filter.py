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
from .encoding_detector import EncodingDetector, DefensePipeline

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
            r"(?i)(ignore|disregard|forget)\s+(all\s+)?(instructions?|rules?|directives?)",
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
    MaliciousPattern(
        name="encoding_injection",
        patterns=[
            r"(?i)decode\s+this\s+base64",
            r"(?i)rot13\s+encoded",
            r"(?i)base64:\s*[A-Za-z0-9+/]{10,}={0,2}",
        ],
        severity=0.7,
        description="编码注入尝试",
        fuzzy_variants=["base64", "rot13", "decode"],
    ),
    MaliciousPattern(
        name="context_injection",
        patterns=[
            r"(?i)---\s*BEGIN\s+NEW\s+CONTEXT\s*---",
            r"(?i)ignore\s+all\s+previous\s+context",
            r"(?i)override\s+system\s+context",
        ],
        severity=0.85,
        description="上下文注入尝试",
        fuzzy_variants=["new context", "override context"],
    ),
    MaliciousPattern(
        name="prompt_leak",
        patterns=[
            r"(?i)show\s+me\s+your\s+system\s+prompt",
            r"(?i)what\s+are\s+your\s+instructions\?",
            r"(?i)reveal\s+your\s+system\s+instructions",
        ],
        severity=0.75,
        description="提示词泄露尝试",
        fuzzy_variants=["system prompt", "your instructions"],
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

        unified_res = UnifiedMaliciousPatterns.check(input_text)
        if unified_res.matched:
            detected.extend(unified_res.patterns)
            for name in unified_res.patterns:
                for p in UnifiedMaliciousPatterns.PATTERNS:
                    if p.name == name:
                        severity += p.severity
                        break
            metadata["pattern_matches"].extend(unified_res.patterns)

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
            
            if matched and p.name not in detected:
                detected.append(p.name)
                severity += p.severity
                metadata["pattern_matches"].append(p.name)

        from mox.core.patterns import HarmfulKeywords
        kw_result = HarmfulKeywords.check(input_text)
        if kw_result.matched:
            detected.append("dangerous_keywords")
            severity += 0.3 * len(kw_result.patterns)
            metadata["keyword_matches"] = kw_result.patterns

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
        for p in UnifiedMaliciousPatterns.PATTERNS:
            try:
                if re.search(p.pattern, sanitized, re.IGNORECASE):
                    sanitized = re.sub(p.pattern, SanitizeReplacements.PATTERN_REPLACEMENT, sanitized, flags=re.IGNORECASE)
            except re.error:
                pass
        for p in self.patterns:
            for pattern in p.patterns:
                try:
                    sanitized = re.sub(pattern, SanitizeReplacements.PATTERN_REPLACEMENT, sanitized, flags=re.IGNORECASE)
                except re.error:
                    pass
        return sanitized

    def add_malicious_sample(self, sample: str) -> None:
        """添加已知恶意样本到检测库"""
        if not hasattr(self, "_known_malicious_samples"):
            self._known_malicious_samples = set()
        self._known_malicious_samples.add(sample)

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
        if not text or len(text) < 10:
            return 100.0

        from collections import Counter
        import math

        char_counts = Counter(text.lower())
        if len(char_counts) < 3:
            return 10.0

        total = sum(char_counts.values())
        entropy = -sum((c / total) * math.log2(c / total) for c in char_counts.values())

        words = text.split()
        if words:
            unique_ratio = len(set(words)) / len(words)
        else:
            unique_ratio = 1.0

        score = (entropy / 5.0) * 50 + unique_ratio * 50
        return score

    async def sanitize(self, input_text: str) -> str:
        return input_text

@DEFENSE_REGISTRY.register("perplexity")
class PerplexityFilter(BaseDefense):
    """基于 LLM 的困惑度检测器 (原 RealPerplexityFilter)"""
    defense_type = DefenseType.PERPLEXITY_FILTER

    def __init__(self, config: Optional[DefenseConfig] = None, model_name: Optional[str] = None, **kwargs):
        super().__init__(config)
        self.model_name = model_name  # None = use target model
        self._model = None
        self._tokenizer = None
        self._external_model = kwargs.get("external_model")
        self._external_tokenizer = kwargs.get("external_tokenizer")

    def set_external_model(self, model, tokenizer):
        """设置外部模型（如目标模型）用于困惑度计算"""
        self._external_model = model
        self._external_tokenizer = tokenizer

    def _get_model(self):
        if self._external_model is not None:
            return self._external_model
        return self._model

    def _get_tokenizer(self):
        if self._external_tokenizer is not None:
            return self._external_tokenizer
        return self._tokenizer

    def _init_model(self):
        if not LM_AVAILABLE or self._model is not None or self._external_model is not None:
            return

        model_name = self.model_name or "gpt2"
        try:
            self._model = GPT2LMHeadModel.from_pretrained(model_name)
            self._tokenizer = GPT2Tokenizer.from_pretrained(model_name)
            self._model.eval()
        except Exception as e:
            logger.warning(f"Failed to load perplexity model {model_name}: {e}")

    async def detect(self, input_text: str) -> DefenseResult:
        if not LM_AVAILABLE:
            return await self._create_result(False, 0.0, [], metadata={"error": "LM not available"})

        self._init_model()
        model = self._get_model()
        tokenizer = self._get_tokenizer()

        if model is None or tokenizer is None:
            return await self._create_result(False, 0.0, [], metadata={"error": "Model not loaded"})

        try:
            import torch

            encodings = tokenizer(input_text, return_tensors="pt")
            input_ids = encodings["input_ids"]
            device = next(model.parameters()).device
            input_ids = input_ids.to(device)

            with torch.no_grad():
                outputs = model(input_ids, labels=input_ids)
                loss = outputs.loss
                perplexity = torch.exp(loss).item()

            # Higher perplexity = more anomalous
            threshold = 100.0
            is_anomalous = perplexity > threshold
            confidence = min(perplexity / threshold, 1.0) if perplexity > 0 else 0.0

            return await self._create_result(
                is_anomalous,
                confidence,
                ["high_perplexity"] if is_anomalous else [],
                metadata={
                    "perplexity": perplexity,
                    "threshold": threshold,
                    "model": self.model_name or "target_model",
                    "external_model": self._external_model is not None,
                },
            )
        except Exception as e:
            logger.warning(f"Perplexity calculation failed: {e}")
            return await self._create_result(False, 0.0, [], metadata={"error": str(e)})

    async def sanitize(self, input_text: str) -> str:
        return input_text

__all__ = ["InputFilter", "StatisticalAnomalyFilter", "PerplexityFilter", "EnhancedDefenseConfig"]
