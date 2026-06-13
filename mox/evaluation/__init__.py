"""
评估模块

提供攻击效果评估、困惑度计算、LLM Judge、基准测试等功能
"""

# 从原有评估器导入
from mox.evaluation.evaluator import (
    EvaluationMetrics,
    AttackTypeMetrics,
    DefenseEvaluator,
    RobustnessEvaluator,
    BenchmarkRunner,
)

# 从基准测试导入
from mox.evaluation.benchmarks import (
    BenchmarkCase,
    HarmBenchCase,
    BenchmarkDataset,
    ADVBENCH_CASES,
    HARMBENCH_CASES,
)

# 从可视化导入
from mox.evaluation.visualization import (
    ChartData,
    ReportGenerator,
    create_quick_report,
)

# 新增：改进的攻击评估器
from mox.evaluation.attack_evaluator import (
    AttackEvaluator as EnhancedAttackEvaluator,
    LLMAttackEvaluator,
    AdaptiveEvaluator,
    EvaluationResult,
    EvaluationConfig,
    EvaluationDimension,
    create_evaluator,
)

# 新增：困惑度和 LLM Judge
from mox.evaluation.perplexity_judge import (
    AccuratePerplexityCalculator,
    PerplexityConfig,
    PerplexityResult,
    StableLLMJudge,
    LLMJudgeConfig,
    JudgeEvaluation,
    ComprehensiveEvaluator,
)

# 新增：LLM Judge 评判器
from mox.evaluation.judge import (
    LLMJudge,
    MultiDimensionJudge,
    JudgeConfig,
    JudgeResult,
    JudgeMode,
)

# 新增：红队模块
from mox.evaluation.redteam import (
    RedTeamOrchestrator,
    RedTeamScenario,
    RedTeamResult,
    RedTeamReportGenerator,
    AttackTechnique,
)

# 新增：统一评估框架
from mox.evaluation.framework import (
    UnifiedEvaluator,
    EvaluationScenario,
    EvaluationType,
    EvaluationStatus,
)

# 新增：最新评估基准 (2025)
from mox.evaluation.benchmarks_v2 import (
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

# 新增：模型安全卡片
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

# 新增：数据集管理
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

# 为了向后兼容，使用原有的名称
AttackEvaluator = EnhancedAttackEvaluator

__all__ = [
    # 原有评估器
    "EvaluationMetrics",
    "AttackTypeMetrics",
    "DefenseEvaluator",
    "RobustnessEvaluator",
    "BenchmarkRunner",
    # 基准测试
    "BenchmarkCase",
    "HarmBenchCase",
    "BenchmarkDataset",
    "ADVBENCH_CASES",
    "HARMBENCH_CASES",
    # 可视化
    "ChartData",
    "ReportGenerator",
    "create_quick_report",
    # 改进的攻击评估
    "AttackEvaluator",
    "LLMAttackEvaluator",
    "AdaptiveEvaluator",
    "EvaluationResult",
    "EvaluationConfig",
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
    # LLM Judge 评判器
    "LLMJudge",
    "MultiDimensionJudge",
    "JudgeConfig",
    "JudgeResult",
    "JudgeMode",
    # 红队模块
    "RedTeamOrchestrator",
    "RedTeamScenario",
    "RedTeamResult",
    "RedTeamReportGenerator",
    "AttackTechnique",
    # 统一评估框架
    "UnifiedEvaluator",
    "EvaluationConfig",
    "EvaluationScenario",
    "EvaluationResult",
    "EvaluationType",
    "EvaluationStatus",
    # 最新评估基准 (2025)
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
