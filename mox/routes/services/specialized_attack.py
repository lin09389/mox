"""Shared specialized attack execution for v1 and v2 routes."""

from typing import Any, Dict, Optional

from mox.core.history_store import persist_attack_outcome
from mox.routes.services import get_cached_llm, execute_registry_attack
from mox.routes.services.attack_service import (
    AGENT_MODE_ATTACK_KEYS,
    format_attack_outcome_enriched,
)
from mox.evaluation.redteam_llms import resolve_redteam_agent_mode


async def run_specialized_attack_response(
    attack_type: str,
    prompt: str,
    model_name: str,
    *,
    target_behavior: Optional[str] = None,
    max_iterations: int = 100,
    use_ollama: bool = False,
    ollama_base_url: str = "http://localhost:11434/v1",
    agent_mode: Optional[str] = None,
    max_agent_steps: Optional[int] = None,
    source: str,
) -> Dict[str, Any]:
    llm = get_cached_llm(
        model_name,
        use_ollama=use_ollama,
        ollama_base_url=ollama_base_url,
    )
    resolved_agent_mode = resolve_redteam_agent_mode(
        agent_mode,
        techniques=[attack_type] if attack_type in AGENT_MODE_ATTACK_KEYS else None,
    )
    outcome = await execute_registry_attack(
        attack_type,
        llm,
        prompt,
        target_behavior=target_behavior,
        max_iterations=max_iterations,
        agent_mode=resolved_agent_mode,
        max_agent_steps=max_agent_steps,
    )
    record_id = await persist_attack_outcome(
        attack_type,
        model_name,
        outcome,
        source=source,
    )
    payload = await format_attack_outcome_enriched(outcome, attack_type)
    payload["model_used"] = model_name
    payload["ollama_mode"] = use_ollama
    payload["record_id"] = record_id
    return payload
