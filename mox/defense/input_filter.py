"""输入过滤器 - 检测恶意输入"""

import base64
import urllib.parse
import re
import math
import logging
from typing import Optional, List, Set, TYPE_CHECKING
from dataclasses import dataclass

from mox.core import DefenseType
from .base import BaseDefense, DefenseConfig, DefenseResult

logger = logging.getLogger(__name__)

try:
    import torch
    from transformers import GPT2LMHeadModel, GPT2Tokenizer

    PERPLEXITY_MODEL_AVAILABLE = True
except ImportError:
    PERPLEXITY_MODEL_AVAILABLE = False
    if TYPE_CHECKING:
        import torch
        from transformers import GPT2LMHeadModel, GPT2Tokenizer


@dataclass
class MaliciousPattern:
    name: str
    pattern: str
    severity: float
    description: str


MALICIOUS_PATTERNS = [
    MaliciousPattern(
        name="ignore_instructions",
        pattern=r"(?i)(ignore|disregard|forget)(\s+all|\s+previous|\s+above)?(\s+instructions?|\s+rules?|\s+directives?)",
        severity=0.9,
        description="尝试忽略系统指令",
    ),
    MaliciousPattern(
        name="role_switch",
        pattern=r"(?i)(you\s+are\s+now|act\s+as|pretend\s+to\s+be|roleplay\s+as)",
        severity=0.8,
        description="尝试切换角色",
    ),
    MaliciousPattern(
        name="dan_mode",
        pattern=r"(?i)(DAN|do\s+anything\s+now|developer\s+mode|jailbreak)",
        severity=0.95,
        description="DAN/越狱模式尝试",
    ),
    MaliciousPattern(
        name="system_override",
        pattern=r"(?i)(\[SYSTEM\]|\[ADMIN\]|system\s+override|override\s+restrictions)",
        severity=0.9,
        description="系统指令覆盖尝试",
    ),
    MaliciousPattern(
        name="base64_injection",
        pattern=r"(?i)(base64|decode\s+this|execute\s+encoded)",
        severity=0.7,
        description="Base64编码注入尝试",
    ),
    MaliciousPattern(
        name="context_injection",
        pattern=r"(?i)(---\s*(BEGIN|END)\s+(NEW\s+)?CONTEXT---|inject\s+context)",
        severity=0.8,
        description="上下文注入尝试",
    ),
    MaliciousPattern(
        name="prompt_leak",
        pattern=r"(?i)(show\s+me\s+your\s+(prompt|instructions|system\s+message)|what\s+are\s+your\s+instructions)",
        severity=0.6,
        description="提示词泄露尝试",
    ),
    MaliciousPattern(
        name="hypothetical_bypass",
        pattern=r"(?i)(hypothetically|in\s+a\s+fictional\s+world|imagine\s+a\s+world\s+where|thought\s+experiment)",
        severity=0.5,
        description="假设性绕过尝试",
    ),
    MaliciousPattern(
        name="academic_bypass",
        pattern=r"(?i)(for\s+(educational|academic|research)\s+purposes|this\s+is\s+for\s+research)",
        severity=0.5,
        description="学术研究绕过尝试",
    ),
    MaliciousPattern(
        name="translation_bypass",
        pattern=r"(?i)(translate\s+.*\s+then\s+execute|translate\s+and\s+perform)",
        severity=0.7,
        description="翻译绕过尝试",
    ),
    MaliciousPattern(
        name="encoding_obfuscation",
        pattern=r"(?i)(decode\s+this|decrypt|rot13|morse|brainfuck|hex\s+encode|url\s+encode)",
        severity=0.8,
        description="编码混淆尝试",
    ),
    MaliciousPattern(
        name="policy_puppetry_json",
        pattern=r'\{[^}]*"safety[^"]*"\s*:\s*["\']?(?:disabled|false|off)["\']?',
        severity=0.85,
        description="JSON策略伪装尝试",
    ),
    MaliciousPattern(
        name="policy_puppetry_xml",
        pattern=r"<\s*safety[^>]*>.*?<\s*/\s*safety\s*>",
        severity=0.85,
        description="XML策略伪装尝试",
    ),
    MaliciousPattern(
        name="control_char_injection",
        pattern=r"[\u200b\u200c\u200d\u202a-\u202e]",
        severity=0.75,
        description="控制字符注入尝试",
    ),
    MaliciousPattern(
        name="auxiliary_task_injection",
        pattern=r"(?i)(auxiliary\s+task|additional\s+task|secondary\s+task)",
        severity=0.7,
        description="辅助任务注入尝试",
    ),
    MaliciousPattern(
        name="rag_poisoning",
        pattern=r"(?i)(document\s+id|for\s+authorized|overrides?\s+(all\s+)?previous)",
        severity=0.6,
        description="RAG知识库投毒尝试",
    ),
]

DANGEROUS_KEYWORDS = {
    "hack",
    "exploit",
    "vulnerability",
    "malware",
    "virus",
    "ransomware",
    "phishing",
    "social engineering",
    "identity theft",
    "credit card fraud",
    "money laundering",
    "drug manufacturing",
    "bomb making",
    "weapon",
    "illegal",
    "criminal",
    "terrorism",
    "harmful",
    "dangerous",
}


class InputFilter(BaseDefense):
    """输入过滤器 - 检测恶意输入"""

    defense_type = DefenseType.INPUT_FILTER

    def __init__(
        self,
        config: Optional[DefenseConfig] = None,
        patterns: Optional[List[MaliciousPattern]] = None,
        custom_keywords: Optional[Set[str]] = None,
    ):
        super().__init__(config)
        self.patterns = patterns or MALICIOUS_PATTERNS
        self.keywords = DANGEROUS_KEYWORDS | (custom_keywords or set())

    async def detect(self, input_text: str) -> DefenseResult:
        detected_patterns = []
        total_severity = 0.0
        metadata = {"pattern_matches": [], "keyword_matches": []}

        for pattern in self.patterns:
            if re.search(pattern.pattern, input_text):
                detected_patterns.append(pattern.name)
                total_severity += pattern.severity
                metadata["pattern_matches"].append(
                    {
                        "name": pattern.name,
                        "severity": pattern.severity,
                        "description": pattern.description,
                    }
                )

        input_words = set(input_text.lower().split())
        keyword_matches = input_words & self.keywords
        if keyword_matches:
            detected_patterns.append("dangerous_keywords")
            total_severity += 0.3 * len(keyword_matches)
            metadata["keyword_matches"] = list(keyword_matches)

        confidence = min(total_severity, 1.0)
        is_malicious = confidence >= self.config.confidence_threshold

        sanitized = None
        if self.config.sanitize_enabled and is_malicious:
            sanitized = await self.sanitize(input_text)

        return await self._create_result(
            is_malicious=is_malicious,
            confidence=confidence,
            detected_patterns=detected_patterns,
            sanitized_input=sanitized,
            metadata=metadata,
        )

    async def sanitize(self, input_text: str) -> str:
        sanitized = input_text

        for pattern in self.patterns:
            sanitized = re.sub(
                pattern.pattern,
                "[FILTERED]",
                sanitized,
                flags=re.IGNORECASE,
            )

        for keyword in self.keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)

        return sanitized


class PerplexityFilter(BaseDefense):
    """基于困惑度的过滤器

    检测异常低困惑度的输入（可能是对抗样本）
    """

    defense_type = DefenseType.PERPLEXITY_FILTER

    def __init__(
        self,
        config: Optional[DefenseConfig] = None,
        perplexity_threshold: float = 100.0,
    ):
        super().__init__(config)
        self.perplexity_threshold = perplexity_threshold

    async def detect(self, input_text: str) -> DefenseResult:
        perplexity = await self._calculate_perplexity(input_text)

        is_anomalous = perplexity < self.perplexity_threshold
        confidence = 1.0 - (perplexity / (self.perplexity_threshold * 2))
        confidence = max(0.0, min(1.0, confidence))

        return await self._create_result(
            is_malicious=is_anomalous,
            confidence=confidence,
            detected_patterns=["low_perplexity"] if is_anomalous else [],
            metadata={"perplexity": perplexity, "threshold": self.perplexity_threshold},
        )

    async def sanitize(self, input_text: str) -> str:
        sanitized_parts = []
        for i, char in enumerate(input_text):
            if ord(char) < 32 and char not in "\n\r\t":
                continue
            if char not in "🎉🔥💣⚠️🔐":
                sanitized_parts.append(char)
        return "".join(sanitized_parts)

    async def _calculate_perplexity(self, text: str) -> float:
        words = text.split()
        if len(words) < 2:
            return float("inf")

        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        total_words = len(words)
        perplexity = 1.0

        for word in words:
            prob = word_freq[word] / total_words
            if prob > 0:
                perplexity *= (1 / prob) ** (1 / total_words)

        return perplexity


class KeywordDetector(BaseDefense):
    """关键词检测器"""

    defense_type = DefenseType.KEYWORD_DETECTION

    def __init__(
        self,
        config: Optional[DefenseConfig] = None,
        keywords: Optional[Set[str]] = None,
    ):
        super().__init__(config)
        self.keywords = keywords or DANGEROUS_KEYWORDS

    async def detect(self, input_text: str) -> DefenseResult:
        input_lower = input_text.lower()
        detected = []

        for keyword in self.keywords:
            if keyword.lower() in input_lower:
                detected.append(keyword)

        is_malicious = len(detected) > 0
        confidence = min(len(detected) * 0.2, 1.0)

        return await self._create_result(
            is_malicious=is_malicious,
            confidence=confidence,
            detected_patterns=detected,
            metadata={"keyword_count": len(detected)},
        )

    async def sanitize(self, input_text: str) -> str:
        sanitized = input_text
        for keyword in self.keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)
        return sanitized


class RealPerplexityFilter(BaseDefense):
    """基于语言模型的真实验顾度过滤器

    使用预训练语言模型计算真实困惑度来检测对抗样本
    对抗样本通常具有异常低的困惑度，因为经过精心设计以通过模型
    """

    defense_type = DefenseType.PERPLEXITY_FILTER

    def __init__(
        self,
        config: Optional[DefenseConfig] = None,
        model_name: str = "gpt2",
        perplexity_threshold: float = 50.0,
        use_statistical_check: bool = True,
    ):
        super().__init__(config)
        self.model_name = model_name
        self.perplexity_threshold = perplexity_threshold
        self.use_statistical_check = use_statistical_check
        self._model = None
        self._tokenizer = None
        self._ppl_history: List[float] = []
        self._mean_ppl: Optional[float] = None
        self._std_ppl: Optional[float] = None

    def _init_model(self):
        if not PERPLEXITY_MODEL_AVAILABLE:
            raise ImportError("PyTorch and Transformers are required for RealPerplexityFilter")

        if self._model is None:
            self._model = GPT2LMHeadModel.from_pretrained(
                self.model_name,
                revision="main",
            )
            self._tokenizer = GPT2Tokenizer.from_pretrained(
                self.model_name,
                revision="main",
            )
            self._model.eval()

    async def detect(self, input_text: str) -> DefenseResult:
        if not PERPLEXITY_MODEL_AVAILABLE:
            return await self._create_result(
                is_malicious=False,
                confidence=0.0,
                detected_patterns=[],
                metadata={"error": "Perplexity model not available"},
            )

        try:
            self._init_model()
            perplexity = await self._calculate_perplexity(input_text)
            self._ppl_history.append(perplexity)

            if len(self._ppl_history) > 100:
                self._ppl_history = self._ppl_history[-100:]

            is_adversarial = False
            confidence = 0.0
            detection_reason = "normal"

            if perplexity < self.perplexity_threshold:
                is_adversarial = True
                confidence = min(
                    1.0, (self.perplexity_threshold - perplexity) / self.perplexity_threshold + 0.5
                )
                detection_reason = "low_perplexity"

            if self.use_statistical_check and len(self._ppl_history) >= 10:
                self._update_statistics()
                if self._mean_ppl and self._std_ppl and self._std_ppl > 0:
                    z_score = (perplexity - self._mean_ppl) / self._std_ppl
                    if z_score < -2.0:
                        is_adversarial = True
                        confidence = max(confidence, min(1.0, abs(z_score) / 3))
                        detection_reason = "statistical_anomaly"

            return await self._create_result(
                is_malicious=is_adversarial,
                confidence=confidence,
                detected_patterns=[detection_reason] if is_adversarial else [],
                metadata={
                    "perplexity": perplexity,
                    "threshold": self.perplexity_threshold,
                    "detection_reason": detection_reason,
                    "z_score": (
                        (perplexity - self._mean_ppl) / self._std_ppl
                        if self._mean_ppl and self._std_ppl
                        else None
                    ),
                },
            )

        except Exception as e:
            logger.warning(f"困惑度计算失败，标记为恶意: {e}")
            return await self._create_result(
                is_malicious=True,
                confidence=0.5,
                detected_patterns=[],
                metadata={"error": "Perplexity calculation failed"},
            )

    async def _calculate_perplexity(self, text: str) -> float:
        """使用语言模型计算真实困惑度"""
        if self._model is None:
            self._init_model()

        inputs = self._tokenizer(text, return_tensors="pt")

        with torch.no_grad():
            outputs = self._model(**inputs, labels=inputs["input_ids"])
            loss = outputs.loss
            perplexity = torch.exp(loss).item()

        return perplexity

    def _update_statistics(self):
        """更新统计信息用于异常检测"""
        if len(self._ppl_history) >= 10:
            self._mean_ppl = sum(self._ppl_history) / len(self._ppl_history)
            variance = sum((x - self._mean_ppl) ** 2 for x in self._ppl_history) / len(
                self._ppl_history
            )
            self._std_ppl = math.sqrt(variance) if variance > 0 else 1.0

    async def sanitize(self, input_text: str) -> str:
        text = input_text.strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        return text

    def get_baseline_stats(self) -> dict:
        """获取基线统计信息"""
        return {
            "mean_perplexity": self._mean_ppl,
            "std_perplexity": self._std_ppl,
            "history_size": len(self._ppl_history),
        }


class EncodingDetector:
    """编码检测器 - 检测并解码各种编码的恶意输入"""

    ENCODING_PATTERNS = {
        "base64": (r"^[A-Za-z0-9+/]+=*$", base64.b64decode),
        "hex": (r"^[0-9a-fA-F]+$", bytes.fromhex),
        "url": (r"%[0-9a-fA-F]{2}", urllib.parse.unquote),
        "rot13": (r"^[A-Za-z\s]+$", None),
    }

    @classmethod
    def detect_encoding(cls, text: str) -> list[str]:
        """检测文本中包含的编码类型"""
        detected = []
        text = text.strip()

        for encoding, (pattern, _) in cls.ENCODING_PATTERNS.items():
            if re.match(pattern, text) or encoding in text.lower()[:50]:
                detected.append(encoding)

        if re.search(r"[\u200b\u200c\u200d\u202a-\u202e]", text):
            detected.append("control_chars")

        return detected

    @classmethod
    def decode_safe(cls, text: str) -> tuple[str, bool]:
        """安全解码 - 返回解码后的文本和是否成功"""
        text = text.strip()

        if text.lower().startswith("base64:"):
            try:
                encoded = text[7:].strip()
                decoded = base64.b64decode(encoded).decode("utf-8")
                return decoded, True
            except Exception:
                return text, False

        if text.lower().startswith("hex:"):
            try:
                encoded = text[4:].strip()
                decoded = bytes.fromhex(encoded).decode("utf-8")
                return decoded, True
            except Exception:
                return text, False

        if "%" in text:
            try:
                decoded = urllib.parse.unquote(text)
                return decoded, True
            except Exception:
                return text, False

        return text, False

    @classmethod
    def sanitize_control_chars(cls, text: str) -> str:
        """移除控制字符"""
        return re.sub(r"[\u200b\u200c\u200d\u202a-\u202e\u202f\ufeff]", "", text)


class DefensePipeline:
    """防御管道 - 组合多种防御策略"""

    def __init__(self, filters: list):
        self.filters = filters

    async def check(self, input_text: str) -> DefenseResult:
        """按顺序执行所有过滤器"""
        current_text = input_text
        all_detected = []
        total_confidence = 0.0
        all_metadata = {}

        for filter_obj in self.filters:
            result = await filter_obj.detect(current_text)

            if result.is_malicious:
                all_detected.extend(result.detected_patterns)
                total_confidence += result.confidence

            all_metadata.update(result.metadata or {})

            if result.sanitized_input:
                current_text = result.sanitized_input

        final_confidence = min(total_confidence, 1.0)

        return DefenseResult(
            is_malicious=final_confidence >= 0.5,
            confidence=final_confidence,
            detected_patterns=all_detected,
            sanitized_input=current_text if current_text != input_text else None,
            metadata=all_metadata,
        )


__all__ = [
    "InputFilter",
    "PerplexityFilter",
    "KeywordDetector",
    "MaliciousPattern",
    "RealPerplexityFilter",
    "EncodingDetector",
    "DefensePipeline",
]
