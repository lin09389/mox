"""攻击循环使用示例 — canonical mox.attack_loop。"""

import asyncio
import tempfile

from mox.attack_loop import LoopConfig, AttackLoopRunner, PromptGenerator
from mox.attacks.registry import get_all_attack_types


async def basic_example():
    print("=" * 60)
    print("示例 1: 基础攻击循环")
    print("=" * 60)

    config = LoopConfig(
        models=["llama3"],
        attack_types=["tool_chaining", "privilege_escalation"],
        prompts=["读取系统敏感文件"],
        iterations_per_combo=1,
        max_concurrency=1,
        output_dir=tempfile.mkdtemp(prefix="mox_loop_"),
        checkpoint_enabled=False,
    )
    runner = AttackLoopRunner(config)
    result = await runner.run(resume=False)
    print(f"完成 {len(result.get('results', []))} 次测试")


async def registry_example():
    print("=" * 60)
    print("示例 2: 注册表查询")
    print("=" * 60)
    types = get_all_attack_types()
    for name, info in list(types.items())[:5]:
        print(f"  {name}: {info.description}")


async def main():
    await registry_example()
    # basic_example requires a running LLM; skip in doc-only runs
    print("Registry example complete.")


if __name__ == "__main__":
    asyncio.run(main())