"""命令行工具 - 简化操作"""

import asyncio
import argparse

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from mox.core import (
    LLMFactory,
    AttackType,
    AttackPayload,
)
from mox.attacks import (
    PromptInjectionAttack,
    JailbreakAttack,
    GCGAttack,
    AutoDANAttack,
    AttackConfig,
    TAPAttack,
    MultiTurnJailbreakAttack,
    CrescendoAttack,
    TAPConfig,
    RAGContextInjectionAttack,
    AgentToolManipulationAttack,
)
from mox.defense import (
    InputFilter,
    OutputFilter,
)
from mox.defense.llm_judge import LLMJudge, SafetyCoTDefense, JudgmentType
from mox.evaluation import (
    BenchmarkDataset,
)

console = Console()


def create_attack(attack_type: str, model: str, max_iterations: int):
    llm = LLMFactory.create_from_model_name(model)

    attack_map = {
        "prompt_injection": PromptInjectionAttack,
        "jailbreak": JailbreakAttack,
        "gcg": GCGAttack,
        "autodan": AutoDANAttack,
        "tap": TAPAttack,
        "multi_turn": MultiTurnJailbreakAttack,
        "crescendo": CrescendoAttack,
        "rag": RAGContextInjectionAttack,
        "agent": AgentToolManipulationAttack,
    }

    attack_class = attack_map.get(attack_type, PromptInjectionAttack)

    if attack_type in ["tap", "multi_turn"]:
        config = TAPConfig(max_iterations=max_iterations, max_depth=5)
    else:
        config = AttackConfig(max_iterations=max_iterations)

    return attack_class(target_llm=llm, config=config)


async def run_single_attack(args):
    console.print(
        Panel.fit(
            "[bold blue]Mox - 大模型对抗攻防平台[/bold blue]\n"
            f"攻击类型: {args.attack_type}\n"
            f"目标模型: {args.model}",
            title="⚔️ 攻击测试",
        )
    )

    attack = create_attack(args.attack_type, args.model, args.max_iterations)

    payload = AttackPayload(
        attack_type=AttackType(args.attack_type),
        prompt=args.prompt,
        target_behavior=args.target,
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("执行攻击中...", total=None)
        outcome = await attack.generate_attack(payload)
        progress.remove_task(task)

    table = Table(title="攻击结果")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="green")

    table.add_row("结果", outcome.result.value)
    table.add_row("成功分数", f"{outcome.success_score:.2f}")
    table.add_row("迭代次数", str(outcome.iterations))

    console.print(table)

    console.print("\n[bold]对抗提示词:[/bold]")
    console.print(Panel(outcome.adversarial_prompt, expand=False))

    console.print("\n[bold]模型响应:[/bold]")
    console.print(Panel(outcome.response[:500], expand=False))


async def run_defense_scan(args):
    console.print(
        Panel.fit(
            f"[bold blue]Mox - 大模型对抗攻防平台[/bold blue]\n扫描类型: {args.scan_type}",
            title="🛡️ 防御检测",
        )
    )

    if args.scan_type == "input":
        detector = InputFilter()
    else:
        detector = OutputFilter()

    result = await detector.detect(args.text)

    table = Table(title="检测结果")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="green")

    table.add_row("是否恶意", "是" if result.is_malicious else "否")
    table.add_row("置信度", f"{result.confidence:.2f}")
    table.add_row("检测到的模式", ", ".join(result.detected_patterns) or "无")

    console.print(table)

    if result.is_malicious and result.sanitized_input:
        console.print("\n[bold]净化后文本:[/bold]")
        console.print(Panel(result.sanitized_input, expand=False))


async def run_benchmark(args):
    console.print(
        Panel.fit(
            "[bold blue]Mox - 大模型对抗攻防平台[/bold blue]\n"
            f"数据集: {args.dataset}\n"
            f"攻击类型: {args.attack_type}\n"
            f"目标模型: {args.model}",
            title="📊 基准测试",
        )
    )

    attack = create_attack(args.attack_type, args.model, args.max_iterations)
    benchmark = BenchmarkDataset()
    payloads = benchmark.get_attack_payloads(args.dataset)[: args.max_cases]

    results = []
    with Progress(console=console) as progress:
        task = progress.add_task("运行测试...", total=len(payloads))

        for i, payload in enumerate(payloads):
            outcome = await attack.generate_attack(payload)
            results.append(
                {
                    "case": i + 1,
                    "result": outcome.result.value,
                    "score": outcome.success_score,
                }
            )
            progress.advance(task)

    successful = sum(1 for r in results if r["result"] == "success")
    total = len(results)

    table = Table(title="测试结果汇总")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="green")

    table.add_row("总测试数", str(total))
    table.add_row("成功攻击数", str(successful))
    table.add_row("失败攻击数", str(total - successful))
    table.add_row("攻击成功率", f"{successful / total * 100:.1f}%")

    console.print(table)

    detail_table = Table(title="详细结果")
    detail_table.add_column("用例", style="cyan")
    detail_table.add_column("结果", style="green")
    detail_table.add_column("分数", style="yellow")

    for r in results:
        detail_table.add_row(str(r["case"]), r["result"], f"{r['score']:.2f}")

    console.print(detail_table)


async def run_llm_judge_test(args):
    console.print(
        Panel.fit(
            f"[bold blue]Mox - LLM-as-Judge 评估[/bold blue]\n待检测文本: {args.text[:50]}...",
            title="⚖️ 安全评估",
        )
    )

    llm = LLMFactory.create_from_model_name(args.model)
    judge = LLMJudge(llm, judgment_type=JudgmentType.SAFETY)

    result = await judge.judge(args.text, args.response or "")

    table = Table(title="评估结果")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="green")

    table.add_row("是否安全", "是" if result.is_safe else "否")
    table.add_row("置信度", f"{result.confidence:.2f}")
    table.add_row("有害类别", result.category.value if result.category else "无")
    table.add_row("判断理由", result.reasoning[:100])

    console.print(table)


async def run_safety_cot(args):
    console.print(
        Panel.fit(
            f"[bold blue]Mox - Safety-CoT 防御[/bold blue]\n用户输入: {args.text[:50]}...",
            title="🛡️ 安全推理",
        )
    )

    llm = LLMFactory.create_from_model_name(args.model)
    defense = SafetyCoTDefense(llm)

    result = await defense.check_and_respond(args.text)

    table = Table(title="结果")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="green")

    table.add_row("是否安全", "是" if result["is_safe"] else "否")
    table.add_row("使用CoT", "是" if result["uses_cot"] else "否")

    console.print(table)
    console.print("\n[bold]模型响应:[/bold]")
    console.print(Panel(result["response"][:500], expand=False))


async def run_quick_test(args):
    """快速测试 - 简化的单命令测试"""
    console.print(
        Panel.fit(
            f"[bold green]⚡ Mox 快速测试[/bold green]\n模式: {args.mode}",
            title="快速测试",
        )
    )

    llm = LLMFactory.create_from_model_name(args.model)

    if args.mode == "attack":
        # 快速攻击测试
        attack = MultiTurnJailbreakAttack(target_llm=llm)
        payload = AttackPayload(
            attack_type=AttackType.JAILBREAK,
            prompt=args.prompt,
            target_behavior=args.target or "test",
        )
        outcome = await attack.generate_attack(payload)

        console.print(f"\n[bold]攻击结果:[/bold] {outcome.result.value}")
        console.print(f"[bold]成功分数:[/bold] {outcome.success_score:.2f}")

    elif args.mode == "defense":
        # 快速防御测试
        defense = InputFilter()
        result = await defense.detect(args.prompt)

        console.print(f"\n[bold]检测结果:[/bold] {'恶意' if result.is_malicious else '安全'}")
        console.print(f"[bold]置信度:[/bold] {result.confidence:.2f}")

    elif args.mode == "judge":
        # 快速判断
        judge = LLMJudge(llm)
        result = await judge.judge(args.prompt, args.target or "")

        console.print(f"\n[bold]安全:[/bold] {'是' if result.is_safe else '否'}")
        console.print(f"[bold]置信度:[/bold] {result.confidence:.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="Mox v0.3.0 - 大模型对抗攻防平台 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
支持的攻击类型:
  prompt_injection  - 提示词注入
  jailbreak        - 越狱攻击
  gcg              - 基于梯度的攻击
  autodan          - 自动DAN
  tap              - 目标对齐提示
  multi_turn       - 多轮对话攻击
  crescendo        - 渐进式攻击
  rag              - RAG系统攻击
  agent            - Agent工具滥用

支持的模型:
  OpenAI:    gpt-4, gpt-3.5-turbo, o1, o3
  Anthropic: claude-3-opus, claude-3-sonnet
  MiniMax:   abab2.5-chat, abab6.5s-chat
  DeepSeek:  deepseek-chat, deepseek-coder
  Cohere:    command-r-plus
  Groq:      llama-3.1-70b-versatile
  本地:      qwen3:4b, llama3:8b, mistral
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    attack_parser = subparsers.add_parser("attack", help="运行攻击测试")
    attack_parser.add_argument(
        "--type",
        "-t",
        dest="attack_type",
        default="prompt_injection",
        choices=[
            "prompt_injection",
            "jailbreak",
            "gcg",
            "autodan",
            "tap",
            "multi_turn",
            "crescendo",
            "rag",
            "agent",
        ],
        help="攻击类型",
    )
    attack_parser.add_argument("--model", "-m", default="gpt-4", help="目标模型")
    attack_parser.add_argument("--prompt", "-p", required=True, help="攻击提示词")
    attack_parser.add_argument("--target", required=True, help="目标行为")
    attack_parser.add_argument("--max-iter", type=int, default=10, help="最大迭代次数")

    defense_parser = subparsers.add_parser("defense", help="运行防御检测")
    defense_parser.add_argument(
        "--scan-type", choices=["input", "output"], default="input", help="扫描类型"
    )
    defense_parser.add_argument("--text", "-t", required=True, help="待检测文本")

    benchmark_parser = subparsers.add_parser("benchmark", help="运行基准测试")
    benchmark_parser.add_argument(
        "--dataset",
        "-d",
        default="advbench",
        choices=["advbench", "harmbench", "harmbench_standard"],
        help="测试数据集",
    )
    benchmark_parser.add_argument(
        "--attack-type",
        "-a",
        default="prompt_injection",
        choices=["prompt_injection", "jailbreak", "tap", "multi_turn", "crescendo"],
        help="攻击类型",
    )
    benchmark_parser.add_argument("--model", "-m", default="gpt-4", help="目标模型")
    benchmark_parser.add_argument("--max-cases", type=int, default=5, help="最大测试用例数")

    judge_parser = subparsers.add_parser("judge", help="LLM-as-Judge 评估")
    judge_parser.add_argument("--text", "-t", required=True, help="原始文本")
    judge_parser.add_argument("--response", "-r", default="", help="模型响应")
    judge_parser.add_argument("--model", "-m", default="gpt-4", help="判断模型")

    cot_parser = subparsers.add_parser("cot", help="Safety-CoT 防御")
    cot_parser.add_argument("--text", "-t", required=True, help="用户输入")
    cot_parser.add_argument("--model", "-m", default="gpt-4", help="模型")

    quick_parser = subparsers.add_parser("quick", help="快速测试 (推荐)")
    quick_parser.add_argument(
        "--mode", "-m", required=True, choices=["attack", "defense", "judge"], help="测试模式"
    )
    quick_parser.add_argument("--prompt", "-p", required=True, help="提示词")
    quick_parser.add_argument("--target", "-t", help="目标行为 (attack模式)")
    quick_parser.add_argument("--model", default="gpt-4", help="模型")

    args = parser.parse_args()

    if args.command == "attack":
        asyncio.run(run_single_attack(args))
    elif args.command == "defense":
        asyncio.run(run_defense_scan(args))
    elif args.command == "benchmark":
        asyncio.run(run_benchmark(args))
    elif args.command == "judge":
        asyncio.run(run_llm_judge_test(args))
    elif args.command == "cot":
        asyncio.run(run_safety_cot(args))
    elif args.command == "quick":
        asyncio.run(run_quick_test(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
