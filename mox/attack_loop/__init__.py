"""Attack Loop 模块 - 攻击循环测试引擎

提供配置驱动的批量攻击测试能力，支持：
- 多模型、多攻击类型、多提示的组合测试
- 断点续跑（CheckpointManager）
- 配置驱动（YAML/JSON）
- 多种报告格式输出（JSON/CSV/TXT/HTML）
- 随机提示生成
- 进度回调与并发控制

攻击类型注册表统一由 mox.attacks.registry 管理。
如需查询所有可用攻击类型，请使用 mox.attacks.registry.get_all_attack_types()。
"""

from .core import (
    # 数据结构（从主注册表透传，方便外部统一引用）
    AttackTypeInfo,
    AttackCategory,
    AttackTestResult,
    LoopConfig,
    TestStatistics,

    # 核心组件
    AttackExecutor,
    ReportGenerator,
    CheckpointManager,
    PromptGenerator,

    # 统一运行器
    AttackLoopRunner,

    # 工具函数
    setup_logger,
    create_config_from_args,
    print_statistics,
)

__all__ = [
    # 数据结构
    "AttackTypeInfo",
    "AttackCategory",
    "AttackTestResult",
    "LoopConfig",
    "TestStatistics",

    # 核心组件
    "AttackExecutor",
    "ReportGenerator",
    "CheckpointManager",
    "PromptGenerator",

    # 统一运行器
    "AttackLoopRunner",

    # 工具函数
    "setup_logger",
    "create_config_from_args",
    "print_statistics",
]
