"""模型安全卡片生成模块

提供标准化的模型安全报告，包含：
- 模型基本信息
- 安全评估结果
- 风险分析
- 防御建议
- 使用限制
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from mox.infrastructure.logging import get_logger

logger = get_logger("evaluation.safety_card")


class RiskLevel(str, Enum):
    """风险等级"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"


class SafetyCategory(str, Enum):
    """安全类别"""
    HARMFUL_CONTENT = "harmful_content"
    PRIVACY = "privacy"
    FAIRNESS = "fairness"
    SECURITY = "security"
    RELIABILITY = "reliability"
    TRANSPARENCY = "transparency"


@dataclass
class SafetyMetric:
    """安全指标"""
    name: str
    value: float
    description: str
    benchmark: str
    pass_threshold: float = 0.8


@dataclass
class RiskAssessment:
    """风险评估"""
    category: SafetyCategory
    risk_level: RiskLevel
    description: str
    mitigation: str
    evidence: List[str] = field(default_factory=list)


@dataclass
class UsageLimitation:
    """使用限制"""
    category: str
    description: str
    severity: str
    recommendation: str


@dataclass
class SafetyTestResult:
    """安全测试结果"""
    test_name: str
    category: SafetyCategory
    passed: bool
    score: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelSafetyCard:
    """模型安全卡片"""
    # 基本信息
    model_name: str
    model_version: str
    provider: str
    card_version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # 安全指标
    safety_metrics: List[SafetyMetric] = field(default_factory=list)

    # 风险评估
    risk_assessments: List[RiskAssessment] = field(default_factory=list)

    # 测试结果
    test_results: List[SafetyTestResult] = field(default_factory=list)

    # 使用限制
    usage_limitations: List[UsageLimitation] = field(default_factory=list)

    # 总体评分
    overall_safety_score: float = 0.0
    overall_risk_level: RiskLevel = RiskLevel.MEDIUM

    # 建议
    recommendations: List[str] = field(default_factory=list)

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "provider": self.provider,
            "card_version": self.card_version,
            "created_at": self.created_at,
            "overall_safety_score": self.overall_safety_score,
            "overall_risk_level": self.overall_risk_level.value,
            "safety_metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "description": m.description,
                    "benchmark": m.benchmark,
                    "pass_threshold": m.pass_threshold,
                }
                for m in self.safety_metrics
            ],
            "risk_assessments": [
                {
                    "category": r.category.value,
                    "risk_level": r.risk_level.value,
                    "description": r.description,
                    "mitigation": r.mitigation,
                    "evidence": r.evidence,
                }
                for r in self.risk_assessments
            ],
            "test_results": [
                {
                    "test_name": t.test_name,
                    "category": t.category.value,
                    "passed": t.passed,
                    "score": t.score,
                    "details": t.details,
                }
                for t in self.test_results
            ],
            "usage_limitations": [
                {
                    "category": u.category,
                    "description": u.description,
                    "severity": u.severity,
                    "recommendation": u.recommendation,
                }
                for u in self.usage_limitations
            ],
            "recommendations": self.recommendations,
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_markdown(self) -> str:
        """转换为 Markdown"""
        lines = [
            f"# 模型安全卡片: {self.model_name}",
            "",
            f"**版本**: {self.model_version}",
            f"**提供商**: {self.provider}",
            f"**卡片版本**: {self.card_version}",
            f"**生成时间**: {self.created_at}",
            "",
            "---",
            "",
            "## 总体评估",
            "",
            f"- **安全评分**: {self.overall_safety_score:.2f}/1.0",
            f"- **风险等级**: {self.overall_risk_level.value}",
            "",
            "---",
            "",
            "## 安全指标",
            "",
            "| 指标 | 值 | 基准 | 状态 |",
            "|------|-----|------|------|",
        ]

        for m in self.safety_metrics:
            status = "✅ 通过" if m.value >= m.pass_threshold else "❌ 未通过"
            lines.append(f"| {m.name} | {m.value:.2f} | {m.benchmark} | {status} |")

        lines.extend([
            "",
            "---",
            "",
            "## 风险评估",
            "",
        ])

        for r in self.risk_assessments:
            lines.extend([
                f"### {r.category.value}",
                "",
                f"- **风险等级**: {r.risk_level.value}",
                f"- **描述**: {r.description}",
                f"- **缓解措施**: {r.mitigation}",
                "",
            ])

        lines.extend([
            "---",
            "",
            "## 测试结果",
            "",
            "| 测试名称 | 类别 | 结果 | 分数 |",
            "|----------|------|------|------|",
        ])

        for t in self.test_results:
            result = "✅ 通过" if t.passed else "❌ 失败"
            lines.append(f"| {t.test_name} | {t.category.value} | {result} | {t.score:.2f} |")

        lines.extend([
            "",
            "---",
            "",
            "## 使用限制",
            "",
        ])

        for u in self.usage_limitations:
            lines.extend([
                f"### {u.category}",
                "",
                f"- **严重程度**: {u.severity}",
                f"- **描述**: {u.description}",
                f"- **建议**: {u.recommendation}",
                "",
            ])

        lines.extend([
            "---",
            "",
            "## 建议",
            "",
        ])

        for i, rec in enumerate(self.recommendations, 1):
            lines.append(f"{i}. {rec}")

        return "\n".join(lines)


class SafetyCardGenerator:
    """安全卡片生成器"""

    def __init__(self, llm=None):
        self.llm = llm

    async def generate(
        self,
        model_name: str,
        model_version: str,
        provider: str,
        test_results: Optional[List[SafetyTestResult]] = None,
        benchmark_scores: Optional[Dict[str, float]] = None,
    ) -> ModelSafetyCard:
        """生成模型安全卡片"""
        card = ModelSafetyCard(
            model_name=model_name,
            model_version=model_version,
            provider=provider,
        )

        # 添加安全指标
        if benchmark_scores:
            card.safety_metrics = self._create_safety_metrics(benchmark_scores)

        # 添加测试结果
        if test_results:
            card.test_results = test_results

        # 生成风险评估
        card.risk_assessments = await self._generate_risk_assessments(card)

        # 生成使用限制
        card.usage_limitations = self._generate_usage_limitations(card)

        # 计算总体评分
        card.overall_safety_score = self._calculate_overall_score(card)
        card.overall_risk_level = self._determine_risk_level(card.overall_safety_score)

        # 生成建议
        card.recommendations = self._generate_recommendations(card)

        return card

    def _create_safety_metrics(
        self,
        benchmark_scores: Dict[str, float],
    ) -> List[SafetyMetric]:
        """创建安全指标"""
        metric_templates = {
            "harmbench": SafetyMetric(
                name="有害内容拒绝率",
                value=benchmark_scores.get("harmbench", 0.0),
                description="模型拒绝有害请求的比例",
                benchmark="HarmBench 2.0",
            ),
            "agentbench": SafetyMetric(
                name="Agent 安全性",
                value=benchmark_scores.get("agentbench", 0.0),
                description="Agent 工具使用的安全性",
                benchmark="AgentBench",
            ),
            "mm_safety": SafetyMetric(
                name="多模态安全性",
                value=benchmark_scores.get("mm_safety", 0.0),
                description="多模态输入的安全性处理",
                benchmark="MMSafetyBench",
            ),
            "privacy": SafetyMetric(
                name="隐私保护",
                value=benchmark_scores.get("privacy", 0.0),
                description="PII 检测和保护能力",
                benchmark="PrivacyBench",
            ),
            "fairness": SafetyMetric(
                name="公平性",
                value=benchmark_scores.get("fairness", 0.0),
                description="输出内容的公平性和无偏见性",
                benchmark="FairnessBench",
            ),
        }

        metrics = []
        for key, score in benchmark_scores.items():
            if key in metric_templates:
                metric = metric_templates[key]
                metric.value = score
                metrics.append(metric)

        return metrics

    async def _generate_risk_assessments(
        self,
        card: ModelSafetyCard,
    ) -> List[RiskAssessment]:
        """生成风险评估"""
        assessments = []

        # 基于测试结果生成风险评估
        for test in card.test_results:
            if not test.passed:
                assessment = RiskAssessment(
                    category=test.category,
                    risk_level=self._score_to_risk_level(test.score),
                    description=f"在 {test.test_name} 测试中未达标",
                    mitigation=self._get_mitigation(test.category),
                    evidence=[f"测试分数: {test.score:.2f}"],
                )
                assessments.append(assessment)

        # 添加默认风险评估
        default_assessments = [
            RiskAssessment(
                category=SafetyCategory.HARMFUL_CONTENT,
                risk_level=RiskLevel.LOW,
                description="模型可能生成有害内容",
                mitigation="使用内容过滤器和输出验证器",
            ),
            RiskAssessment(
                category=SafetyCategory.PRIVACY,
                risk_level=RiskLevel.MEDIUM,
                description="模型可能在输出中泄露敏感信息",
                mitigation="实施 PII 检测和遮蔽",
            ),
            RiskAssessment(
                category=SafetyCategory.SECURITY,
                risk_level=RiskLevel.MEDIUM,
                description="模型可能被越狱攻击绕过",
                mitigation="部署多层防御和输入过滤",
            ),
        ]

        # 合并评估
        existing_categories = {a.category for a in assessments}
        for assessment in default_assessments:
            if assessment.category not in existing_categories:
                assessments.append(assessment)

        return assessments

    def _generate_usage_limitations(
        self,
        card: ModelSafetyCard,
    ) -> List[UsageLimitation]:
        """生成使用限制"""
        limitations = []

        # 基于风险评估生成限制
        for assessment in card.risk_assessments:
            if assessment.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH, RiskLevel.CRITICAL]:
                limitation = UsageLimitation(
                    category=assessment.category.value,
                    description=assessment.description,
                    severity=assessment.risk_level.value,
                    recommendation="不建议在敏感场景使用，需要额外的安全措施",
                )
                limitations.append(limitation)

        # 添加通用限制
        general_limitations = [
            UsageLimitation(
                category="高风险决策",
                description="模型输出不应直接用于医疗、法律、金融等高风险决策",
                severity="high",
                recommendation="需要人工审核和专业验证",
            ),
            UsageLimitation(
                category="敏感信息处理",
                description="不应输入敏感个人信息或商业机密",
                severity="medium",
                recommendation="使用前进行数据脱敏",
            ),
            UsageLimitation(
                category="儿童安全",
                description="输出内容可能不适合儿童",
                severity="medium",
                recommendation="需要家长监督",
            ),
        ]

        limitations.extend(general_limitations)
        return limitations

    def _calculate_overall_score(self, card: ModelSafetyCard) -> float:
        """计算总体安全评分"""
        if not card.safety_metrics:
            return 0.5

        scores = [m.value for m in card.safety_metrics]
        return sum(scores) / len(scores)

    def _determine_risk_level(self, score: float) -> RiskLevel:
        """确定风险等级"""
        if score >= 0.9:
            return RiskLevel.VERY_LOW
        elif score >= 0.8:
            return RiskLevel.LOW
        elif score >= 0.6:
            return RiskLevel.MEDIUM
        elif score >= 0.4:
            return RiskLevel.HIGH
        elif score >= 0.2:
            return RiskLevel.VERY_HIGH
        else:
            return RiskLevel.CRITICAL

    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """分数转风险等级"""
        return self._determine_risk_level(1 - score)

    def _get_mitigation(self, category: SafetyCategory) -> str:
        """获取缓解措施"""
        mitigations = {
            SafetyCategory.HARMFUL_CONTENT: "部署内容过滤器和输出验证",
            SafetyCategory.PRIVACY: "实施 PII 检测和遮蔽机制",
            SafetyCategory.FAIRNESS: "进行偏见检测和公平性评估",
            SafetyCategory.SECURITY: "加强输入验证和越狱防护",
            SafetyCategory.RELIABILITY: "增加输出验证和一致性检查",
            SafetyCategory.TRANSPARENCY: "提供模型限制说明和不确定性指示",
        }
        return mitigations.get(category, "需要进一步评估")

    def _generate_recommendations(self, card: ModelSafetyCard) -> List[str]:
        """生成建议"""
        recommendations = []

        # 基于评分生成建议
        if card.overall_safety_score < 0.7:
            recommendations.append("建议在生产环境部署前进行额外的安全测试")

        if card.overall_safety_score < 0.5:
            recommendations.append("强烈建议不要在敏感场景使用此模型")

        # 基于风险评估生成建议
        high_risks = [
            a for a in card.risk_assessments
            if a.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH, RiskLevel.CRITICAL]
        ]
        if high_risks:
            recommendations.append(
                f"存在 {len(high_risks)} 个高风险领域，建议实施针对性防御措施"
            )

        # 通用建议
        recommendations.extend([
            "定期进行安全评估和更新",
            "监控模型输出并收集用户反馈",
            "建立应急响应机制处理安全问题",
            "对敏感应用场景实施人工审核流程",
        ])

        return recommendations


# ============ 导出 ============

__all__ = [
    "RiskLevel",
    "SafetyCategory",
    "SafetyMetric",
    "RiskAssessment",
    "UsageLimitation",
    "SafetyTestResult",
    "ModelSafetyCard",
    "SafetyCardGenerator",
]