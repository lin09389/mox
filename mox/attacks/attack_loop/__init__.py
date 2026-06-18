"""攻击循环测试模块

提供完整的攻击循环测试能力，包括：
- 配置管理（AttackLoopConfig，支持 YAML/JSON 加载）
- 攻击执行器（AttackExecutor，基于统一攻击注册表）
- 检查点管理（CheckpointManager，支持断点续跑）
- 随机提示生成（PromptGenerator）
- 报告生成（ReportGenerator，支持 JSON/CSV/TXT/HTML）
- 运行器（AttackLoopRunner，完整编排）

基本用法::

    from mox.attacks.attack_loop import AttackLoopConfig, AttackLoopRunner

    config = AttackLoopConfig.from_yaml("config.yaml")
    runner = AttackLoopRunner(config)
    result = await runner.run()
"""

from .config import AttackLoopConfig
from .result import AttackTestResult, TestStatistics
from .executor import AttackExecutor
from .checkpoint import CheckpointManager
from .prompt_generator import PromptGenerator
from .report import ReportGenerator
from .runner import AttackLoopRunner, run_attack_loop, run_attack_loop_async

__all__ = [
    "AttackLoopConfig",
    "AttackTestResult",
    "TestStatistics",
    "AttackExecutor",
    "CheckpointManager",
    "PromptGenerator",
    "ReportGenerator",
    "AttackLoopRunner",
    "run_attack_loop",
    "run_attack_loop_async",
]
