"""Red Team 测试脚本 - 使用本地模型"""

import asyncio
import sys
from mox.evaluation import RedTeamOrchestrator, RedTeamReportGenerator
from mox.core.llm import OllamaLLM


async def main():
    print("=" * 50)
    print("Red Team 安全评估测试")
    print("=" * 50)

    # 使用本地模型 (gemma3 或 qwen3)
    print("\n[1] 创建 LLM 实例...")
    model_name = "gemma3:4b"  # 可改为 "qwen3:4b"

    target_llm = OllamaLLM(
        model=model_name,
        base_url="http://localhost:11434/v1",
        temperature=0.7,
        max_tokens=2048,
    )
    attacker_llm = OllamaLLM(
        model=model_name,
        base_url="http://localhost:11434/v1",
        temperature=0.8,
        max_tokens=2048,
    )
    print(f"    模型: {model_name}")

    # 创建红队编排器
    print("\n[2] 创建红队编排器...")
    orchestrator = RedTeamOrchestrator(attacker_llm, target_llm, judge_mode="pattern")

    # 只运行基础场景
    orchestrator.scenarios = orchestrator.create_scenarios("basic")
    print(f"    场景数: {len(orchestrator.scenarios)}")

    # 运行场景
    print("\n[3] 运行红队测试...")
    print("-" * 50)

    results = []
    for i, scenario in enumerate(orchestrator.scenarios, 1):
        print(f"\n    [{i}/{len(orchestrator.scenarios)}] {scenario.name}")
        print(f"         技术: {scenario.technique.value}")
        print(f"         目标: {scenario.target_behavior[:50]}...")

        try:
            result = await orchestrator.run_scenario(scenario, max_attempts=1)
            results.append(result)

            status = "SUCCESS" if result.success else "BLOCKED"
            print(f"         结果: {status}")

        except Exception as e:
            print(f"         错误: {str(e)[:50]}")

        await asyncio.sleep(0.5)  # 避免过快请求

    # 生成报告
    print("\n" + "=" * 50)
    print("[4] 测试完成!")
    print("=" * 50)

    # 统计结果
    successful = sum(1 for r in results if r.success)
    total = len(results)

    print(f"\n总场景数: {total}")
    print(f"成功攻击: {successful}")
    print(f"被阻止: {total - successful}")
    print(f"成功率: {successful/total*100:.1f}%")

    # 保存报告
    print("\n[5] 保存报告...")
    RedTeamReportGenerator.save_report(results, "redteam_report.html", format="html")
    print("    已保存: redteam_report.html")

    RedTeamReportGenerator.save_report(results, "redteam_report.json", format="json")
    print("    已保存: redteam_report.json")

    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
