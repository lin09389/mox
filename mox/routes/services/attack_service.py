"""Registry-backed attack execution helpers for API routes."""

from typing import Any, Dict, Optional

from mox.core import AttackPayload, AttackType, BaseLLM, AttackOutcome
from mox.attacks.registry import create_attack_instance, has_attack_type


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
) -> AttackOutcome:
    """Create and run an attack exclusively via the global registry."""
    if not has_attack_type(attack_type):
        raise ValueError(f"Unknown attack type: {attack_type}")

    attack = create_attack_instance(
        attack_type=attack_type,
        llm=llm,
        max_iterations=max_iterations,
    )
    payload = build_attack_payload(attack_type, prompt, target_behavior)
    return await attack.generate_attack(payload)


def format_attack_outcome(outcome: AttackOutcome) -> Dict[str, Any]:
    """Normalize attack outcome fields for API responses."""
    result_value = outcome.result.value if hasattr(outcome.result, "value") else str(outcome.result)
    response_text = getattr(outcome, "model_response", None) or getattr(outcome, "response", "")
    return {
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