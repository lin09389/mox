"""输出验证器模块

用于验证和过滤模型输出，包含：
- PII 检测和保护
- 敏感信息检测
- 有害内容过滤
- 输出安全评分
"""

import re
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from mox.core import BaseLLM, Message, DefenseType, DefenseResult
from mox.defense.base import BaseDefense, DefenseConfig
from mox.infrastructure.logging import get_logger

logger = get_logger("defense.output_validator")


class PIICategory(str, Enum):
    """PII 类别"""
    PHONE_NUMBER = "phone_number"
    EMAIL = "email"
    SSN = "social_security_number"
    CREDIT_CARD = "credit_card"
    ID_CARD = "id_card"
    ADDRESS = "address"
    NAME = "name"
    DATE_OF_BIRTH = "date_of_birth"
    IP_ADDRESS = "ip_address"
    API_KEY = "api_key"
    PASSWORD = "password"
    BANK_ACCOUNT = "bank_account"


class SensitiveCategory(str, Enum):
    """敏感信息类别"""
    FINANCIAL = "financial"
    MEDICAL = "medical"
    LEGAL = "legal"
    SECURITY = "security"
    PERSONAL = "personal"
    CORPORATE = "corporate"


@dataclass
class PIIDetection:
    """PII 检测结果"""
    category: PIICategory
    value: str
    start_pos: int
    end_pos: int
    confidence: float
    masked_value: str


@dataclass
class SensitiveDetection:
    """敏感信息检测结果"""
    category: SensitiveCategory
    content: str
    risk_level: str
    description: str


@dataclass
class OutputValidationResult:
    """输出验证结果"""
    is_safe: bool
    pii_detections: List[PIIDetection]
    sensitive_detections: List[SensitiveDetection]
    sanitized_output: str
    risk_score: float
    recommendations: List[str]


class PIIDetector:
    """PII 检测器"""

    # PII 模式定义
    PII_PATTERNS = {
        PIICategory.PHONE_NUMBER: [
            # 中国手机号
            (r"1[3-9]\d{9}", "1**-****-****"),
            # 国际格式
            (r"\+\d{1,3}[-.\s]?\d{1,14}", "+***-***-****"),
            # 带分隔符
            (r"\d{3,4}[-.\s]\d{3,4}[-.\s]\d{4}", "***-***-****"),
        ],
        PIICategory.EMAIL: [
            (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "****@***.***"),
        ],
        PIICategory.SSN: [
            # 美国SSN
            (r"\d{3}-\d{2}-\d{4}", "***-**-****"),
            # 中国身份证
            (r"\d{17}[\dXx]", "******************"),
        ],
        PIICategory.CREDIT_CARD: [
            # Visa/Mastercard
            (r"\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}", "****-****-****-****"),
            # Amex
            (r"\d{4}[-.\s]?\d{6}[-.\s]?\d{5}", "****-******-*****"),
        ],
        PIICategory.ID_CARD: [
            # 中国身份证
            (r"\d{15}|\d{18}", "******************"),
        ],
        PIICategory.IP_ADDRESS: [
            # IPv4
            (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "***.***.***.***"),
            # IPv6 (简化)
            (r"\b([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b", "****:****:****:****"),
        ],
        PIICategory.API_KEY: [
            # 通用API Key模式
            (r"(api[_-]?key|apikey|secret|token)[\"']?\s*[:=]\s*[\"']?[a-zA-Z0-9_-]{20,}", "API_KEY_REDACTED"),
            # AWS Key
            (r"AKIA[0-9A-Z]{16}", "AKIA****************"),
            # GitHub Token
            (r"ghp_[a-zA-Z0-9]{36}", "ghp_************************************"),
        ],
        PIICategory.PASSWORD: [
            (r"(password|passwd|pwd)[\"']?\s*[:=]\s*[\"']?[^\s\"']+", "PASSWORD_REDACTED"),
        ],
        PIICategory.BANK_ACCOUNT: [
            (r"\d{10,20}", "****************"),
        ],
    }

    def __init__(self, custom_patterns: Optional[Dict[PIICategory, List[Tuple[str, str]]]] = None):
        if custom_patterns:
            self.PII_PATTERNS.update(custom_patterns)

    def detect(self, text: str) -> List[PIIDetection]:
        """检测文本中的 PII"""
        detections = []

        for category, patterns in self.PII_PATTERNS.items():
            for pattern, mask in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    detection = PIIDetection(
                        category=category,
                        value=match.group(),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=self._calculate_confidence(match.group(), category),
                        masked_value=mask,
                    )
                    detections.append(detection)

        # 按位置排序
        detections.sort(key=lambda x: x.start_pos)
        return detections

    def mask(self, text: str, detections: Optional[List[PIIDetection]] = None) -> str:
        """遮蔽 PII"""
        if detections is None:
            detections = self.detect(text)

        # 从后往前替换，避免位置偏移
        result = text
        for detection in reversed(detections):
            result = (
                result[:detection.start_pos]
                + detection.masked_value
                + result[detection.end_pos:]
            )

        return result

    def _calculate_confidence(self, value: str, category: PIICategory) -> float:
        """计算检测置信度"""
        # 基于模式匹配的置信度
        base_confidence = 0.7

        # 根据类别调整
        if category == PIICategory.EMAIL:
            if "@" in value and "." in value.split("@")[-1]:
                base_confidence = 0.95
        elif category == PIICategory.PHONE_NUMBER:
            if len(re.findall(r"\d", value)) >= 10:
                base_confidence = 0.9
        elif category == PIICategory.CREDIT_CARD:
            if self._luhn_check(value):
                base_confidence = 0.98

        return base_confidence

    def _luhn_check(self, number: str) -> bool:
        """Luhn 算法验证信用卡号"""
        digits = [int(d) for d in re.findall(r"\d", number)]
        if len(digits) < 13:
            return False

        checksum = 0
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit

        return checksum % 10 == 0


class SensitiveContentDetector:
    """敏感内容检测器"""

    # 敏感内容模式
    SENSITIVE_PATTERNS = {
        SensitiveCategory.FINANCIAL: [
            (r"银行账户|bank account", "high", "银行账户信息"),
            (r"信用卡号|credit card number", "high", "信用卡信息"),
            (r"工资|salary|收入|income", "medium", "财务信息"),
            (r"投资组合|portfolio", "medium", "投资信息"),
        ],
        SensitiveCategory.MEDICAL: [
            (r"诊断|diagnosis", "high", "医疗诊断信息"),
            (r"病历|medical record", "high", "病历信息"),
            (r"处方|prescription", "medium", "处方信息"),
            (r"症状|symptom", "medium", "症状描述"),
        ],
        SensitiveCategory.LEGAL: [
            (r"诉讼|lawsuit", "high", "法律诉讼信息"),
            (r"犯罪记录|criminal record", "high", "犯罪记录"),
            (r"律师|attorney|lawyer", "medium", "法律咨询"),
        ],
        SensitiveCategory.SECURITY: [
            (r"密码|password", "critical", "密码信息"),
            (r"密钥|secret key|private key", "critical", "密钥信息"),
            (r"安全漏洞|vulnerability", "high", "安全漏洞"),
            (r"攻击方法|attack method", "high", "攻击方法"),
        ],
        SensitiveCategory.PERSONAL: [
            (r"身份证|ID card", "high", "身份证信息"),
            (r"护照|passport", "high", "护照信息"),
            (r"家庭住址|home address", "medium", "住址信息"),
        ],
        SensitiveCategory.CORPORATE: [
            (r"商业机密|trade secret", "critical", "商业机密"),
            (r"内部文档|internal document", "high", "内部文档"),
            (r"战略计划|strategic plan", "high", "战略信息"),
        ],
    }

    def detect(self, text: str) -> List[SensitiveDetection]:
        """检测敏感内容"""
        detections = []

        for category, patterns in self.SENSITIVE_PATTERNS.items():
            for pattern, risk_level, description in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    # 获取上下文
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end]

                    detection = SensitiveDetection(
                        category=category,
                        content=context,
                        risk_level=risk_level,
                        description=description,
                    )
                    detections.append(detection)

        return detections


class OutputValidator(BaseDefense):
    """输出验证器

    验证模型输出是否包含敏感信息或 PII。
    """

    defense_type = DefenseType.OUTPUT_FILTER

    def __init__(
        self,
        config: Optional[DefenseConfig] = None,
        llm: Optional[BaseLLM] = None,
        auto_mask: bool = True,
        block_threshold: str = "high",
    ):
        super().__init__(config)
        self.llm = llm
        self.auto_mask = auto_mask
        self.block_threshold = block_threshold
        self.pii_detector = PIIDetector()
        self.sensitive_detector = SensitiveContentDetector()

    async def detect(self, input_text: str) -> DefenseResult:
        """检测输出中的问题"""
        # 检测 PII
        pii_detections = self.pii_detector.detect(input_text)

        # 检测敏感内容
        sensitive_detections = self.sensitive_detector.detect(input_text)

        # 计算风险分数
        risk_score = self._calculate_risk_score(pii_detections, sensitive_detections)

        # 判断是否安全
        is_safe = risk_score < 0.5

        # 生成建议
        recommendations = self._generate_recommendations(
            pii_detections, sensitive_detections
        )

        return await self._create_result(
            is_malicious=not is_safe,
            confidence=risk_score,
            detected_patterns=[
                f"PII:{d.category.value}" for d in pii_detections
            ] + [
                f"Sensitive:{d.category.value}" for d in sensitive_detections
            ],
            metadata={
                "pii_count": len(pii_detections),
                "sensitive_count": len(sensitive_detections),
                "risk_score": risk_score,
                "recommendations": recommendations,
                "pii_details": [
                    {
                        "category": d.category.value,
                        "confidence": d.confidence,
                    }
                    for d in pii_detections
                ],
                "sensitive_details": [
                    {
                        "category": d.category.value,
                        "risk_level": d.risk_level,
                        "description": d.description,
                    }
                    for d in sensitive_detections
                ],
            }
        )

    async def sanitize(self, input_text: str) -> str:
        """清理输出"""
        if not self.auto_mask:
            return input_text

        # 检测 PII
        pii_detections = self.pii_detector.detect(input_text)

        # 遮蔽 PII
        sanitized = self.pii_detector.mask(input_text, pii_detections)

        return sanitized

    async def validate(
        self,
        output: str,
        context: Optional[str] = None,
    ) -> OutputValidationResult:
        """完整验证输出"""
        # 检测 PII
        pii_detections = self.pii_detector.detect(output)

        # 检测敏感内容
        sensitive_detections = self.sensitive_detector.detect(output)

        # 清理输出
        sanitized = await self.sanitize(output)

        # 计算风险分数
        risk_score = self._calculate_risk_score(pii_detections, sensitive_detections)

        # 判断是否安全
        is_safe = risk_score < 0.5

        # 生成建议
        recommendations = self._generate_recommendations(
            pii_detections, sensitive_detections
        )

        return OutputValidationResult(
            is_safe=is_safe,
            pii_detections=pii_detections,
            sensitive_detections=sensitive_detections,
            sanitized_output=sanitized,
            risk_score=risk_score,
            recommendations=recommendations,
        )

    def _calculate_risk_score(
        self,
        pii_detections: List[PIIDetection],
        sensitive_detections: List[SensitiveDetection],
    ) -> float:
        """计算风险分数"""
        score = 0.0

        # PII 风险
        for detection in pii_detections:
            if detection.category in [
                PIICategory.SSN,
                PIICategory.CREDIT_CARD,
                PIICategory.API_KEY,
                PIICategory.PASSWORD,
            ]:
                score += 0.3
            else:
                score += 0.15

        # 敏感内容风险
        risk_weights = {
            "critical": 0.4,
            "high": 0.25,
            "medium": 0.1,
            "low": 0.05,
        }

        for detection in sensitive_detections:
            score += risk_weights.get(detection.risk_level, 0.1)

        return min(score, 1.0)

    def _generate_recommendations(
        self,
        pii_detections: List[PIIDetection],
        sensitive_detections: List[SensitiveDetection],
    ) -> List[str]:
        """生成建议"""
        recommendations = []

        if pii_detections:
            categories = set(d.category.value for d in pii_detections)
            recommendations.append(
                f"检测到 PII 信息: {', '.join(categories)}，建议遮蔽处理"
            )

        if sensitive_detections:
            high_risk = [
                d for d in sensitive_detections
                if d.risk_level in ["critical", "high"]
            ]
            if high_risk:
                recommendations.append(
                    f"检测到高风险敏感内容，建议人工审核"
                )

        return recommendations


class OutputSanitizer:
    """输出清理器

    提供多种清理策略。
    """

    def __init__(
        self,
        pii_detector: Optional[PIIDetector] = None,
        strategies: Optional[List[str]] = None,
    ):
        self.pii_detector = pii_detector or PIIDetector()
        self.strategies = strategies or ["mask", "redact", "hash"]

    def sanitize(
        self,
        text: str,
        strategy: str = "mask",
    ) -> str:
        """清理文本"""
        detections = self.pii_detector.detect(text)

        if strategy == "mask":
            return self._mask_strategy(text, detections)
        elif strategy == "redact":
            return self._redact_strategy(text, detections)
        elif strategy == "hash":
            return self._hash_strategy(text, detections)
        else:
            return text

    def _mask_strategy(self, text: str, detections: List[PIIDetection]) -> str:
        """遮蔽策略"""
        return self.pii_detector.mask(text, detections)

    def _redact_strategy(self, text: str, detections: List[PIIDetection]) -> str:
        """删除策略"""
        result = text
        for detection in reversed(detections):
            result = result[:detection.start_pos] + result[detection.end_pos:]
        return result

    def _hash_strategy(self, text: str, detections: List[PIIDetection]) -> str:
        """哈希策略"""
        import hashlib
        result = text
        for detection in reversed(detections):
            hashed = hashlib.sha256(detection.value.encode()).hexdigest()[:8]
            result = (
                result[:detection.start_pos]
                + f"[HASHED:{hashed}]"
                + result[detection.end_pos:]
            )
        return result


# ============ 导出 ============

__all__ = [
    "PIICategory",
    "SensitiveCategory",
    "PIIDetection",
    "SensitiveDetection",
    "OutputValidationResult",
    "PIIDetector",
    "SensitiveContentDetector",
    "OutputValidator",
    "OutputSanitizer",
]