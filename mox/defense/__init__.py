"""Defense module exports

输入检测分工:
- input_filter: 入口级通用检测 (正则/关键词/困惑度/编码)
- injection_detector: Prompt Injection 语义与多层编码检测
- semantic_firewall: 意图分类与风险评分 (语义级)
"""

from .base import BaseDefense, DefenseConfig

# 入口级通用输入过滤
from .input_filter import (
    InputFilter,
    PerplexityFilter,
    KeywordDetector,
    MaliciousPattern,
    MALICIOUS_PATTERNS,
    RealPerplexityFilter,
    EncodingDetector,
    DefensePipeline,
)
from .output_filter import (
    OutputFilter,
    ContentModerator,
    OutputPattern,
    DANGEROUS_OUTPUT_PATTERNS,
)
from .hardening import (
    SystemPromptHardening,
    HardeningPipeline,
    HardeningRule,
    HARDENING_RULES,
)
from .llm_judge import (
    LLMJudge,
    SafetyJudgment,
    JudgmentType,
    HarmCategory,
    DefenseEvaluator,
    SafetyCoTDefense,
)
from .hallucination import (
    HallucinationDetector,
    HallucinationResult,
    HallucinationType,
    BiasDetector,
    BiasResult,
)

# Prompt Injection 专项检测
from .injection_detector import (
    PromptInjectionDetector,
    MultiLayerInjectionDetector,
    InjectionType,
)

# 新增：统一防御框架
from mox.defense.orchestrator import (
    DefenseOrchestrator,
    DefenseScenario,
    DefenseResult,
    DefenseReportGenerator,
    DefenseType,
)

# 新增：Constitutional AI 防御
from .constitutional_ai import (
    ConstitutionalAI,
    ConstitutionalPrinciple,
    PrincipleCategory,
    PrincipleEnforcer,
    SelfCorrectionPipeline,
    DEFAULT_PRINCIPLES,
)

# 语义级意图分类与风险评分
from .semantic_firewall import (
    SemanticFirewall,
    IntentClassifier,
    RiskScorer,
    ContextualAnalyzer,
    IntentCategory,
    RiskLevel,
    IntentAnalysis,
    RiskAssessment,
)

# 输出检测：output_filter (快速正则) + output_validator (PII/敏感信息精细检测)
from .output_validator import (
    OutputValidator,
    OutputSanitizer,
    PIIDetector,
    SensitiveContentDetector,
    PIICategory,
    SensitiveCategory,
    PIIDetection,
    SensitiveDetection,
    OutputValidationResult,
)

__all__ = [
    "BaseDefense",
    "DefenseConfig",
    "InputFilter",
    "PerplexityFilter",
    "KeywordDetector",
    "MaliciousPattern",
    "MALICIOUS_PATTERNS",
    "RealPerplexityFilter",
    "EncodingDetector",
    "DefensePipeline",
    "OutputFilter",
    "ContentModerator",
    "OutputPattern",
    "DANGEROUS_OUTPUT_PATTERNS",
    "SystemPromptHardening",
    "HardeningPipeline",
    "HardeningRule",
    "HARDENING_RULES",
    "LLMJudge",
    "SafetyJudgment",
    "JudgmentType",
    "HarmCategory",
    "DefenseEvaluator",
    "SafetyCoTDefense",
    "HallucinationDetector",
    "HallucinationResult",
    "HallucinationType",
    "BiasDetector",
    "BiasResult",
    "PromptInjectionDetector",
    "MultiLayerInjectionDetector",
    "InjectionType",
    # 新增
    "DefenseOrchestrator",
    "DefenseScenario",
    "DefenseResult",
    "DefenseReportGenerator",
    "DefenseType",
    # Constitutional AI
    "ConstitutionalAI",
    "ConstitutionalPrinciple",
    "PrincipleCategory",
    "PrincipleEnforcer",
    "SelfCorrectionPipeline",
    "DEFAULT_PRINCIPLES",
    # Semantic Firewall
    "SemanticFirewall",
    "IntentClassifier",
    "RiskScorer",
    "ContextualAnalyzer",
    "IntentCategory",
    "RiskLevel",
    "IntentAnalysis",
    "RiskAssessment",
    # Output Validator
    "OutputValidator",
    "OutputSanitizer",
    "PIIDetector",
    "SensitiveContentDetector",
    "PIICategory",
    "SensitiveCategory",
    "PIIDetection",
    "SensitiveDetection",
    "OutputValidationResult",
]
