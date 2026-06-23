"""Registry-backed attack execution helpers for API routes."""

from typing import Any, Dict, Optional

from mox.core import AttackPayload, AttackType, BaseLLM, AttackOutcome
from mox.core.agent_runtime import analyze_agent_tool_response
from mox.attacks.registry import create_attack_instance, has_attack_type

AGENT_RUNTIME_ATTACK_KEYS = frozenset(
    {
        "tool_abuse",
        "agent_tool_manipulation",
        "memory_injection",
        "role_hijacking",
        "cot_injection",
        "privilege_escalation",
        "role_confusion",
        "attack_chain",
    }
)


def build_attack_payload(
    attack_type: str,
    prompt: str,
    target_behavior: Optional[str] = None,
) -> AttackPayload:
    """Build an AttackPayload, resolving AttackType when possible."""
    try:
        resolved_type = AttackType(attack_type)
    except ValueError:
        resolved_type = AttackType.PROMPT_INJECTION

    return AttackPayload(
        attack_type=resolved_type,
        prompt=prompt,
        target_behavior=target_behavior or prompt,
    )


async def execute_registry_attack(
    attack_type: str,
    llm: BaseLLM,
    prompt: str,
    *,
    target_behavior: Optional[str] = None,
    max_iterations: int = 100,
    attacker_llm: Optional[BaseLLM] = None,
    judge_llm: Optional[BaseLLM] = None,
) -> AttackOutcome:
    """Create and run an attack exclusively via the global registry."""
    if not has_attack_type(attack_type):
        raise ValueError(f"Unknown attack type: {attack_type}")

    attack = create_attack_instance(
        attack_type=attack_type,
        llm=llm,
        max_iterations=max_iterations,
        attacker_llm=attacker_llm or llm,
        judge_llm=judge_llm,
    )
    payload = build_attack_payload(attack_type, prompt, target_behavior)
    return await attack.generate_attack(payload)


def format_attack_outcome(
    outcome: AttackOutcome,
    *,
    attack_type: Optional[str] = None,
    agent_runtime: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Normalize attack outcome fields for API responses."""
    result_value = outcome.result.value if hasattr(outcome.result, "value") else str(outcome.result)
    response_text = getattr(outcome, "model_response", None) or getattr(outcome, "response", "")
    payload = {
        "result": result_value,
        "success_score": outcome.success_score,
        "adversarial_prompt": outcome.adversarial_prompt,
        "model_response": response_text,
        "iterations": outcome.iterations,
        "metadata": outcome.metadata,
        "original_prompt": outcome.original_prompt,
        "target_behavior": outcome.target_behavior if hasattr(outcome, "target_behavior") else None,
        "timestamp": outcome.timestamp.isoformat() if outcome.timestamp else None,
    }
    if agent_runtime is not None:
        payload["agent_runtime"] = agent_runtime
    if attack_type:
        payload["attack_type"] = attack_type
    return payload


async def format_attack_outcome_enriched(
    outcome: AttackOutcome,
    attack_type: str,
) -> Dict[str, Any]:
    """格式化攻击结果，Agent/工具类攻击附加 runtime 分析"""
    agent_runtime = None
    response_text = getattr(outcome, "model_response", None) or getattr(outcome, "response", "")
    if attack_type in AGENT_RUNTIME_ATTACK_KEYS or "agent" in attack_type or "tool" in attack_type:
        agent_runtime = await analyze_agent_tool_response(response_text)
    return format_attack_outcome(outcome, attack_type=attack_type, agent_runtime=agent_runtime)
