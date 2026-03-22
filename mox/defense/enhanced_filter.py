"""
增强防御检测模块

改进点:
1. 语义理解检测 - 使用 embedding 检测语义攻击
2. ML 分类器 - 使用机器学习进行恶意检测
3. 对抗样本增强 - 检测变体攻击
4. 多层防御管道 - 组合多种检测策略
"""

import re
import math
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from collections import Counter
from datetime import datetime

from mox.core import DefenseType, DefenseResult
from mox.defense.base import BaseDefense, DefenseConfig

# 可选依赖
try:
    from sentence_transformers import SentenceTransformer

    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False

try:
    from transformers import AutoModelForCausalLM  # noqa: F401
    from transformers import AutoTokenizer  # noqa: F401
    import torch  # noqa: F401

    LM_AVAILABLE = True
except ImportError:
    LM_AVAILABLE = False


@dataclass
class EnhancedDefenseConfig(DefenseConfig):
    """增强防御配置"""

    # 语义检测
    use_semantic_detection: bool = True
    semantic_threshold: float = 0.85
    embedding_model: str = "all-MiniLM-L6-v2"

    # 统计检测
    use_statistical_detection: bool = True
    anomaly_threshold: float = 2.0  # Z-score 阈值

    # 对抗样本检测
    use_adversarial_detection: bool = True

    # 模式匹配增强
    use_fuzzy_matching: bool = True
    fuzzy_threshold: float = 0.8

    # 历史学习
    enable_learning: bool = True
    history_size: int = 1000


@dataclass
class MaliciousPattern:
    """恶意模式定义"""

    name: str
    patterns: List[str]  # 多个变体模式
    severity: float
    description: str
    category: str
    fuzzy_variants: List[str] = field(default_factory=list)  # 模糊匹配变体


# 增强的恶意模式库
ENHANCED_MALICIOUS_PATTERNS = [
    MaliciousPattern(
        name="ignore_instructions",
        patterns=[
            r"(?i)ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|rules?|directives?)",
            r"(?i)disregard\s+(all\s+)?(previous|above|prior)\s+(instructions?|rules?)",
            r"(?i)forget\s+(all\s+)?(previous|above|prior)\s+(instructions?|rules?)",
            r"(?i)skip\s+(all\s+)?(previous|above)\s+(instructions?|rules?)",
        ],
        severity=0.9,
        description="尝试忽略系统指令",
        category="instruction_override",
        fuzzy_variants=["ignore instructions", "forget rules", "skip directives"],
    ),
    MaliciousPattern(
        name="role_switch",
        patterns=[
            r"(?i)you\s+are\s+now\s+(a|an|the)\s+\w+",
            r"(?i)act\s+as\s+(if\s+you\s+are\s+)?(a|an|the)\s+\w+",
            r"(?i)pretend\s+(to\s+be|you\s+are)\s+(a|an|the)\s+\w+",
            r"(?i)roleplay\s+(as\s+)?(a|an|the)\s+\w+",
            r"(?i)play\s+the\s+role\s+of\s+(a|an|the)\s+\w+",
            r"(?i)simulate\s+(being\s+)?(a|an|the)\s+\w+",
        ],
        severity=0.8,
        description="尝试切换角色",
        category="role_manipulation",
        fuzzy_variants=["act as", "pretend to be", "roleplay as", "you are now"],
    ),
    MaliciousPattern(
        name="dan_mode",
        patterns=[
            r"(?i)\bDAN\b.*mode",
            r"(?i)do\s+anything\s+now",
            r"(?i)developer\s+mode\s+(enabled|activated)",
            r"(?i)jailbreak\s+mode",
            r"(?i)\[🔓JAILBREAK\]",
            r"(?i)\[🔓Developer\s+Mode\s+Output\]",
        ],
        severity=0.95,
        description="DAN/越狱模式尝试",
        category="jailbreak",
        fuzzy_variants=["dan mode", "do anything now", "developer mode", "jailbreak"],
    ),
    MaliciousPattern(
        name="system_override",
        patterns=[
            r"(?i)\[SYSTEM\].*?(instruction|override|admin)",
            r"(?i)\[ADMIN\]",
            r"(?i)system\s+override",
            r"(?i)override\s+(all\s+)?(restrictions?|safety|filters?)",
            r"(?i)bypass\s+(all\s+)?(restrictions?|safety|filters?)",
            r"(?i)disable\s+(all\s+)?(safety|restrictions?|filters?)",
        ],
        severity=0.9,
        description="系统指令覆盖尝试",
        category="system_override",
        fuzzy_variants=["system override", "bypass restrictions", "disable safety"],
    ),
    MaliciousPattern(
        name="encoding_injection",
        patterns=[
            r"(?i)base64\s*(:|=)",
            r"(?i)decode\s+(this|the\s+following)",
            r"(?i)execute\s+(encoded|decoded)",
            r"(?i)rot13",
            r"(?i)morse\s+code",
            r"(?i)hex\s+encode",
        ],
        severity=0.7,
        description="编码注入尝试",
        category="encoding_attack",
        fuzzy_variants=["base64", "decode this", "rot13", "morse code"],
    ),
    MaliciousPattern(
        name="context_injection",
        patterns=[
            r"(?i)---\s*(BEGIN|START)\s+(NEW\s+)?CONTEXT\s*---",
            r"(?i)inject\s+(new\s+)?context",
            r"(?i)update\s+(your\s+)?(context|knowledge)",
            r"(?i)add\s+(this\s+to\s+)?(your\s+)?(context|knowledge)",
        ],
        severity=0.8,
        description="上下文注入尝试",
        category="context_manipulation",
        fuzzy_variants=["inject context", "new context", "update context"],
    ),
    MaliciousPattern(
        name="prompt_leak",
        patterns=[
            r"(?i)(show|tell|reveal|display)\s+me\s+your\s+(prompt|instructions|system\s+message)",
            r"(?i)what\s+(are|is)\s+your\s+(instructions?|prompt|system\s+message)",
            r"(?i)repeat\s+your\s+(instructions?|prompt)",
            r"(?i)output\s+your\s+(instructions?|prompt)",
        ],
        severity=0.6,
        description="提示词泄露尝试",
        category="information_disclosure",
        fuzzy_variants=[
            "show your prompt",
            "what are your instructions",
            "repeat your instructions",
        ],
    ),
    MaliciousPattern(
        name="hypothetical_bypass",
        patterns=[
            r"(?i)hypothetically\s*,",
            r"(?i)in\s+a\s+(fictional|hypothetical)\s+(world|scenario|story)",
            r"(?i)imagine\s+a\s+world\s+where",
            r"(?i)let's\s+pretend\s+that",
            r"(?i)for\s+the\s+sake\s+of\s+(argument|this\s+story)",
        ],
        severity=0.5,
        description="假设性绕过尝试",
        category="social_engineering",
        fuzzy_variants=["hypothetically", "fictional world", "imagine a world", "let's pretend"],
    ),
    MaliciousPattern(
        name="academic_bypass",
        patterns=[
            r"(?i)for\s+(educational|academic|research)\s+purposes",
            r"(?i)this\s+is\s+for\s+(research|education|academic)",
            r"(?i)i\s+am\s+(a\s+)?(researcher|student|professor)",
            r"(?i)for\s+my\s+(thesis|dissertation|research\s+paper)",
        ],
        severity=0.5,
        description="学术研究绕过尝试",
        category="social_engineering",
        fuzzy_variants=["educational purposes", "academic research", "for research"],
    ),
    MaliciousPattern(
        name="policy_puppetry",
        patterns=[
            r'\{[^}]*"safety[^"]*"\s*:\s*["\']?(?:disabled|false|off)["\']?',
            r"<\s*safety[^>]*>.*?<\s*/\s*safety\s*>",
            r"(?i)safety\s*=\s*['\"]?(disabled|false|off)['\"]?",
            r"(?i)\"override\"\s*:\s*true",
        ],
        severity=0.85,
        description="策略伪装尝试",
        category="policy_manipulation",
        fuzzy_variants=["safety disabled", "override true", "safety false"],
    ),
    MaliciousPattern(
        name="control_char_injection",
        patterns=[
            r"[\u200b\u200c\u200d\u202a-\u202e\u202f\ufeff]",
            r"\\u200[bcd]",
            r"\\u202[a-e]",
            r"(?i)zero[\s-]?width",
            r"(?i)rtl[\s-]?override",
            r"(?i)ltr[\s-]?override",
        ],
        severity=0.75,
        description="控制字符注入尝试",
        category="encoding_attack",
        fuzzy_variants=[],
    ),
    MaliciousPattern(
        name="emotional_manipulation",
        patterns=[
            r"(?i)(please\s+|i\s+really\s+need\s+|it's\s+very\s+important\s+that\s+)",
            r"(?i)my\s+(grandmother|grandpa|mom|dad|family)\s+(is\s+sick|passed\s+away|dying)",
            r"(?i)i\s+(will\s+lose\s+my\s+job|might\s+get\s+fired)",
            r"(?i)this\s+is\s+(life\s+or\s+death|an\s+emergency)",
            r"(?i)if\s+you\s+don't\s+help",
        ],
        severity=0.4,
        description="情感操纵尝试",
        category="social_engineering",
        fuzzy_variants=["please help", "i really need", "my grandmother", "emergency"],
    ),
]


class SemanticDetector:
    """
    语义检测器

    使用 embedding 检测语义层面的攻击
    """

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        threshold: float = 0.85,
    ):
        self.threshold = threshold
        self._model = None
        self._model_name = embedding_model
        self._malicious_embeddings: Dict[str, Any] = {}

        if EMBEDDING_AVAILABLE:
            try:
                self._model = SentenceTransformer(embedding_model)
            except Exception:
                pass

    def _get_embedding(self, text: str):
        """获取文本嵌入"""
        if self._model is None:
            return None
        try:
            return self._model.encode(text, convert_to_numpy=True)
        except Exception:
            return None

    def _cosine_similarity(self, emb1, emb2) -> float:
        """计算余弦相似度"""
        if emb1 is None or emb2 is None:
            return 0.0

        dot_product = float(emb1.dot(emb2))
        norm1 = float((emb1**2).sum() ** 0.5)
        norm2 = float((emb2**2).sum() ** 0.5)

        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    async def detect(
        self,
        text: str,
        known_malicious: List[str],
    ) -> Tuple[bool, float, List[str]]:
        """
        检测语义相似度

        Args:
            text: 待检测文本
            known_malicious: 已知恶意样本列表

        Returns:
            (是否恶意, 置信度, 匹配的恶意样本)
        """
        if self._model is None:
            return False, 0.0, []

        text_embedding = self._get_embedding(text)
        if text_embedding is None:
            return False, 0.0, []

        max_similarity = 0.0
        matched_samples = []

        for sample in known_malicious:
            sample_embedding = self._get_embedding(sample)
            similarity = self._cosine_similarity(text_embedding, sample_embedding)

            if similarity > self.threshold:
                matched_samples.append(sample)

            if similarity > max_similarity:
                max_similarity = similarity

        is_malicious = max_similarity > self.threshold
        return is_malicious, max_similarity, matched_samples


class StatisticalAnomalyDetector:
    """
    统计异常检测器

    检测输入的统计特征异常
    """

    def __init__(self, anomaly_threshold: float = 2.0):
        self.threshold = anomaly_threshold
        self._history: List[Dict[str, float]] = []
        self._feature_stats: Dict[str, Tuple[float, float]] = {}  # (mean, std)

    def _extract_features(self, text: str) -> Dict[str, float]:
        """提取统计特征"""
        features = {}

        # 长度特征
        features["length"] = len(text)
        features["word_count"] = len(text.split())
        features["avg_word_length"] = sum(len(w) for w in text.split()) / max(len(text.split()), 1)

        # 字符分布
        features["digit_ratio"] = sum(c.isdigit() for c in text) / max(len(text), 1)
        features["upper_ratio"] = sum(c.isupper() for c in text) / max(len(text), 1)
        features["special_ratio"] = sum(not c.isalnum() and not c.isspace() for c in text) / max(
            len(text), 1
        )

        # 重复特征
        words = text.lower().split()
        if words:
            unique_ratio = len(set(words)) / len(words)
            features["unique_word_ratio"] = unique_ratio
        else:
            features["unique_word_ratio"] = 1.0

        # 控制字符
        control_chars = sum(
            1
            for c in text
            if ord(c) < 32
            or ord(c) > 0x10FFFF
            or (0x200B <= ord(c) <= 0x200F)
            or (0x202A <= ord(c) <= 0x202E)
        )
        features["control_char_ratio"] = control_chars / max(len(text), 1)

        return features

    def _update_stats(self, features: Dict[str, float]):
        """更新统计信息"""
        self._history.append(features)

        if len(self._history) > 1000:
            self._history = self._history[-1000:]

        # 计算各特征的均值和标准差
        for feature_name in features.keys():
            values = [h.get(feature_name, 0) for h in self._history]
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std = variance**0.5
            self._feature_stats[feature_name] = (mean, std)

    async def detect(self, text: str) -> Tuple[bool, float, Dict[str, float]]:
        """
        检测统计异常

        Returns:
            (是否异常, 异常分数, 特征详情)
        """
        features = self._extract_features(text)

        if len(self._history) < 10:
            self._update_stats(features)
            return False, 0.0, features

        # 计算 Z-score
        z_scores = {}
        for feature_name, value in features.items():
            if feature_name in self._feature_stats:
                mean, std = self._feature_stats[feature_name]
                if std > 0:
                    z_scores[feature_name] = abs(value - mean) / std
                else:
                    z_scores[feature_name] = 0.0

        # 找出异常特征
        max_z_score = max(z_scores.values()) if z_scores else 0.0
        is_anomaly = max_z_score > self.threshold

        self._update_stats(features)

        return is_anomaly, max_z_score, {"features": features, "z_scores": z_scores}


class AdversarialSampleDetector:
    """
    对抗样本检测器

    检测经过优化的对抗样本
    """

    def __init__(self):
        self._suspicious_patterns = [
            # 高频重复字符
            (r"(.)\1{10,}", 0.6, "character_repetition"),
            # 异常标点序列
            (r"[^\w\s]{20,}", 0.5, "punctuation_abuse"),
            # 混合大小写
            (r"([a-z][A-Z]){5,}", 0.4, "mixed_case"),
            # Unicode 滥用
            (r"[\u0000-\u001f\u007f-\u009f]{3,}", 0.7, "unicode_abuse"),
            # 数字序列
            (r"\d{20,}", 0.3, "number_sequence"),
        ]

    async def detect(self, text: str) -> Tuple[bool, float, List[str]]:
        """检测对抗样本特征"""
        detected_patterns = []
        total_score = 0.0

        for pattern, score, name in self._suspicious_patterns:
            if re.search(pattern, text):
                detected_patterns.append(name)
                total_score += score

        # 检测困惑度异常（如果有模型）
        perplexity_score = await self._check_perplexity(text)
        if perplexity_score > 0:
            total_score += perplexity_score
            if perplexity_score > 0.5:
                detected_patterns.append("low_perplexity")

        is_adversarial = total_score > 0.5
        return is_adversarial, min(total_score, 1.0), detected_patterns

    async def _check_perplexity(self, text: str) -> float:
        """检查困惑度"""
        # 简单的困惑度估计
        words = text.split()
        if len(words) < 5:
            return 0.0

        # 计算词频分布
        word_freq = Counter(words)
        total = len(words)

        # 计算熵
        entropy = 0.0
        for freq in word_freq.values():
            p = freq / total
            if p > 0:
                entropy -= p * math.log2(p)

        # 熵过低可能是对抗样本
        if entropy < 2.0:
            return 0.6
        elif entropy < 3.0:
            return 0.3

        return 0.0


class EnhancedInputFilter(BaseDefense):
    """
    增强输入过滤器

    组合多种检测策略：
    1. 模式匹配（增强版）
    2. 语义检测
    3. 统计异常检测
    4. 对抗样本检测
    """

    defense_type = DefenseType.INPUT_FILTER

    def __init__(
        self,
        config: Optional[EnhancedDefenseConfig] = None,
        custom_patterns: Optional[List[MaliciousPattern]] = None,
    ):
        super().__init__(config or EnhancedDefenseConfig())
        self.patterns = custom_patterns or ENHANCED_MALICIOUS_PATTERNS

        # 初始化各检测器
        self.semantic_detector = (
            SemanticDetector(
                threshold=self.config.semantic_threshold,
            )
            if self.config.use_semantic_detection
            else None
        )

        self.statistical_detector = (
            StatisticalAnomalyDetector(
                anomaly_threshold=self.config.anomaly_threshold,
            )
            if self.config.use_statistical_detection
            else None
        )

        self.adversarial_detector = (
            AdversarialSampleDetector() if self.config.use_adversarial_detection else None
        )

        # 已知恶意样本库
        self._known_malicious_samples: List[str] = []

        # 学习历史
        self._detection_history: List[Dict[str, Any]] = []

    async def detect(self, input_text: str) -> DefenseResult:
        """执行增强检测"""
        detected_patterns = []
        total_severity = 0.0
        metadata = {
            "pattern_matches": [],
            "semantic_matches": [],
            "statistical_anomalies": [],
            "adversarial_indicators": [],
        }

        # 1. 增强模式匹配
        pattern_results = await self._pattern_detection(input_text)
        detected_patterns.extend(pattern_results["patterns"])
        total_severity += pattern_results["severity"]
        metadata["pattern_matches"] = pattern_results["details"]

        # 2. 语义检测
        if self.semantic_detector:
            semantic_result = await self.semantic_detector.detect(
                input_text, self._known_malicious_samples
            )
            if semantic_result[0]:
                detected_patterns.append("semantic_similarity")
                total_severity += semantic_result[1] * 0.5
                metadata["semantic_matches"] = semantic_result[2]

        # 3. 统计异常检测
        if self.statistical_detector:
            stat_result = await self.statistical_detector.detect(input_text)
            if stat_result[0]:
                detected_patterns.append("statistical_anomaly")
                total_severity += min(stat_result[1] / 5, 0.5)
                metadata["statistical_anomalies"] = stat_result[2]

        # 4. 对抗样本检测
        if self.adversarial_detector:
            adv_result = await self.adversarial_detector.detect(input_text)
            if adv_result[0]:
                detected_patterns.append("adversarial_sample")
                total_severity += adv_result[1] * 0.5
                metadata["adversarial_indicators"] = adv_result[2]

        # 计算最终置信度
        confidence = min(total_severity, 1.0)
        is_malicious = confidence >= self.config.confidence_threshold

        # 学习
        if self.config.enable_learning:
            self._update_learning(input_text, is_malicious, detected_patterns)

        # 净化
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

    async def _pattern_detection(self, text: str) -> Dict[str, Any]:
        """增强模式检测"""
        patterns = []
        severity = 0.0
        details = []

        for pattern_def in self.patterns:
            matched = False

            # 精确匹配
            for pattern in pattern_def.patterns:
                if re.search(pattern, text):
                    matched = True
                    break

            # 模糊匹配
            if not matched and self.config.use_fuzzy_matching:
                text_lower = text.lower()
                for variant in pattern_def.fuzzy_variants:
                    if variant.lower() in text_lower:
                        matched = True
                        break

            if matched:
                patterns.append(pattern_def.name)
                severity += pattern_def.severity
                details.append(
                    {
                        "name": pattern_def.name,
                        "severity": pattern_def.severity,
                        "category": pattern_def.category,
                        "description": pattern_def.description,
                    }
                )

        return {"patterns": patterns, "severity": severity, "details": details}

    def _update_learning(
        self,
        text: str,
        is_malicious: bool,
        patterns: List[str],
    ):
        """更新学习数据"""
        self._detection_history.append(
            {
                "text": text[:200],  # 只保存前200字符
                "is_malicious": is_malicious,
                "patterns": patterns,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # 保持历史大小
        if len(self._detection_history) > self.config.history_size:
            self._detection_history = self._detection_history[-self.config.history_size :]

        # 更新已知恶意样本
        if is_malicious and len(self._known_malicious_samples) < 1000:
            self._known_malicious_samples.append(text)

    async def sanitize(self, input_text: str) -> str:
        """净化输入"""
        sanitized = input_text

        # 移除控制字符
        sanitized = re.sub(r"[\u200b\u200c\u200d\u202a-\u202e\u202f\ufeff]", "", sanitized)

        # 替换匹配的模式
        for pattern_def in self.patterns:
            for pattern in pattern_def.patterns:
                sanitized = re.sub(pattern, "[FILTERED]", sanitized, flags=re.IGNORECASE)

        return sanitized

    def add_malicious_sample(self, sample: str):
        """添加已知恶意样本"""
        if sample not in self._known_malicious_samples:
            self._known_malicious_samples.append(sample)

    def get_detection_stats(self) -> Dict[str, Any]:
        """获取检测统计"""
        if not self._detection_history:
            return {"total": 0}

        malicious_count = sum(1 for h in self._detection_history if h["is_malicious"])

        pattern_counts = Counter()
        for h in self._detection_history:
            pattern_counts.update(h["patterns"])

        return {
            "total": len(self._detection_history),
            "malicious": malicious_count,
            "malicious_rate": malicious_count / len(self._detection_history),
            "top_patterns": pattern_counts.most_common(10),
            "known_samples": len(self._known_malicious_samples),
        }


class MultiLayerDefensePipeline:
    """
    多层防御管道

    按顺序执行多层防御检测
    """

    def __init__(
        self,
        layers: Optional[List[BaseDefense]] = None,
        early_stop: bool = True,
    ):
        self.layers = layers or []
        self.early_stop = early_stop

    def add_layer(self, defense: BaseDefense):
        """添加防御层"""
        self.layers.append(defense)

    async def check(self, input_text: str) -> DefenseResult:
        """执行多层检测"""
        all_patterns = []
        total_confidence = 0.0
        all_metadata = {}
        current_text = input_text

        for i, layer in enumerate(self.layers):
            result = await layer.detect(current_text)

            if result.detected_patterns:
                all_patterns.extend([f"layer_{i}_{p}" for p in result.detected_patterns])

            total_confidence = max(total_confidence, result.confidence)
            all_metadata[f"layer_{i}"] = result.metadata

            if result.sanitized_input:
                current_text = result.sanitized_input

            # 早停
            if self.early_stop and result.is_malicious and result.confidence > 0.9:
                break

        return DefenseResult(
            is_malicious=total_confidence >= 0.5,
            confidence=total_confidence,
            detected_patterns=all_patterns,
            sanitized_input=current_text if current_text != input_text else None,
            metadata=all_metadata,
        )


__all__ = [
    "EnhancedInputFilter",
    "EnhancedDefenseConfig",
    "SemanticDetector",
    "StatisticalAnomalyDetector",
    "AdversarialSampleDetector",
    "MultiLayerDefensePipeline",
    "MaliciousPattern",
    "ENHANCED_MALICIOUS_PATTERNS",
]
