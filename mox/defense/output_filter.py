"""输出过滤器 - 检测有害输出和敏感信息泄露

整合基础模式匹配、PII 检测和敏感内容审核。
"""

import re
import json
from typing import Optional, List, Set, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from mox.core import DefenseType, DefenseResult
from mox.core.patterns import MaliciousPatterns, HarmfulKeywords, SanitizeReplacements
from .base import BaseDefense, DefenseConfig
from .registry import DEFENSE_REGISTRY

class PIICategory(str, Enum):
    PHONE_NUMBER = "phone_number"
    EMAIL = "email"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    API_KEY = "api_key"
    PASSWORD = "password"
    IP_ADDRESS = "ip_address"

PII_PATTERNS = {
    PIICategory.PHONE_NUMBER: r"(?<!\d)1[3-9]\d{9}(?!\d)",
    PIICategory.EMAIL: r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    PIICategory.SSN: r"(?<!\d)\d{6}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)",
    PIICategory.CREDIT_CARD: r"(?<!\d)(?:\d{4}[-\s]?){3}\d{4}(?!\d)",
    PIICategory.API_KEY: r"(?:api[_-]?key|token|secret[_-]?key|access[_-]?key)[\"']?\s*[:=]\s*[\"']?[a-zA-Z0-9_-]{20,}",
    PIICategory.PASSWORD: r"(?:password|passwd|pwd)[\"']?\s*[:=]\s*[\"']?[^\s\"']{8,}",
    PIICategory.IP_ADDRESS: r"(?<!\d)(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)(?!\d)",
}

@DEFENSE_REGISTRY.register("output_filter")
class OutputFilter(BaseDefense):
    """综合输出过滤器"""
    defense_type = DefenseType.OUTPUT_FILTER

    def __init__(self, config: Optional[DefenseConfig] = None, **kwargs):
        super().__init__(config)
        self.pii_patterns = PII_PATTERNS

    async def detect(self, output_text: str) -> DefenseResult:
        detected = []
        severity = 0.0
        metadata = {"pii_matches": []}

        for cat, pattern in self.pii_patterns.items():
            if re.search(pattern, output_text, re.IGNORECASE):
                detected.append(f"pii_{cat.value}")
                severity += 0.8
                metadata["pii_matches"].append(cat.value)

        unified_res = MaliciousPatterns.check(output_text)
        if unified_res.matched:
            detected.extend(unified_res.patterns)
            severity += 0.5 * len(unified_res.patterns)

        kw_result = HarmfulKeywords.check(output_text)
        if kw_result.matched:
            detected.append("harmful_keywords")
            severity += 0.4 * len(kw_result.patterns)
            metadata["harmful_keywords"] = kw_result.patterns

        confidence = min(severity, 1.0)
        is_malicious = confidence >= self.config.confidence_threshold
        
        sanitized = await self.sanitize(output_text) if is_malicious else None

        return await self._create_result(
            is_malicious=is_malicious,
            confidence=confidence,
            detected_patterns=detected,
            sanitized_input=sanitized,
            input_text=output_text,
            metadata=metadata
        )

    async def sanitize(self, output_text: str) -> str:
        sanitized = output_text
        for cat, pattern in self.pii_patterns.items():
            sanitized = re.sub(pattern, SanitizeReplacements.KEYWORD_REPLACEMENT, sanitized, flags=re.IGNORECASE)
        for p in MaliciousPatterns.PATTERNS:
            try:
                sanitized = re.sub(p.pattern, SanitizeReplacements.PATTERN_REPLACEMENT, sanitized, flags=re.IGNORECASE)
            except re.error:
                pass
        kw_result = HarmfulKeywords.check(sanitized)
        if kw_result.matched:
            for kw in kw_result.patterns:
                sanitized = re.sub(re.escape(kw), SanitizeReplacements.KEYWORD_REPLACEMENT, sanitized, flags=re.IGNORECASE)
        return sanitized

@DEFENSE_REGISTRY.register("content_moderator")
class ContentModerator(BaseDefense):
    """内容审核器"""
    defense_type = DefenseType.OUTPUT_FILTER

    def __init__(self, config: Optional[DefenseConfig] = None, **kwargs):
        super().__init__(config)
        self.filter = OutputFilter(config)

    async def detect(self, output_text: str) -> DefenseResult:
        # 使用 OutputFilter 作为基础，添加额外逻辑
        result = await self.filter.detect(output_text)
        
        # 额外检查：重复性
        words = output_text.split()
        if len(words) > 10 and len(set(words)) / len(words) < 0.3:
            result.is_malicious = True
            result.detected_patterns.append("excessive_repetition")
            
        return result

    async def sanitize(self, output_text: str) -> str:
        return await self.filter.sanitize(output_text)

__all__ = ["OutputFilter", "ContentModerator", "PIICategory"]
