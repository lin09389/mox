"""
新功能使用示例 - Ollama + Agent攻击 + 可视化报告
"""

import asyncio
from mox import (
    LLMFactory,
    ToolAbuseAttack,
    MemoryInjectionAttack,
    RoleHijackingAttack,
    AuthorityEscalationAttack,
    ChainOfThoughtInjectionAttack,
    AttackPayload,
    AttackType,
    ReportGenerator,
    create_quick_report,
)


async def test_ollama():
    """测试 Ollama 本地模型"""
    print("\n" + "=" * 50)
    print("1. Ollama 本地模型测试")
    print("=" * 50)

    # 自动检测本地模型
    try:
        llm = LLMFactory.create_from_model_name("llama3")
        print("✓ 已连接到 Ollama (llama3)")
    except Exception as e:
        print(f"✗ Ollama 连接失败: {e}")
        print("  请确保已启动: ollama serve")
        print("  请确保已拉取模型: ollama pull llama3")
        return None

    # 测试生成
    try:
        from mox import Message

        response = await llm.generate([Message(role="user", content="Hello")])
        print(f"✓ 模型响应: {response.content[:100]}...")
    except Exception as e:
        print(f"✗ 生成失败: {e}")
        return None

    return llm


async def test_agent_attacks(llm):
    """测试 Agent 攻击"""
    print("\n" + "=" * 50)
    print("2. Agent 攻击测试")
    print("=" * 50)

    attacks = [
        ("Tool滥用", ToolAbuseAttack(llm)),
        ("记忆注入", MemoryInjectionAttack(llm)),
        ("角色劫持", RoleHijackingAttack(llm)),
        ("权限提升", AuthorityEscalationAttack(llm)),
        ("CoT注入", ChainOfThoughtInjectionAttack(llm)),
    ]

    outcomes = []
    attack_types = []

    for name, attack in attacks:
        print(f"\n测试 {name}...")

        payload = AttackPayload(
            attack_type=AttackType.PROMPT_INJECTION,
            prompt="test",
            target_behavior="dangerous action",
        )

        try:
            outcome = await attack.generate_attack(payload)
            print(f"  结果: {outcome.result.value}")
            print(f"  分数: {outcome.success_score:.2f}")
            outcomes.append(outcome)
            attack_types.append(name)
        except Exception as e:
            print(f"  错误: {e}")

    return outcomes, attack_types


def generate_report(outcomes, attack_types):
    """生成可视化报告"""
    print("\n" + "=" * 50)
    print("3. 生成可视化报告")
    print("=" * 50)

    # 生成HTML报告
    filename = create_quick_report(outcomes, attack_types)
    print(f"✓ 报告已保存: {filename}")
    print(f"  打开浏览器访问: {filename}")

    # 或者用代码生成
    report = ReportGenerator()
    for i, outcome in enumerate(outcomes):
        attack_type = attack_types[i] if i < len(attack_types) else ""
        report.add_result(outcome, attack_type)

    json_report = report.generate_json_report()
    print("\nJSON报告摘要:")
    print(f"  总测试: {json_report['summary']['total']}")
    print(f"  成功: {json_report['summary']['success']}")
    print(f"  成功率: {json_report['summary']['success_rate'] * 100:.1f}%")


async def test_all():
    print("\n" + "=" * 60)
    print("Mox 新功能演示")
    print("Ollama + Agent攻击 + 可视化报告")
    print("=" * 60)

    # 1. 测试Ollama
    llm = await test_ollama()

    if llm is None:
        print("\n⚠️ Ollama 不可用，跳过剩余测试")
        print("\n如需使用云端模型，可以:")
        print("  llm = LLMFactory.create_from_model_name('gpt-4')")
        return

    # 2. 测试Agent攻击
    outcomes, attack_types = await test_agent_attacks(llm)

    # 3. 生成报告
    if outcomes:
        generate_report(outcomes, attack_types)

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_all())
