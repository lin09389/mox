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
    ScenarioTestResult,
    DefenseReportGenerator,
)

# 兼容性别名 (deprecated — 请使用正确的类名)
DefenseTestResult = ScenarioTestResult  # deprecated: use ScenarioTestResult
KeywordDetector = InputFilter  # deprecated: use InputFilter
DefensePipeline = InputFilter  # deprecated: use InputFilter
RealPerplexityFilter = PerplexityFilter  # deprecated: use PerplexityFilter
EnhancedInputFilter = InputFilter  # deprecated: use InputFilter

# 语义防火墙与 Constitutional AI
try:
    from .semantic_firewall import SemanticFirewall
    from .constitutional_ai import ConstitutionalAI
except ImportError as e:
    import logging
    _init_log = logging.getLogger(__name__)
    _init_log.warning("SemanticFirewall/ConstitutionalAI not available: %s", e)
    SemanticFirewall = None
    ConstitutionalAI = None

_defense_load_failures: list[tuple[str, Exception]] = []
_defenses_loaded = False


def _discover_defenses():
    """动态加载所有防御子模块以触发注册"""
    global _defenses_loaded
    if _defenses_loaded:
        return
    _defenses_loaded = True

    import logging
    _log = logging.getLogger(__name__)
    package_dir = str(Path(__file__).parent)
    for _, module_name, _ in pkgutil.iter_modules([package_dir]):
        if module_name not in ["base", "registry"]:
            try:
                __import__(f"mox.defense.{module_name}")
            except Exception as e:
                _defense_load_failures.append((module_name, e))
                _log.warning(
                    "Failed to load defense module '%s': %s. "
                    "This defense type will NOT be available in the registry.",
                    module_name, e,
                )

    n_ok = len(DEFENSE_REGISTRY.registered_names)
    n_fail = len(_defense_load_failures)
    if n_fail:
        _log.warning(
            "Defense registry loaded with %d defenses (%d modules failed: %s)",
            n_ok, n_fail, [name for name, _ in _defense_load_failures],
        )
    else:
        _log.info("Defense registry loaded successfully: %d defenses registered", n_ok)


# Auto-load on first import.
_discover_defenses()


def init_defense_modules() -> None:
    """Explicitly trigger defense module loading (idempotent)."""
    global _defenses_loaded
    _defenses_loaded = False
    _defense_load_failures.clear()
    _discover_defenses()


def verify_registry() -> list[str]:
    """Return names of defense modules that failed to load."""
    return [name for name, _ in _defense_load_failures]

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
    "ScenarioTestResult",
    "DefenseTestResult",
    "verify_registry",
]
