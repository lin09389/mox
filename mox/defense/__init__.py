"""防御模块统一入口

支持通过注册中心动态加载防御组件。
"""

import pkgutil
from pathlib import Path
from typing import Dict, Any, Type, Optional

from .base import BaseDefense, DefenseConfig
from .registry import DEFENSE_REGISTRY, create_defense_instance

# 基础导出
from .input_filter import (
    InputFilter,
    StatisticalAnomalyFilter,
    PerplexityFilter,
    EnhancedDefenseConfig,
)
from .output_filter import (
    OutputFilter,
    ContentModerator,
    PIICategory,
)
from .hardening import (
    SystemPromptHardening,
    HardeningRule,
    HARDENING_RULES,
)
from .llm_judge import (
    LLMJudge,
    SafetyJudgment,
    JudgmentType,
    HarmCategory,
    SafetyCoTDefense,
)
from .injection_detector import (
    PromptInjectionDetector,
    InjectionType,
)
from .orchestrator import (
    DefenseOrchestrator,
    DefenseScenario,
    DefenseTestResult,
    DefenseReportGenerator,
)

# 兼容性别名
DefenseResult = DefenseTestResult
KeywordDetector = InputFilter # InputFilter now handles keyword detection
DefensePipeline = InputFilter # InputFilter acts as a single-entry filter now
RealPerplexityFilter = PerplexityFilter
EnhancedInputFilter = InputFilter

# 语义防火墙与 Constitutional AI
try:
    from .semantic_firewall import SemanticFirewall
    from .constitutional_ai import ConstitutionalAI
except ImportError:
    pass

def _discover_defenses():
    """动态加载所有防御子模块以触发注册"""
    package_dir = str(Path(__file__).parent)
    for _, module_name, _ in pkgutil.iter_modules([package_dir]):
        if module_name not in ["base", "registry"]:
            try:
                __import__(f"mox.defense.{module_name}")
            except Exception:
                pass

# 初始加载
_discover_defenses()

__all__ = [
    "BaseDefense",
    "DefenseConfig",
    "DEFENSE_REGISTRY",
    "create_defense_instance",
    "InputFilter",
    "StatisticalAnomalyFilter",
    "PerplexityFilter",
    "OutputFilter",
    "ContentModerator",
    "SystemPromptHardening",
    "LLMJudge",
    "SafetyCoTDefense",
    "PromptInjectionDetector",
    "DefenseOrchestrator",
    "DefenseResult",
]
