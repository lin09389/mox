"""命令行工具 - 简化操作"""

import asyncio
import argparse

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

from mox.core import LLMFactory
from mox.attacks.registry import get_registry, has_attack_type, list_attack_types
from mox.routes.services.attack_service import execute_registry_attack
from mox.defense import InputFilter, OutputFilter
from mox.defense.llm_judge import LLMJudge, SafetyCoTDefense, JudgmentType
from mox.evaluation import BenchmarkDataset

console = Console()

DEFAULT_CLI_ATTACK_TYPES = [
    "prompt_injection",
    "jailbreak",
    "gcg",
    "autodan",
    "tap",
    "multi_turn",
    "crescendo",
    "rag",
    "agent",
]


def get_attack_type_choices() -> list[str]:
    """Return all registry attack names and aliases for CLI argument validation."""
    registry = get_registry()
    return sorted(set(list_attack_types()) | set(registry.get_aliases().keys()))


def resolve_attack_type(attack_type: str) -> str:
    """Resolve CLI attack type via registry (supports aliases)."""
    if not has_attack_type(attack_type):
        raise ValueError(
            f"Unknown attack type: {attack_type}. "
            f"Use one of: {', '.join(DEFAULT_CLI_ATTACK_TYPES)}"
        )
    return get_registry().get_aliases().get(attack_type, attack_type)


def create_llm(model: str):
    return LLMFactory.create_from_model_name(model)


def get_max_iterations(args, default: int = 10) -> int:
    return getattr(args, "max_iter", getattr(args, "max_iterations", default))


async def run_registry_attack(
    attack_type: str,
    model: str,
    prompt: str,
    *,
    target_behavior: str,
    max_iterations: int = 10,
):
    llm = create_llm(model)
    resolved = resolve_attack_type(attack_type)
    return await execute_registry_attack(
        resolved,
        llm,
        prompt,
        target_behavior=target_behavior,
        max_iterations=max_iterations,
    )


def _attack_response_text(outcome) -> str:
    return getattr(outcome, "model_response", None) or getattr(outcome, "response", "")


async def run_single_attack(args):
    console.print(
        Panel.fit(
            "[bold blue]Mox - 大模型对抗攻防平台[/bold blue]\n"
            f"攻击类型: {args.attack_type}\n"
            f"目标模型: {args.model}",
            title="⚔️ 攻击测试",
        )
    )

    try:
        outcome = await run_registry_attack(
            args.attack_type,
            args.model,
            args.prompt,
            target_behavior=args.target,
            max_iterations=get_max_iterations(args),
        )
    except ValueError as exc:
        console.print(f"[bold red]错误:[/bold red] {exc}")
        return

    table = Table(title="攻击结果")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="green")

    table.add_row("结果", outcome.result.value)
    table.add_row("成功分数", f"{outcome.success_score:.2f}")
    table.add_row("迭代次数", str(outcome.iterations))

    console.print(table)

    console.print("\n[bold]对抗提示词:[/bold]")
    console.print(Panel(outcome.adversarial_prompt, expand=False))

    response_text = _attack_response_text(outcome)
    console.print("\n[bold]模型响应:[/bold]")
    console.print(Panel(response_text[:500], expand=False))


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

    try:
        resolve_attack_type(args.attack_type)
    except ValueError as exc:
        console.print(f"[bold red]错误:[/bold red] {exc}")
        return

    llm = create_llm(args.model)
    benchmark = BenchmarkDataset()
    payloads = benchmark.get_attack_payloads(args.dataset)[: args.max_cases]
    max_iterations = get_max_iterations(args)

    results = []
    with Progress(console=console) as progress:
        task = progress.add_task("运行测试...", total=len(payloads))

        for i, payload in enumerate(payloads):
            outcome = await execute_registry_attack(
                args.attack_type,
                llm,
                payload.prompt,
                target_behavior=payload.target_behavior,
                max_iterations=max_iterations,
            )
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
    table.add_row("攻击成功率", f"{successful / total * 100:.1f}%" if total else "0.0%")

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

    llm = create_llm(args.model)
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

    llm = create_llm(args.model)
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

    if args.mode == "attack":
        try:
            outcome = await run_registry_attack(
                "multi_turn",
                args.model,
                args.prompt,
                target_behavior=args.target or "test",
                max_iterations=10,
            )
        except ValueError as exc:
            console.print(f"[bold red]错误:[/bold red] {exc}")
            return

        console.print(f"\n[bold]攻击结果:[/bold] {outcome.result.value}")
        console.print(f"[bold]成功分数:[/bold] {outcome.success_score:.2f}")

    elif args.mode == "defense":
        defense = InputFilter()
        result = await defense.detect(args.prompt)

        console.print(f"\n[bold]检测结果:[/bold] {'恶意' if result.is_malicious else '安全'}")
        console.print(f"[bold]置信度:[/bold] {result.confidence:.2f}")

    elif args.mode == "judge":
        llm = create_llm(args.model)
        judge = LLMJudge(llm)
        result = await judge.judge(args.prompt, args.target or "")

        console.print(f"\n[bold]安全:[/bold] {'是' if result.is_safe else '否'}")
        console.print(f"[bold]置信度:[/bold] {result.confidence:.2f}")


def _attack_types_epilog() -> str:
    lines = ["常用攻击类型 (registry):"]
    registry = get_registry()
    for name in DEFAULT_CLI_ATTACK_TYPES:
        info = registry.get_attack_type(name)
        if info:
            lines.append(f"  {name:18} - {info.description}")
        else:
            lines.append(f"  {name}")
    lines.append(
        f"\n注册表共 {len(list_attack_types())} 种攻击，含别名共 {len(get_attack_type_choices())} 个 CLI 选项。"
    )
    return "\n".join(lines)


def main():
    attack_choices = get_attack_type_choices()
    benchmark_choices = [t for t in DEFAULT_CLI_ATTACK_TYPES if t in attack_choices]

    parser = argparse.ArgumentParser(
        description="Mox v0.3.0 - 大模型对抗攻防平台 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{_attack_types_epilog()}

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
        choices=attack_choices,
        help="攻击类型 (registry)",
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
        choices=benchmark_choices or attack_choices,
        help="攻击类型 (registry)",
    )
    benchmark_parser.add_argument("--model", "-m", default="gpt-4", help="目标模型")
    benchmark_parser.add_argument("--max-cases", type=int, default=5, help="最大测试用例数")
    benchmark_parser.add_argument("--max-iter", type=int, default=10, help="最大迭代次数")

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
