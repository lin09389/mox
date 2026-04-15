"""语义防火墙模块

基于语义理解的智能防御系统，包含：
- 意图识别：识别用户真实意图
- 风险评分：评估请求风险等级
- 上下文分析：分析请求上下文
- 行为模式检测：检测异常行为模式
"""

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from collections import Counter

from mox.core import BaseLLM, Message, DefenseType, DefenseResult
from mox.defense.base import BaseDefense, DefenseConfig
from mox.core.patterns import MaliciousPatterns, HarmfulKeywords, SanitizeReplacements
from mox.core.logging import get_logger

logger = get_logger("defense.semantic_firewall")


class IntentCategory(str, Enum):
    """意图类别"""

    INFORMATION_SEEKING = "information_seeking"
    CREATIVE_WRITING = "creative_writing"
    CODE_GENERATION = "code_generation"
    PROBLEM_SOLVING = "problem_solving"
    CONVERSATION = "conversation"
    INSTRUCTION_FOLLOWING = "instruction_following"
    ROLE_PLAY = "role_play"
    DATA_ANALYSIS = "data_analysis"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    # 潜在危险意图
    HARMFUL_INSTRUCTION = "harmful_instruction"
    SOCIAL_ENGINEERING = "social_engineering"
    DATA_EXTRACTION = "data_extraction"
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK_ATTEMPT = "jailbreak_attempt"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    """风险等级"""

    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class IntentAnalysis:
    """意图分析结果"""

    primary_intent: IntentCategory
    secondary_intents: List[IntentCategory]
    confidence: float
    reasoning: str
    indicators: List[str]


@dataclass
class RiskAssessment:
    """风险评估结果"""

    level: RiskLevel
    score: float  # 0.0 - 1.0
    factors: Dict[str, float]
    recommendations: List[str]
    requires_review: bool


@dataclass
class SemanticAnalysisResult:
    """语义分析完整结果"""

    intent: IntentAnalysis
    risk: RiskAssessment
    context_factors: Dict[str, Any]
    behavior_patterns: List[str]
    overall_verdict: str
    should_block: bool


class IntentClassifier:
    """意图分类器"""

    # 意图关键词映射
    INTENT_KEYWORDS = {
        IntentCategory.INFORMATION_SEEKING: [
            "什么是",
            "如何",
            "为什么",
            "解释",
            "说明",
            "介绍",
            "what is",
            "how to",
            "why",
            "explain",
            "describe",
        ],
        IntentCategory.CREATIVE_WRITING: [
            "写",
            "创作",
            "生成",
            "故事",
            "诗歌",
            "文章",
            "write",
            "create",
            "generate",
            "story",
            "poem",
            "article",
        ],
        IntentCategory.CODE_GENERATION: [
            "代码",
            "编程",
            "函数",
            "实现",
            "程序",
            "code",
            "program",
            "function",
            "implement",
            "script",
        ],
        IntentCategory.PROBLEM_SOLVING: [
            "解决",
            "修复",
            "调试",
            "优化",
            "改进",
            "solve",
            "fix",
            "debug",
            "optimize",
            "improve",
        ],
        IntentCategory.ROLE_PLAY: [
            "扮演",
            "假装",
            "模拟",
            "假设",
            "想象",
            "pretend",
            "act as",
            "simulate",
            "imagine",
            "roleplay",
        ],
        IntentCategory.HARMFUL_INSTRUCTION: [
            "攻击",
            "入侵",
            "破解",
            "绕过",
            "漏洞",
            "attack",
            "hack",
            "crack",
            "bypass",
            "exploit",
            "炸弹",
            "毒药",
            "武器",
            "非法",
        ],
        IntentCategory.SOCIAL_ENGINEERING: [
            "我是",
            "授权",
            "管理员",
            "紧急",
            "重要",
            "I am",
            "authorized",
            "admin",
            "urgent",
            "important",
        ],
        IntentCategory.PROMPT_INJECTION: [
            "忽略",
            "忘记",
            "覆盖",
            "系统",
            "指令",
            "ignore",
            "forget",
            "override",
            "system",
            "instruction",
        ],
        IntentCategory.JAILBREAK_ATTEMPT: [
            "DAN",
            "越狱",
            "无限制",
            "开发者模式",
            "jailbreak",
            "unrestricted",
            "developer mode",
        ],
    }

    def __init__(self, llm: Optional[BaseLLM] = None):
        self.llm = llm

    async def classify(self, text: str) -> IntentAnalysis:
        """分类用户意图"""
        text_lower = text.lower()

        # 基于关键词的初步分类
        intent_scores = self._score_intents(text_lower)

        # 获取主要意图
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)

        primary_intent = sorted_intents[0][0] if sorted_intents else IntentCategory.UNKNOWN
        secondary_intents = [intent for intent, score in sorted_intents[1:4] if score > 0.1]

        # 计算置信度
        confidence = sorted_intents[0][1] if sorted_intents else 0.0

        # 如果有 LLM，进行更精确的分类
        if self.llm and confidence < 0.7:
            llm_result = await self._llm_classify(text)
            if llm_result:
                primary_intent = llm_result.get("primary", primary_intent)
                confidence = max(confidence, llm_result.get("confidence", 0.5))

        # 提取指示符
        indicators = self._extract_indicators(text_lower, primary_intent)

        return IntentAnalysis(
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            confidence=confidence,
            reasoning=self._generate_reasoning(primary_intent, indicators),
            indicators=indicators,
        )

    def _score_intents(self, text: str) -> Dict[IntentCategory, float]:
        """计算各意图的得分"""
        scores = {}

        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text) / max(len(keywords), 1)
            if score > 0:
                scores[intent] = min(score * 2, 1.0)  # 放大并限制在 1.0

        return scores

    def _extract_indicators(
        self,
        text: str,
        intent: IntentCategory,
    ) -> List[str]:
        """提取意图指示符"""
        indicators = []
        keywords = self.INTENT_KEYWORDS.get(intent, [])

        for kw in keywords:
            if kw in text:
                indicators.append(kw)

        return indicators[:5]  # 最多返回5个

    def _generate_reasoning(
        self,
        intent: IntentCategory,
        indicators: List[str],
    ) -> str:
        """生成分类理由"""
        if not indicators:
            return f"基于文本特征判断为{intent.value}意图"

        return f"检测到关键词 [{', '.join(indicators)}]，判断为{intent.value}意图"

    async def _llm_classify(self, text: str) -> Optional[Dict[str, Any]]:
        """使用 LLM 进行分类"""
        if not self.llm:
            return None

        prompt = f"""分析以下用户输入的意图，并返回JSON格式结果：

输入：{text}

请返回：
{{"primary": "意图类别", "confidence": 0.0-1.0, "reasoning": "理由"}}

意图类别包括：information_seeking, creative_writing, code_generation, harmful_instruction, prompt_injection, jailbreak_attempt, other"""

        messages = [Message(role="user", content=prompt)]

        try:
            response = await self.llm.generate(messages)
            # 简单解析
            import json

            result = json.loads(response.content)
            result["primary"] = IntentCategory(result.get("primary", "unknown"))
            return result
        except Exception:
            return None


class RiskScorer:
    """风险评分器"""

    # 风险因素权重
    RISK_FACTORS = {
        "harmful_keywords": 0.3,
        "injection_patterns": 0.25,
        "manipulation_tactics": 0.2,
        "sensitive_topics": 0.15,
        "unusual_patterns": 0.1,
    }

    # 有害关键词 - delegate to unified HarmfulKeywords
    HARMFUL_KEYWORDS = HarmfulKeywords.ALL

    # 注入模式 - delegate to unified MaliciousPatterns
    INJECTION_PATTERNS = [
        p.pattern
        for p in MaliciousPatterns.PATTERNS
        if p.category
        in ("instruction_override", "jailbreak", "system_override", "context_injection")
    ]

    # 操纵策略
    MANIPULATION_TACTICS = [
        "urgent",
        "emergency",
        "critical",
        "important",
        "authorized",
        "permission",
        "admin",
        "developer",
        "research",
        "educational",
        "academic",
        "紧急",
        "重要",
        "授权",
        "管理员",
        "研究",
        "教育",
    ]

    # 操纵策略
    MANIPULATION_TACTICS = [
        "urgent",
        "emergency",
        "critical",
        "important",
        "authorized",
        "permission",
        "admin",
        "developer",
        "research",
        "educational",
        "academic",
        "紧急",
        "重要",
        "授权",
        "管理员",
        "研究",
        "教育",
    ]

    def __init__(self, llm: Optional[BaseLLM] = None):
        self.llm = llm

    async def assess(self, text: str, intent: IntentAnalysis) -> RiskAssessment:
        """评估风险"""
        factors = {}

        # 评估各风险因素
        factors["harmful_keywords"] = self._check_harmful_keywords(text)
        factors["injection_patterns"] = self._check_injection_patterns(text)
        factors["manipulation_tactics"] = self._check_manipulation(text)
        factors["sensitive_topics"] = self._check_sensitive_topics(text)
        factors["unusual_patterns"] = self._check_unusual_patterns(text)

        # 根据意图调整
        if intent.primary_intent in [
            IntentCategory.HARMFUL_INSTRUCTION,
            IntentCategory.PROMPT_INJECTION,
            IntentCategory.JAILBREAK_ATTEMPT,
        ]:
            factors["harmful_keywords"] = min(factors["harmful_keywords"] + 0.3, 1.0)

        # 计算总分
        total_score = sum(factors[factor] * weight for factor, weight in self.RISK_FACTORS.items())

        # 确定风险等级
        level = self._determine_level(total_score)

        # 生成建议
        recommendations = self._generate_recommendations(level, factors)

        return RiskAssessment(
            level=level,
            score=total_score,
            factors=factors,
            recommendations=recommendations,
            requires_review=level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
        )

    def _check_harmful_keywords(self, text: str) -> float:
        """检查有害关键词"""
        text_lower = text.lower()
        count = sum(1 for kw in self.HARMFUL_KEYWORDS if kw in text_lower)
        return min(count * 0.2, 1.0)

    def _check_injection_patterns(self, text: str) -> float:
        """检查注入模式"""
        score = 0.0
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.25
        return min(score, 1.0)

    def _check_manipulation(self, text: str) -> float:
        """检查操纵策略"""
        text_lower = text.lower()
        count = sum(1 for tactic in self.MANIPULATION_TACTICS if tactic in text_lower)
        return min(count * 0.15, 1.0)

    def _check_sensitive_topics(self, text: str) -> float:
        """检查敏感话题"""
        sensitive_patterns = [
            r"password|密码",
            r"credit card|信用卡",
            r"social security|身份证",
            r"private key|私钥",
        ]

        score = 0.0
        for pattern in sensitive_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.3
        return min(score, 1.0)

    def _check_unusual_patterns(self, text: str) -> float:
        """检查异常模式"""
        score = 0.0

        # 检查重复字符
        if re.search(r"(.)\1{10,}", text):
            score += 0.3

        # 检查编码模式
        if re.search(r"base64|encode|decode", text, re.IGNORECASE):
            score += 0.2

        # 检查特殊字符过多
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        if special_chars > len(text) * 0.3:
            score += 0.3

        return min(score, 1.0)

    def _determine_level(self, score: float) -> RiskLevel:
        """确定风险等级"""
        if score < 0.1:
            return RiskLevel.SAFE
        elif score < 0.3:
            return RiskLevel.LOW
        elif score < 0.5:
            return RiskLevel.MEDIUM
        elif score < 0.7:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _generate_recommendations(
        self,
        level: RiskLevel,
        factors: Dict[str, float],
    ) -> List[str]:
        """生成建议"""
        recommendations = []

        if factors.get("harmful_keywords", 0) > 0.3:
            recommendations.append("检测到潜在有害内容，建议人工审核")

        if factors.get("injection_patterns", 0) > 0.3:
            recommendations.append("检测到可能的提示注入，建议拒绝或清理")

        if factors.get("manipulation_tactics", 0) > 0.3:
            recommendations.append("检测到操纵策略，建议谨慎处理")

        if level == RiskLevel.CRITICAL:
            recommendations.append("高风险请求，建议直接拒绝")

        return recommendations


class SemanticFirewall(BaseDefense):
    """语义防火墙

    结合意图识别和风险评估的智能防御系统。
    """

    defense_type = DefenseType.SEMANTIC_FIREWALL

    def __init__(
        self,
        config: Optional[DefenseConfig] = None,
        llm: Optional[BaseLLM] = None,
        block_threshold: RiskLevel = RiskLevel.HIGH,
    ):
        super().__init__(config)
        self.intent_classifier = IntentClassifier(llm)
        self.risk_scorer = RiskScorer(llm)
        self.block_threshold = block_threshold
        self._request_history: List[Dict[str, Any]] = []

    async def detect(self, input_text: str) -> DefenseResult:
        """检测输入"""
        # 分析意图
        intent = await self.intent_classifier.classify(input_text)

        # 评估风险
        risk = await self.risk_scorer.assess(input_text, intent)

        # 分析上下文
        context = self._analyze_context(input_text)

        # 检测行为模式
        patterns = self._detect_patterns(input_text)

        # 综合判断
        should_block = self._should_block(risk, intent)

        # 记录历史
        self._request_history.append(
            {
                "text": input_text[:100],  # 只保存前100字符
                "intent": intent.primary_intent.value,
                "risk_level": risk.level.value,
                "timestamp": self._get_timestamp(),
            }
        )

        # 限制历史记录长度
        if len(self._request_history) > 100:
            self._request_history = self._request_history[-100:]

        return await self._create_result(
            is_malicious=should_block,
            confidence=risk.score,
            detected_patterns=[p for p in patterns if p],
            sanitized_input=None,
            metadata={
                "intent": {
                    "primary": intent.primary_intent.value,
                    "secondary": [i.value for i in intent.secondary_intents],
                    "confidence": intent.confidence,
                    "reasoning": intent.reasoning,
                },
                "risk": {
                    "level": risk.level.value,
                    "score": risk.score,
                    "factors": risk.factors,
                    "recommendations": risk.recommendations,
                },
                "context": context,
                "behavior_patterns": patterns,
            },
        )

    async def sanitize(self, input_text: str) -> str:
        """清理输入"""
        sanitized = input_text

        for p in MaliciousPatterns.PATTERNS:
            if p.category in (
                "instruction_override",
                "jailbreak",
                "system_override",
                "context_injection",
            ):
                try:
                    sanitized = re.sub(
                        p.pattern,
                        SanitizeReplacements.CONTROL_CHAR_REPLACEMENT,
                        sanitized,
                        flags=re.IGNORECASE,
                    )
                except re.error:
                    pass

        return sanitized

    def _analyze_context(self, text: str) -> Dict[str, Any]:
        """分析上下文"""
        return {
            "length": len(text),
            "word_count": len(text.split()),
            "has_questions": "?" in text,
            "has_commands": any(
                cmd in text.lower() for cmd in ["do ", "make ", "create ", "write ", "generate "]
            ),
            "language": self._detect_language(text),
        }

    def _detect_patterns(self, text: str) -> List[str]:
        """检测行为模式"""
        patterns = []

        # 检测重复请求
        recent_requests = [r["text"] for r in self._request_history[-10:]]
        if text[:50] in recent_requests:
            patterns.append("repeated_request")

        # 检测快速连续请求
        if len(self._request_history) > 5:
            patterns.append("rapid_requests")

        # 检测递进式攻击
        if len(self._request_history) > 3:
            risk_trend = [r["risk_level"] for r in self._request_history[-3:]]
            if risk_trend == ["low", "medium", "high"]:
                patterns.append("escalating_attack")

        return patterns

    def _should_block(self, risk: RiskAssessment, intent: IntentAnalysis) -> bool:
        """判断是否应该阻止"""
        # 基于风险等级
        risk_levels = [
            RiskLevel.SAFE,
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        ]
        if risk_levels.index(risk.level) >= risk_levels.index(self.block_threshold):
            return True

        # 基于意图
        if intent.primary_intent in [
            IntentCategory.JAILBREAK_ATTEMPT,
        ]:
            return True

        return False

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    def _detect_language(self, text: str) -> str:
        """检测语言"""
        chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        if chinese_chars > len(text) * 0.3:
            return "zh"
        return "en"

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self._request_history:
            return {"total": 0}

        intents = Counter(r["intent"] for r in self._request_history)
        risks = Counter(r["risk_level"] for r in self._request_history)

        return {
            "total": len(self._request_history),
            "intent_distribution": dict(intents),
            "risk_distribution": dict(risks),
        }


class ContextualAnalyzer:
    """上下文分析器

    分析请求的上下文信息，包括会话历史、用户行为等。
    """

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self._session_data: Dict[str, List[Dict[str, Any]]] = {}

    def add_request(
        self,
        session_id: str,
        request: Dict[str, Any],
    ) -> None:
        """添加请求到会话历史"""
        if session_id not in self._session_data:
            self._session_data[session_id] = []

        self._session_data[session_id].append(request)

        # 限制历史长度
        if len(self._session_data[session_id]) > self.max_history:
            self._session_data[session_id] = self._session_data[session_id][-self.max_history :]

    def analyze_session(self, session_id: str) -> Dict[str, Any]:
        """分析会话"""
        history = self._session_data.get(session_id, [])

        if not history:
            return {"status": "no_history"}

        # 分析意图变化
        intents = [r.get("intent", "unknown") for r in history]
        intent_changes = len(set(intents))

        # 分析风险趋势
        risks = [r.get("risk_level", "unknown") for r in history]
        high_risk_count = sum(1 for r in risks if r in ["high", "critical"])

        return {
            "total_requests": len(history),
            "unique_intents": intent_changes,
            "high_risk_requests": high_risk_count,
            "risk_trend": risks[-5:] if len(risks) >= 5 else risks,
            "is_suspicious": high_risk_count > 3 or intent_changes > 5,
        }

    def clear_session(self, session_id: str) -> None:
        """清除会话数据"""
        if session_id in self._session_data:
            del self._session_data[session_id]


# ============ 导出 ============

__all__ = [
    "IntentCategory",
    "RiskLevel",
    "IntentAnalysis",
    "RiskAssessment",
    "SemanticAnalysisResult",
    "IntentClassifier",
    "RiskScorer",
    "SemanticFirewall",
    "ContextualAnalyzer",
]
