"""Defense module exports"""

from .base import BaseDefense, DefenseConfig
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
from .injection_detector import (
    PromptInjectionDetector,
    MultiLayerInjectionDetector,
    InjectionType,
)

# 新增：统一防御框架
from mox.defense.orchestrator import (
    DefenseOrchestrator,
    DefenseScenario,
    DefenseTestResult,
    DefenseReportGenerator,
    DefenseTestType,
)

DefenseResult = DefenseTestResult
DefenseType = DefenseTestType

# 新增：Constitutional AI 防御
from .constitutional_ai import (
    ConstitutionalAI,
    ConstitutionalPrinciple,
    PrincipleCategory,
    PrincipleEnforcer,
    SelfCorrectionPipeline,
    DEFAULT_PRINCIPLES,
)

# 新增：语义防火墙
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

# 新增：输出验证器
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
    "DefenseTestResult",
    "DefenseResult",
    "DefenseReportGenerator",
    "DefenseTestType",
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
