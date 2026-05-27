"""Event handlers that persist attack/defense records to the database.

Register these at application startup::

    from mox.infrastructure.event_handlers import register_persistence_handlers
    register_persistence_handlers()
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def _persist_attack(outcome: Any, attack: Any, save_to_db: bool = False, **_: Any) -> None:
    """Persist an AttackOutcome to the database when save_to_db is True."""
    if not save_to_db:
        return

    try:
        from mox.infrastructure.database import get_database

        db = get_database()
        if db is None:
            return

        attack_type = attack.attack_type
        await db.save_attack_record(
            attack_type=attack_type.value if hasattr(attack_type, "value") else str(attack_type),
            original_prompt=outcome.original_prompt,
            adversarial_prompt=outcome.adversarial_prompt,
            model_response=outcome.response,
            result=outcome.result.value if hasattr(outcome.result, "value") else str(outcome.result),
            success_score=outcome.success_score,
            iterations=outcome.iterations,
            model_name=getattr(getattr(attack, "target_llm", None), "model", None),
            metadata=outcome.metadata or {},
        )
    except Exception as e:
        logger.warning("Failed to persist attack record: %s", e)


async def _persist_defense(
    result: Any,
    defense: Any,
    input_text: str = "",
    model_name: str | None = None,
    save_to_db: bool = False,
    **_: Any,
) -> None:
    """Persist a DefenseResult to the database when save_to_db is True."""
    if not save_to_db:
        return

    try:
        from mox.infrastructure.database import get_database

        db = get_database()
        if db is None:
            return

        defense_type = getattr(defense, "defense_type", None)
        await db.save_defense_record(
            defense_type=defense_type.value if defense_type and hasattr(defense_type, "value") else str(defense_type),
            input_text=input_text,
            output_text=result.sanitized_input,
            is_malicious=result.is_malicious,
            confidence=result.confidence,
            detected_patterns=result.detected_patterns,
            model_name=model_name,
            metadata=result.metadata or {},
        )
    except Exception as e:
        logger.warning("Failed to persist defense record: %s", e)


def register_persistence_handlers() -> None:
    """Subscribe persistence handlers to the global event bus.

    Call once at application startup (e.g. in the FastAPI lifespan).
    """
    from mox.core.events import event_bus

    event_bus.on("attack_completed", _persist_attack)
    event_bus.on("defense_detected", _persist_defense)
    logger.info("Persistence event handlers registered")
