"""Shared persistence helpers for attack/defense history records."""

from typing import Any, Dict, List, Optional, Sequence

from mox.core.database import get_database
from mox.core.logging import get_logger
from mox.core.types import AttackOutcome

logger = get_logger("history_store")


async def persist_attack_outcome(
    attack_type: str,
    model: str,
    outcome: AttackOutcome,
    *,
    source: str = "api",
    report_id: Optional[int] = None,
) -> Optional[int]:
    try:
        result_value = (
            outcome.result.value if hasattr(outcome.result, "value") else str(outcome.result)
        )
        metadata = dict(outcome.metadata or {})
        metadata["source"] = source
        if report_id is not None:
            metadata["report_id"] = report_id
        return await get_database().save_attack_record(
            attack_type=attack_type,
            original_prompt=outcome.original_prompt or "",
            adversarial_prompt=outcome.adversarial_prompt,
            model_response=outcome.model_response or "",
            result=result_value,
            success_score=float(outcome.success_score or 0.0),
            iterations=int(outcome.iterations or 1),
            model_name=model,
            metadata=metadata,
        )
    except Exception as exc:
        logger.warning(f"Failed to persist attack record ({attack_type}): {exc}")
        return None


async def persist_defense_scan(
    defense_type: str,
    input_text: str,
    *,
    output_text: Optional[str] = None,
    is_malicious: bool,
    confidence: float,
    detected_patterns: Optional[List[str]] = None,
    model_name: Optional[str] = None,
    source: str = "api",
    report_id: Optional[int] = None,
) -> Optional[int]:
    try:
        metadata: Dict[str, Any] = {"source": source}
        if report_id is not None:
            metadata["report_id"] = report_id
        return await get_database().save_defense_record(
            defense_type=defense_type,
            input_text=input_text,
            output_text=output_text,
            is_malicious=is_malicious,
            confidence=float(confidence or 0.0),
            detected_patterns=detected_patterns or [],
            model_name=model_name,
            metadata=metadata,
        )
    except Exception as exc:
        logger.warning(f"Failed to persist defense record ({defense_type}): {exc}")
        return None


async def persist_advanced_attack_batch(
    attack_type: str,
    model: str,
    target: str,
    results: Sequence[Any],
    *,
    source: str = "advanced_attack",
) -> Optional[int]:
    """Persist a summary row for multi-template advanced attacks."""
    if not results:
        return None
    try:
        total = len(results)
        success_count = sum(1 for item in results if getattr(item, "success", False))
        avg_confidence = (
            sum(float(getattr(item, "confidence", 0.0) or 0.0) for item in results) / total
        )
        success_rate = success_count / total
        first = results[0]
        preview = [
            {
                "template_name": getattr(item, "template_name", None),
                "category": getattr(item, "category", None),
                "severity": getattr(item, "severity", None),
                "success": getattr(item, "success", False),
                "confidence": getattr(item, "confidence", 0.0),
            }
            for item in results[:5]
        ]
        return await get_database().save_attack_record(
            attack_type=attack_type,
            original_prompt=target,
            adversarial_prompt=getattr(first, "prompt", target),
            model_response=(getattr(first, "response", "") or "")[:2000],
            result="success" if success_rate >= 0.5 else "failure",
            success_score=avg_confidence,
            iterations=total,
            model_name=model,
            metadata={
                "source": source,
                "target": target,
                "total_templates": total,
                "success_count": success_count,
                "success_rate": round(success_rate, 4),
                "results_preview": preview,
            },
        )
    except Exception as exc:
        logger.warning(f"Failed to persist advanced attack batch ({attack_type}): {exc}")
        return None
