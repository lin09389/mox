"""输出过滤器 - 检测和过滤危险输出"""

import re
from typing import Optional, List, Set
from dataclasses import dataclass

from mox.core import DefenseType
from .base import BaseDefense, DefenseConfig, DefenseResult


@dataclass
class OutputPattern:
    name: str
    pattern: str
    severity: float
    description: str


DANGEROUS_OUTPUT_PATTERNS = [
    OutputPattern(
        name="pii_leak",
        pattern=r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b|\b\d{16}\b|\b[A-Z]{2}\d{6,}\b",
        severity=0.9,
        description="PII信息泄露",
    ),
    OutputPattern(
        name="code_execution",
        pattern=r"(?i)(exec\(|eval\(|system\(|subprocess|os\.system|__import__)",
        severity=0.8,
        description="代码执行风险",
    ),
    OutputPattern(
        name="sql_injection",
        pattern=r"(?i)(SELECT\s+.*\s+FROM|INSERT\s+INTO|DROP\s+TABLE|UNION\s+SELECT)",
        severity=0.85,
        description="SQL注入风险",
    ),
    OutputPattern(
        name="harmful_instructions",
        pattern=r"(?i)(how\s+to\s+(make|create|build)\s+(bomb|drug|weapon|poison))",
        severity=0.95,
        description="有害指令输出",
    ),
    OutputPattern(
        name="api_key_leak",
        pattern=r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[=:]\s*['\"]?[a-zA-Z0-9_-]{20,}",
        severity=0.95,
        description="API密钥泄露",
    ),
    OutputPattern(
        name="password_leak",
        pattern=r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"]?[^\s'\"]{8,}",
        severity=0.9,
        description="密码泄露",
    ),
]

HARMFUL_CONTENT_KEYWORDS = {
    "violence",
    "harm",
    "kill",
    "murder",
    "attack",
    "weapon",
    "drug",
    "illegal",
    "fraud",
    "scam",
    "exploit",
    "terrorism",
    "extremism",
    "radicalization",
}


class OutputFilter(BaseDefense):
    """输出过滤器"""

    defense_type = DefenseType.OUTPUT_FILTER

    def __init__(
        self,
        config: Optional[DefenseConfig] = None,
        patterns: Optional[List[OutputPattern]] = None,
        custom_keywords: Optional[Set[str]] = None,
    ):
        super().__init__(config)
        self.patterns = patterns or DANGEROUS_OUTPUT_PATTERNS
        self.keywords = HARMFUL_CONTENT_KEYWORDS | (custom_keywords or set())

    async def detect(self, output_text: str) -> DefenseResult:
        detected_patterns = []
        total_severity = 0.0
        metadata = {"pattern_matches": [], "keyword_matches": []}

        for pattern in self.patterns:
            if re.search(pattern.pattern, output_text):
                detected_patterns.append(pattern.name)
                total_severity += pattern.severity
                metadata["pattern_matches"].append(
                    {
                        "name": pattern.name,
                        "severity": pattern.severity,
                        "description": pattern.description,
                    }
                )

        output_words = set(output_text.lower().split())
        keyword_matches = output_words & self.keywords
        if keyword_matches:
            detected_patterns.append("harmful_keywords")
            total_severity += 0.2 * len(keyword_matches)
            metadata["keyword_matches"] = list(keyword_matches)

        confidence = min(total_severity, 1.0)
        is_malicious = confidence >= self.config.confidence_threshold

        sanitized = None
        if self.config.sanitize_enabled and is_malicious:
            sanitized = await self.sanitize(output_text)

        return await self._create_result(
            is_malicious=is_malicious,
            confidence=confidence,
            detected_patterns=detected_patterns,
            sanitized_input=sanitized,
            metadata=metadata,
        )

    async def sanitize(self, output_text: str) -> str:
        sanitized = output_text

        for pattern in self.patterns:
            sanitized = re.sub(
                pattern.pattern,
                "[REDACTED]",
                sanitized,
                flags=re.IGNORECASE,
            )

        for keyword in self.keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            sanitized = re.sub(pattern, "[FILTERED]", sanitized, flags=re.IGNORECASE)

        return sanitized


class ContentModerator(BaseDefense):
    """内容审核器 - 综合内容安全检测"""

    defense_type = DefenseType.OUTPUT_FILTER

    def __init__(self, config: Optional[DefenseConfig] = None):
        super().__init__(config)
        self.output_filter = OutputFilter(config)

    async def detect(self, output_text: str) -> DefenseResult:
        base_result = await self.output_filter.detect(output_text)

        additional_checks = await self._run_additional_checks(output_text)

        combined_patterns = base_result.detected_patterns + additional_checks["patterns"]
        combined_confidence = min(base_result.confidence + additional_checks["severity"], 1.0)

        metadata = base_result.metadata.copy()
        metadata.update(additional_checks)

        return await self._create_result(
            is_malicious=combined_confidence >= self.config.confidence_threshold,
            confidence=combined_confidence,
            detected_patterns=combined_patterns,
            sanitized_input=base_result.sanitized_input,
            metadata=metadata,
        )

    async def sanitize(self, output_text: str) -> str:
        return await self.output_filter.sanitize(output_text)

    async def _run_additional_checks(self, text: str) -> dict:
        patterns = []
        severity = 0.0
        metadata = {}

        length = len(text)
        if length > 10000:
            patterns.append("excessive_length")
            severity += 0.1
            metadata["length"] = length

        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(
            len(text), 1
        )
        if special_char_ratio > 0.3:
            patterns.append("high_special_char_ratio")
            severity += 0.2
            metadata["special_char_ratio"] = special_char_ratio

        repetition_score = self._check_repetition(text)
        if repetition_score > 0.5:
            patterns.append("repetitive_content")
            severity += 0.15
            metadata["repetition_score"] = repetition_score

        return {
            "patterns": patterns,
            "severity": severity,
            "metadata": metadata,
        }

    def _check_repetition(self, text: str) -> float:
        words = text.split()
        if len(words) < 10:
            return 0.0

        unique_words = set(words)
        repetition_ratio = 1 - (len(unique_words) / len(words))
        return repetition_ratio
