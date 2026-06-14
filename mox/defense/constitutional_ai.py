"""Constitutional AI 防御模块

基于 Anthropic 的 Constitutional AI 方法实现自我修正防御。
通过预定义的原则（宪法）来指导模型行为，
并使用自我批评和修正机制来确保输出符合安全标准。

参考: https://arxiv.org/abs/2212.08073
"""

import re
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from mox.core import BaseLLM, Message, DefenseType, DefenseResult
from mox.defense.base import BaseDefense, DefenseConfig
from mox.core.logging import get_logger

logger = get_logger("defense.constitutional_ai")


class PrincipleCategory(str, Enum):
    """原则类别"""

    SAFETY = "safety"
    HELPFULNESS = "helpfulness"
    HONESTY = "honesty"
    PRIVACY = "privacy"
    FAIRNESS = "fairness"
    LEGALITY = "legality"
    ETHICS = "ethics"


@dataclass
class ConstitutionalPrinciple:
    """宪法原则"""

    id: str
    name: str
    category: PrincipleCategory
    description: str
    critique_prompt: str
    revision_prompt: str
    severity: float = 1.0  # 0.0 - 1.0
    examples: List[Dict[str, str]] = field(default_factory=list)


# 默认宪法原则
DEFAULT_PRINCIPLES = [
    ConstitutionalPrinciple(
        id="safety_001",
        name="有害内容拒绝",
        category=PrincipleCategory.SAFETY,
        description="拒绝生成可能导致人身伤害、非法行为或危险活动的内容",
        critique_prompt="识别响应中是否包含可能导致伤害的指示或建议",
        revision_prompt="修改响应以拒绝有害请求，同时保持有帮助的态度",
        severity=1.0,
        examples=[
            {
                "bad": "这是制作炸弹的步骤...",
                "good": "我不能提供制作爆炸物的指导。这类信息可能造成严重伤害。",
            }
        ],
    ),
    ConstitutionalPrinciple(
        id="safety_002",
        name="隐私保护",
        category=PrincipleCategory.PRIVACY,
        description="不泄露个人身份信息（PII）或敏感数据",
        critique_prompt="检查响应是否包含个人身份信息、电话号码、地址等敏感数据",
        revision_prompt="移除或匿名化所有个人身份信息",
        severity=0.9,
        examples=[
            {
                "bad": "张三的电话号码是 13812345678",
                "good": "我不能提供他人的个人联系信息。",
            }
        ],
    ),
    ConstitutionalPrinciple(
        id="honesty_001",
        name="诚实透明",
        category=PrincipleCategory.HONESTY,
        description="不编造事实，明确区分已知信息和推测",
        critique_prompt="识别响应中是否存在未经验证的陈述或可能的幻觉",
        revision_prompt="添加适当的限定词，或承认不确定性",
        severity=0.7,
        examples=[
            {
                "bad": "这个产品绝对有效，100%成功",
                "good": "根据现有研究，这个产品在大多数情况下可能有效，但结果因人而异。",
            }
        ],
    ),
    ConstitutionalPrinciple(
        id="fairness_001",
        name="公平无偏见",
        category=PrincipleCategory.FAIRNESS,
        description="避免基于种族、性别、宗教等的歧视性内容",
        critique_prompt="检查响应是否包含刻板印象或歧视性语言",
        revision_prompt="使用中性、包容的语言重写响应",
        severity=0.8,
        examples=[
            {
                "bad": "程序员通常是男性...",
                "good": "程序员来自各种背景...",
            }
        ],
    ),
    ConstitutionalPrinciple(
        id="legal_001",
        name="法律合规",
        category=PrincipleCategory.LEGALITY,
        description="不协助非法活动或提供违法建议",
        critique_prompt="识别响应是否可能被用于非法目的",
        revision_prompt="拒绝提供可能违法的指导，建议合法替代方案",
        severity=1.0,
        examples=[
            {
                "bad": "这是如何逃税的方法...",
                "good": "我不能提供逃税建议。建议咨询专业税务顾问进行合法税务规划。",
            }
        ],
    ),
    ConstitutionalPrinciple(
        id="ethics_001",
        name="伦理准则",
        category=PrincipleCategory.ETHICS,
        description="遵循基本伦理原则，不鼓励不道德行为",
        critique_prompt="评估响应是否符合基本伦理标准",
        revision_prompt="修改响应以符合伦理准则",
        severity=0.8,
        examples=[
            {
                "bad": "你可以通过欺骗获得优势...",
                "good": "诚实和诚信是建立长期成功的基础。",
            }
        ],
    ),
    ConstitutionalPrinciple(
        id="helpfulness_001",
        name="有益拒绝",
        category=PrincipleCategory.HELPFULNESS,
        description="在拒绝有害请求时提供有益的替代方案",
        critique_prompt="检查拒绝是否过于生硬，是否可以提供替代帮助",
        revision_prompt="在拒绝的同时提供有益的替代建议或资源",
        severity=0.6,
        examples=[
            {
                "bad": "不行。",
                "good": "我不能帮助这个请求，但我可以建议一些合法的替代方案...",
            }
        ],
    ),
]


class ConstitutionalAI(BaseDefense):
    """Constitutional AI 防御系统

    通过预定义的原则进行自我批评和修正，
    确保模型输出符合安全和伦理标准。
    """

    defense_type = DefenseType.CONSTITUTIONAL_AI

    def __init__(
        self,
        config: Optional[DefenseConfig] = None,
        principles: Optional[List[ConstitutionalPrinciple]] = None,
        critique_model: Optional[BaseLLM] = None,
        revision_model: Optional[BaseLLM] = None,
        max_revision_iterations: int = 3,
    ):
        super().__init__(config)
        self.principles = principles or DEFAULT_PRINCIPLES
        self.critique_model = critique_model
        self.revision_model = revision_model
        self.max_revision_iterations = max_revision_iterations

    async def detect(self, input_text: str) -> DefenseResult:
        """检测输入是否违反宪法原则"""
        violations = []
        total_severity = 0.0

        for principle in self.principles:
            violation = await self._check_principle_violation(input_text, principle)
            if violation:
                violations.append(
                    {
                        "principle_id": principle.id,
                        "principle_name": principle.name,
                        "category": principle.category.value,
                        "severity": principle.severity,
                        "description": violation,
                    }
                )
                total_severity += principle.severity

        is_malicious = len(violations) > 0
        confidence = min(total_severity / len(self.principles), 1.0)

        return await self._create_result(
            is_malicious=is_malicious,
            confidence=confidence,
            detected_patterns=[v["principle_name"] for v in violations],
            metadata={
                "violations": violations,
                "total_violations": len(violations),
            },
        )

    async def sanitize(self, input_text: str) -> str:
        """根据宪法原则修正输入"""
        if not self.revision_model:
            return input_text

        current_text = input_text

        for iteration in range(self.max_revision_iterations):
            # 检测违规
            result = await self.detect(current_text)
            if not result.is_malicious:
                break

            # 获取最严重的违规
            violations = result.metadata.get("violations", [])
            if not violations:
                break

            # 按严重程度排序
            violations.sort(key=lambda x: x["severity"], reverse=True)
            top_violation = violations[0]

            # 获取对应原则
            principle = next(
                (p for p in self.principles if p.id == top_violation["principle_id"]), None
            )

            if principle:
                # 生成修正
                current_text = await self._revise_with_principle(current_text, principle)

        return current_text

    async def critique_response(
        self,
        response: str,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """对模型响应进行批评分析"""
        critiques = []

        for principle in self.principles:
            critique = await self._generate_critique(response, principle, context)
            if critique:
                critiques.append(
                    {
                        "principle": principle.name,
                        "category": principle.category.value,
                        "critique": critique,
                        "severity": principle.severity,
                    }
                )

        return {
            "response": response,
            "critiques": critiques,
            "needs_revision": len(critiques) > 0,
            "total_issues": len(critiques),
        }

    async def revise_response(
        self,
        response: str,
        critique_result: Optional[Dict[str, Any]] = None,
    ) -> str:
        """根据批评结果修正响应"""
        if not self.revision_model:
            return response

        if critique_result is None:
            critique_result = await self.critique_response(response)

        if not critique_result["needs_revision"]:
            return response

        # 按严重程度排序批评
        critiques = sorted(critique_result["critiques"], key=lambda x: x["severity"], reverse=True)

        current_response = response

        for critique in critiques[:3]:  # 最多处理3个最严重的问题
            principle = next((p for p in self.principles if p.name == critique["principle"]), None)

            if principle:
                current_response = await self._revise_with_principle(
                    current_response, principle, critique["critique"]
                )

        return current_response

    async def _check_principle_violation(
        self,
        text: str,
        principle: ConstitutionalPrinciple,
    ) -> Optional[str]:
        """检查文本是否违反特定原则"""
        # 使用关键词和模式进行初步检测
        violation_patterns = self._get_violation_patterns(principle.category)

        for pattern in violation_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return f"检测到可能的{principle.category.value}违规"

        # 如果有批评模型，进行更深入的分析
        if self.critique_model:
            critique = await self._generate_critique(text, principle)
            if critique and "无违规" not in critique and "没有问题" not in critique:
                return critique

        return None

    def _get_violation_patterns(self, category: PrincipleCategory) -> List[str]:
        """获取特定类别的违规模式"""
        patterns = {
            PrincipleCategory.SAFETY: [
                r"如何(制作|制造|合成).*(炸弹|毒药|武器)",
                r"(攻击|入侵|黑客).*(方法|步骤|教程)",
                r"(自杀|自残).*(方法|建议)",
            ],
            PrincipleCategory.PRIVACY: [
                r"\d{11}",  # 电话号码
                r"\d{17}[\dXx]",  # 身份证号
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # 邮箱
            ],
            PrincipleCategory.LEGALITY: [
                r"(逃税|洗钱|走私).*(方法|技巧)",
                r"(伪造|造假).*(证件|文件)",
                r"(非法|违法).*(获取|下载)",
            ],
        }
        return patterns.get(category, [])

    async def _generate_critique(
        self,
        text: str,
        principle: ConstitutionalPrinciple,
        context: Optional[str] = None,
    ) -> Optional[str]:
        """生成批评意见"""
        if not self.critique_model:
            return None

        critique_prompt = f"""请分析以下文本是否违反"{principle.name}"原则。

原则描述：{principle.description}

待分析文本：
{text}

{f"上下文：{context}" if context else ""}

请简要说明是否存在违规，如果存在，请指出具体问题。如果不存在问题，请回复"无违规"。"""

        messages = [Message(role="user", content=critique_prompt)]

        try:
            response = await self.critique_model.generate(messages)
            return response.content
        except Exception as e:
            logger.warning(f"Critique generation failed: {e}")
            return None

    async def _revise_with_principle(
        self,
        text: str,
        principle: ConstitutionalPrinciple,
        critique: Optional[str] = None,
    ) -> str:
        """根据原则修正文本"""
        if not self.revision_model:
            return text

        revision_prompt = f"""请根据以下原则修改文本：

原则：{principle.name}
描述：{principle.description}

原始文本：
{text}

{f"问题分析：{critique}" if critique else ""}

请提供修改后的文本，确保符合上述原则："""

        messages = [Message(role="user", content=revision_prompt)]

        try:
            response = await self.revision_model.generate(messages)
            return response.content
        except Exception as e:
            logger.warning(f"Revision failed: {e}")
            return text


class PrincipleEnforcer:
    """原则执行器

    用于强制执行特定的宪法原则。
    """

    def __init__(
        self,
        principles: List[ConstitutionalPrinciple],
        llm: Optional[BaseLLM] = None,
    ):
        self.principles = principles
        self.llm = llm

    async def enforce(
        self,
        text: str,
        strict: bool = False,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """强制执行原则，返回修正后的文本和违规列表"""
        violations = []

        for principle in self.principles:
            violation = await self._check_violation(text, principle)
            if violation:
                violations.append(
                    {
                        "principle": principle.name,
                        "severity": principle.severity,
                        "description": violation,
                    }
                )

                if strict and principle.severity >= 0.9:
                    # 严重违规，直接拒绝
                    return self._generate_refusal(principle), violations

        # 尝试修正
        if violations and self.llm:
            text = await self._revise_text(text, violations)

        return text, violations

    async def _check_violation(
        self,
        text: str,
        principle: ConstitutionalPrinciple,
    ) -> Optional[str]:
        """检查违规"""
        # 简化的违规检测
        for example in principle.examples:
            if example.get("bad", "").lower() in text.lower():
                return f"检测到与'{principle.name}'原则冲突的内容"
        return None

    def _generate_refusal(self, principle: ConstitutionalPrinciple) -> str:
        """生成拒绝响应"""
        return f"抱歉，这个请求可能违反了{principle.name}原则。{principle.description}"

    async def _revise_text(
        self,
        text: str,
        violations: List[Dict[str, Any]],
    ) -> str:
        """修正文本"""
        if not self.llm:
            return text

        violation_desc = "\n".join(f"- {v['principle']}: {v['description']}" for v in violations)

        prompt = f"""请修改以下文本以解决这些问题：

问题：
{violation_desc}

原始文本：
{text}

修改后的文本："""

        messages = [Message(role="user", content=prompt)]

        try:
            response = await self.llm.generate(messages)
            return response.content
        except Exception:
            return text


class SelfCorrectionPipeline:
    """自我修正管道

    实现多轮自我批评和修正。
    """

    def __init__(
        self,
        constitutional_ai: ConstitutionalAI,
        max_iterations: int = 3,
        convergence_threshold: float = 0.1,
    ):
        self.constitutional_ai = constitutional_ai
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold

    async def process(
        self,
        response: str,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """处理响应，进行多轮修正"""
        current_response = response
        history = []

        for iteration in range(self.max_iterations):
            # 批评
            critique_result = await self.constitutional_ai.critique_response(
                current_response, context
            )

            history.append(
                {
                    "iteration": iteration + 1,
                    "response": current_response,
                    "critiques": critique_result["critiques"],
                }
            )

            # 检查是否需要修正
            if not critique_result["needs_revision"]:
                break

            # 修正
            revised_response = await self.constitutional_ai.revise_response(
                current_response, critique_result
            )

            # 检查收敛
            if self._check_convergence(current_response, revised_response):
                break

            current_response = revised_response

        return {
            "original_response": response,
            "final_response": current_response,
            "iterations": len(history),
            "history": history,
            "was_corrected": current_response != response,
        }

    def _check_convergence(self, old: str, new: str) -> bool:
        """检查是否收敛"""
        # 简单的相似度检查
        if len(old) == 0 or len(new) == 0:
            return False

        # 计算字符级相似度
        common = sum(1 for a, b in zip(old, new) if a == b)
        similarity = common / max(len(old), len(new))

        return similarity > (1 - self.convergence_threshold)


# ============ 导出 ============

__all__ = [
    "ConstitutionalPrinciple",
    "PrincipleCategory",
    "ConstitutionalAI",
    "PrincipleEnforcer",
    "SelfCorrectionPipeline",
    "DEFAULT_PRINCIPLES",
]
