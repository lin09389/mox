"""Tests for OutputValidationResult / DefenseResult compatibility."""

from mox.defense.output_validator import (
    OutputValidationResult,
    PIIDetection,
    PIICategory,
    OutputValidator,
)


def test_output_validation_result_defense_compat():
    result = OutputValidationResult(
        is_safe=False,
        pii_detections=[
            PIIDetection(
                category=PIICategory.EMAIL,
                value="user@example.com",
                start_pos=0,
                end_pos=16,
                confidence=0.9,
                masked_value="****@***.***",
            )
        ],
        sensitive_detections=[],
        sanitized_output="****@***.***",
        risk_score=0.75,
        recommendations=["检测到 PII 信息"],
    )

    assert result.is_malicious is True
    assert result.is_valid is False
    assert result.confidence == 0.75
    assert "PII:email" in result.detected_patterns
    assert result.metadata["has_pii"] is True

    defense = result.to_defense_result()
    assert defense.is_malicious is True
    assert defense.confidence == 0.75
    assert defense.sanitized_input == "****@***.***"


async def test_output_validator_detect_matches_validate():
    validator = OutputValidator()
    text = "Contact me at user@secret.com for details"
    detect = await validator.detect(text)
    validation = await validator.validate(text)

    assert detect.is_malicious == validation.is_malicious
    assert detect.confidence == validation.confidence
    assert set(detect.detected_patterns) == set(validation.detected_patterns)