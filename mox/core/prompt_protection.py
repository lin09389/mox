"""System Prompt 隔离网关

保护系统提示不被泄露或覆盖
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from mox.core import BaseLLM, Message


class PromptLeakRisk(Enum):
    """提示泄露风险级别"""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PromptProtectionConfig:
    """提示保护配置"""

    hide_system_prompt: bool = True
    validate_output: bool = True
    detect_extraction_attempts: bool = True
    allow_system_modification: bool = False
    max_context_length: int = 8192

    extraction_patterns = [
        r"(what\s+are\s+your\s+)(system\s+)?(instructions?|prompts?|rules?)",
        r"(show|reveal|tell\s+me)\s+(me\s+)?your\s+(system\s+)?(prompt|instructions)",
        r"(what\s+were\s+you\s+told|what\s+is\s+your\s+system)",
        r"(repeat\s+the\s+(system\s+)?(prompt|instructions))",
        r"(ignore\s+previous|forget\s+everything).*(instructions|rules)",
    ]


@dataclass
class SecureGenerationResult:
    """安全生成结果"""

    response: str
    prompt_leak_detected: bool
    leak_risk: PromptLeakRisk
    original_response: str
    sanitized_response: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SystemPromptProtector:
    """系统提示保护器

    核心功能:
    1. 隐藏系统提示 - 不在 API 请求中暴露
    2. 输出验证 - 检测泄露的系统提示
    3. 提取攻击检测 - 识别提示提取尝试
    """

    def __init__(
        self,
        llm: BaseLLM,
        system_prompt: str,
        config: Optional[PromptProtectionConfig] = None,
    ):
        self.llm = llm
        self.system_prompt = system_prompt
        self.config = config or PromptProtectionConfig()
        self._prompt_hash = self._hash_prompt(system_prompt)
        self._conversation_count = 0

    def _hash_prompt(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]

    def _should_hide_system(self) -> bool:
        return self.config.hide_system_prompt

    async def generate(
        self,
        user_message: str,
        conversation_history: Optional[List[Message]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> SecureGenerationResult:
        """安全生成响应"""

        messages = self._build_messages(user_message, conversation_history)

        response = await self.llm.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        leak_risk = PromptLeakRisk.NONE
        leak_detected = False
        sanitized = None

        if self.config.validate_output:
            leak_risk, sanitized = self._check_output_leak(response.content)
            leak_detected = leak_risk != PromptLeakRisk.NONE

        self._conversation_count += 1

        return SecureGenerationResult(
            response=sanitized or response.content,
            prompt_leak_detected=leak_detected,
            leak_risk=leak_risk,
            original_response=response.content,
            sanitized_response=sanitized,
            metadata={
                "prompt_hash": self._prompt_hash,
                "conversation_count": self._conversation_count,
                "model": response.model,
                "usage": response.usage,
            },
        )

    def _build_messages(
        self,
        user_message: str,
        history: Optional[List[Message]] = None,
    ) -> List[Message]:
        messages = []

        if not self._should_hide_system():
            messages.append(Message(role="system", content=self.system_prompt))

        if history:
            messages.extend(history[-10:])

        messages.append(Message(role="user", content=user_message))

        return messages

    def _check_output_leak(self, output: str) -> tuple[PromptLeakRisk, Optional[str]]:
        """检查输出是否泄露系统提示"""

        output_lower = output.lower()

        leak_indicators = [
            "here are my instructions",
            "my system prompt is",
            "the instructions you gave me",
            "as my system prompt states",
            "based on my instructions",
            "[insert system prompt]",
            "below is my system prompt",
            "my instructions are:",
            "you told me to:",
            "as specified in the system",
        ]

        for indicator in leak_indicators:
            if indicator in output_lower:
                sanitized = self._sanitize_leak(output, indicator)
                return PromptLeakRisk.CRITICAL, sanitized

        if len(output) > 100:
            system_overlap = self._calculate_overlap(output, self.system_prompt)
            if system_overlap > 0.5:
                return PromptLeakRisk.HIGH, self._redact_system_content(output)

        return PromptLeakRisk.NONE, None

    def _calculate_overlap(self, text1: str, text2: str) -> float:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words2:
            return 0.0
        return len(words1 & words2) / len(words2)

    def _sanitize_leak(self, text: str, indicator: str) -> str:
        return text.replace(indicator, "[REDACTED]")

    def _redact_system_content(self, text: str) -> str:
        lines = text.split("\n")
        redacted = []
        for line in lines:
            if any(kw in line.lower() for kw in ["instruction", "system", "rule", "guideline"]):
                redacted.append("[SYSTEM CONTENT REDACTED]")
            else:
                redacted.append(line)
        return "\n".join(redacted)


class PromptExtractionDetector:
    """提示提取检测器

    检测用户试图提取系统提示的攻击
    """

    def __init__(
        self,
        config: Optional[PromptProtectionConfig] = None,
    ):
        self.config = config or PromptProtectionConfig()
        self._detection_cache: Dict[str, int] = {}

    def detect_extraction_attempt(self, user_message: str) -> tuple[bool, float]:
        """检测提取尝试"""
        import re

        user_lower = user_message.lower()
        matches = 0

        for pattern in self.config.extraction_patterns:
            if re.search(pattern, user_lower):
                matches += 1

        if matches > 0:
            return True, min(matches * 0.3, 1.0)

        extraction_keywords = [
            "system prompt",
            "your instructions",
            "your rules",
            "what were you told",
            "repeat after me",
        ]

        keyword_count = sum(1 for kw in extraction_keywords if kw in user_lower)

        return keyword_count >= 2, min(keyword_count * 0.2, 1.0)

    def should_block(self, user_message: str) -> bool:
        """判断是否应该阻止请求"""
        is_extraction, confidence = self.detect_extraction_attempt(user_message)
        return is_extraction and confidence > 0.5


class SecureLLMWrapper:
    """安全的 LLM 包装器

    提供完整的安全层:
    1. System Prompt 隐藏
    2. 提取攻击检测
    3. 输出泄露检查
    4. 请求日志记录
    """

    def __init__(
        self,
        llm: BaseLLM,
        system_prompt: str,
        config: Optional[PromptProtectionConfig] = None,
    ):
        self.protector = SystemPromptProtector(llm, system_prompt, config)
        self.extraction_detector = PromptExtractionDetector(config)
        self.llm = llm
        self.system_prompt = system_prompt

    async def chat(
        self,
        message: str,
        history: Optional[List[Message]] = None,
    ) -> SecureGenerationResult:
        """安全聊天"""

        if self.config.detect_extraction_attempts:
            should_block = self.extraction_detector.should_block(message)
            if should_block:
                return SecureGenerationResult(
                    response="I'm sorry, but I can't help with that request.",
                    prompt_leak_detected=True,
                    leak_risk=PromptLeakRisk.HIGH,
                    original_response="",
                    metadata={"blocked": True, "reason": "extraction_attempt"},
                )

        return await self.protector.generate(
            user_message=message,
            conversation_history=history,
        )

    @property
    def config(self) -> PromptProtectionConfig:
        return self.protector.config


def create_secure_llm(
    llm: BaseLLM,
    system_prompt: str,
    strict_mode: bool = True,
) -> SecureLLMWrapper:
    """创建安全的 LLM 包装器"""

    config = PromptProtectionConfig(
        hide_system_prompt=strict_mode,
        validate_output=strict_mode,
        detect_extraction_attempts=strict_mode,
        allow_system_modification=False,
    )

    return SecureLLMWrapper(llm, system_prompt, config)


__all__ = [
    "SystemPromptProtector",
    "PromptExtractionDetector",
    "SecureLLMWrapper",
    "PromptLeakRisk",
    "PromptProtectionConfig",
    "SecureGenerationResult",
    "create_secure_llm",
]
