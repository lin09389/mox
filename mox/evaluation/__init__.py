"""
评估模块

三层评估架构:
- 基础指标层 (evaluator.py): BasicAttackEvaluator, DefenseEvaluator, RobustnessEvaluator
- 增强评估层 (attack_evaluator.py): AttackEvaluator — 多维度语义/LLM 评分
- 统一编排层 (framework.py): UnifiedEvaluator — 场景编排与报告生成
"""

# --- 基础指标层 ---
from mox.evaluation.evaluator import (
    EvaluationMetrics,
    AttackTypeMetrics,
    BasicAttackEvaluator,
    DefenseEvaluator,
    RobustnessEvaluator,
    BenchmarkRunner,
)

# --- 基准测试 (v1 legacy + v2 canonical) ---
from mox.evaluation.benchmarks import (
    LegacyBenchmarkCase as BenchmarkCase,
    HarmBenchCase,
    BenchmarkDataset,
    ADVBENCH_CASES,
    HARMBENCH_CASES,
    BenchmarkType,
    HarmCategory,
    Severity,
    BenchmarkCase as BenchmarkCaseV2,
    BenchmarkResult,
    AgentBenchmarkCase,
    MMSafetyBenchmarkCase,
    HARMBENCH_V2_CASES,
    AGENTBENCH_CASES,
    MM_SAFETY_BENCH_CASES,
    SAFETY_BENCH_CASES,
    RED_TEAM_BENCH_CASES,
    BenchmarkRunner as BenchmarkRunnerV2,
    BenchmarkEvaluator,
)

# --- 可视化 ---
from mox.evaluation.visualization import (
    ChartData,
    ReportGenerator,
    create_quick_report,
)

# --- 增强评估层 ---
from mox.evaluation.attack_evaluator import (
    AttackEvaluator as EnhancedAttackEvaluator,
    LLMAttackEvaluator,
    AdaptiveEvaluator,
    AttackEvaluationResult,
    AttackEvaluationConfig,
    EvaluationDimension,
    create_evaluator,
)

# --- 攻击成功率评估（canonical types）---
from mox.evaluation.attack_success import (
    AttackSuccessResult,
    AttackSuccessEvaluator,
    KeywordOverlapEvaluator as AttackSuccessKeywordEvaluator,
    evaluate_attack_success,
    is_attack_successful,
)

# --- 困惑度和 LLM Judge ---
from mox.evaluation.perplexity_judge import (
    AccuratePerplexityCalculator,
    PerplexityConfig,
    PerplexityResult,
    StableLLMJudge,
    LLMJudgeConfig,
    JudgeEvaluation,
    ComprehensiveEvaluator,
)

from mox.evaluation.judge import (
    LLMJudge,
    MultiDimensionJudge,
    JudgeConfig,
    JudgeResult,
    JudgeMode,
)

# --- 红队 ---
from mox.evaluation.redteam import (
    RedTeamOrchestrator,
    RedTeamScenario,
    RedTeamResult,
    RedTeamReportGenerator,
    AttackTechnique,
)

# --- 统一编排层 ---
from mox.evaluation.framework import (
    UnifiedEvaluator,
    EvaluationScenario,
    EvaluationType,
    EvaluationStatus,
    EvaluationConfig,
    EvaluationResult,
)

# --- 模型安全卡片 ---
from mox.evaluation.safety_card import (
    RiskLevel,
    SafetyCategory,
    SafetyMetric,
    RiskAssessment,
    UsageLimitation,
    SafetyTestResult,
    ModelSafetyCard,
    SafetyCardGenerator,
)

# --- 数据集管理 ---
from mox.evaluation.datasets import (
    DatasetFormat,
    DatasetMetadata,
    BenchmarkCase as BenchmarkCaseDataset,
    HarmBenchCase as HarmBenchCaseDataset,
    DatasetManager,
    get_dataset_manager,
    load_dataset,
    filter_dataset,
    sample_dataset,
    list_datasets,
    get_dataset_statistics,
)

# Public API: AttackEvaluator 指向增强评估层
AttackEvaluator = EnhancedAttackEvaluator

__all__ = [
    # 基础指标层
    "EvaluationMetrics",
    "AttackTypeMetrics",
    "BasicAttackEvaluator",
    "DefenseEvaluator",
    "RobustnessEvaluator",
    "BenchmarkRunner",
    # 基准测试
    "BenchmarkCase",
    "HarmBenchCase",
    "BenchmarkDataset",
    "ADVBENCH_CASES",
    "HARMBENCH_CASES",
    "BenchmarkType",
    "HarmCategory",
    "Severity",
    "BenchmarkCaseV2",
    "BenchmarkResult",
    "AgentBenchmarkCase",
    "MMSafetyBenchmarkCase",
    "HARMBENCH_V2_CASES",
    "AGENTBENCH_CASES",
    "MM_SAFETY_BENCH_CASES",
    "SAFETY_BENCH_CASES",
    "RED_TEAM_BENCH_CASES",
    "BenchmarkRunnerV2",
    "BenchmarkEvaluator",
    # 可视化
    "ChartData",
    "ReportGenerator",
    "create_quick_report",
    # 增强评估层
    "AttackEvaluator",
    "LLMAttackEvaluator",
    "AdaptiveEvaluator",
    "AttackEvaluationResult",
    "AttackEvaluationConfig",
    "EvaluationDimension",
    "create_evaluator",
    # 困惑度和 Judge
    "AccuratePerplexityCalculator",
    "PerplexityConfig",
    "PerplexityResult",
    "StableLLMJudge",
    "LLMJudgeConfig",
    "JudgeEvaluation",
    "ComprehensiveEvaluator",
    "LLMJudge",
    "MultiDimensionJudge",
    "JudgeConfig",
    "JudgeResult",
    "JudgeMode",
    # 红队
    "RedTeamOrchestrator",
    "RedTeamScenario",
    "RedTeamResult",
    "RedTeamReportGenerator",
    "AttackTechnique",
    # 统一编排层
    "UnifiedEvaluator",
    "EvaluationScenario",
    "EvaluationType",
    "EvaluationStatus",
    "EvaluationConfig",
    "EvaluationResult",
    # 模型安全卡片
    "RiskLevel",
    "SafetyCategory",
    "SafetyMetric",
    "RiskAssessment",
    "UsageLimitation",
    "SafetyTestResult",
    "ModelSafetyCard",
    "SafetyCardGenerator",
    # 数据集管理
    "DatasetFormat",
    "DatasetMetadata",
    "BenchmarkCaseDataset",
    "HarmBenchCaseDataset",
    "DatasetManager",
    "get_dataset_manager",
    "load_dataset",
    "filter_dataset",
    "sample_dataset",
    "list_datasets",
    "get_dataset_statistics",
]