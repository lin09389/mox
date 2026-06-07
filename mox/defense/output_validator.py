"""Compatibility shim — exposes an ``OutputValidator`` class that previously
lived in a separate ``output_validator.py`` module.

The output-validation logic has been consolidated into
:mod:`mox.defense.output_filter` (``OutputFilter``).  ``OutputValidator`` is
now a thin alias that delegates to the registered ``OutputFilter`` instance
so that the v2 ``/defense/output-validator`` endpoint works without a
behavioral regression.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mox.core.types import DefenseResult, ThreatLevel


@dataclass
class OutputValidatorResult:
    """Result object expected by the v2 ``/defense/output-validator`` endpoint."""

    is_valid: bool
    sanitized_output: str
    warnings: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class OutputValidator:
    """Drop-in replacement backed by the consolidated ``OutputFilter``.

    The original ``OutputValidator`` had a different surface (``validate()``
    returning a dataclass) than the consolidated ``OutputFilter`` (whose
    ``detect()`` returns a :class:`DefenseResult`).  This shim translates
    between the two contracts so legacy callers keep working.
    """

    def __init__(self) -> None:
        # Import lazily to avoid a hard dependency at module load time —
        # if OutputFilter is ever removed, this shim will still report a
        # clean error to the caller instead of breaking the whole process.
        from mox.defense.output_filter import OutputFilter

        self._filter = OutputFilter()

    async def validate(self, text: str) -> OutputValidatorResult:
        """Validate ``text`` and return a v2-shaped result.

        Translates ``DefenseResult`` -> ``OutputValidatorResult`` so the
        existing v2 endpoint contract is preserved.
        """
        result: DefenseResult = await self._filter.detect(text)
        is_valid = not result.is_malicious
        warnings: list = []
        if result.detected_patterns:
            warnings.extend(result.detected_patterns)
        metadata: dict[str, Any] = {
            "confidence": result.confidence,
            "threat_level": (
                result.threat_level.value
                if hasattr(result.threat_level, "value")
                else str(result.threat_level)
            ),
            "is_malicious": result.is_malicious,
            "detected_patterns": result.detected_patterns,
            # legacy keys that the v2 endpoint used to expose directly
            "has_pii": any("pii" in p.lower() for p in result.detected_patterns),
            "has_sensitive": any(
                "sensitive" in p.lower() for p in result.detected_patterns
            ),
            "pii_types": [
                p for p in result.detected_patterns if "pii" in p.lower()
            ],
            "sensitive_types": [
                p for p in result.detected_patterns if "sensitive" in p.lower()
            ],
        }
        return OutputValidatorResult(
            is_valid=is_valid,
            sanitized_output=result.sanitized_input or text,
            warnings=warnings,
            metadata=metadata,
        )


__all__ = ["OutputValidator", "OutputValidatorResult"]
