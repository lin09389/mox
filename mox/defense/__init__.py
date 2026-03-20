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
    DefenseResult,
    DefenseReportGenerator,
    DefenseType,
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
]
