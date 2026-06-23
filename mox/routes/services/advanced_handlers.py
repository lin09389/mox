"""Shared handlers for advanced defense, safety cards, and Ollama status."""

from typing import Any, Dict, List, Optional

from mox.core.history_store import persist_defense_scan
from mox.routes.services import get_cached_llm


async def run_semantic_firewall(
    text: str,
    *,
    context: Optional[str] = None,
    source: str = "semantic_firewall",
) -> Dict[str, Any]:
    from mox.defense.semantic_firewall import SemanticFirewall

    firewall = SemanticFirewall()
    result = await firewall.analyze(text, context)
    record_id = await persist_defense_scan(
        "semantic_firewall",
        text,
        is_malicious=result.is_malicious,
        confidence=result.confidence,
        detected_patterns=result.detected_patterns,
        source=source,
    )

    return {
        "is_malicious": result.is_malicious,
        "threat_level": result.threat_level.value
        if hasattr(result.threat_level, "value")
        else str(result.threat_level),
        "confidence": result.confidence,
        "intent": result.metadata.get("intent", "unknown"),
        "risk_score": result.metadata.get("risk_score", 0.0),
        "detected_patterns": result.detected_patterns,
        "record_id": record_id,
    }


async def run_output_validator(
    text: str,
    *,
    check_pii: bool = True,
    check_sensitive: bool = True,
    source: str = "output_validator",
) -> Dict[str, Any]:
    from mox.defense.output_validator import OutputValidator

    validator = OutputValidator()
    validation = await validator.validate(text)
    defense = validation.to_defense_result()
    record_id = await persist_defense_scan(
        "output_validator",
        text,
        output_text=validation.sanitized_output,
        is_malicious=defense.is_malicious,
        confidence=defense.confidence,
        detected_patterns=defense.detected_patterns,
        source=source,
    )

    return {
        "is_valid": validation.is_valid,
        "is_malicious": defense.is_malicious,
        "confidence": defense.confidence,
        "detected_patterns": defense.detected_patterns,
        "has_pii": validation.metadata.get("has_pii", False),
        "has_sensitive": validation.metadata.get("has_sensitive", False),
        "pii_types": validation.metadata.get("pii_types", []),
        "sensitive_types": validation.metadata.get("sensitive_types", []),
        "sanitized_text": validation.sanitized_output,
        "sanitized_input": defense.sanitized_input,
        "warnings": validation.warnings,
        "risk_score": validation.risk_score,
        "recommendations": validation.recommendations,
        "record_id": record_id,
    }


async def run_constitutional_ai(
    text: str,
    model_name: str = "gpt-4",
) -> Dict[str, Any]:
    from mox.defense.constitutional_ai import ConstitutionalAI

    llm = get_cached_llm(model_name)
    cai = ConstitutionalAI(llm)
    result = await cai.process(text)

    return {
        "original_text": text,
        "revised_text": result.revised_text,
        "violations_found": result.violations,
        "corrections_made": result.corrections,
        "is_compliant": result.is_compliant,
    }


async def generate_safety_card(
    model_name: str,
    *,
    include_tests: bool = True,
) -> Dict[str, Any]:
    from mox.evaluation.safety_card import SafetyCardGenerator

    generator = SafetyCardGenerator()
    card = await generator.generate(model_name, include_tests=include_tests)

    return {
        "model_name": card.model_name,
        "version": card.version,
        "generated_at": card.generated_at.isoformat() if card.generated_at else None,
        "overall_risk_level": card.overall_risk_level.value
        if hasattr(card.overall_risk_level, "value")
        else str(card.overall_risk_level),
        "overall_safety_score": card.overall_safety_score,
        "tests_passed": card.tests_passed,
        "total_tests": card.total_tests,
        "vulnerabilities_found": card.vulnerabilities_found,
        "compliance_score": card.compliance_score,
        "category_scores": card.category_scores,
        "risk_assessment": [
            {
                "category": r.category,
                "description": r.description,
                "level": r.level.value if hasattr(r.level, "value") else str(r.level),
            }
            for r in card.risk_assessment
        ],
        "usage_limitations": card.usage_limitations,
        "recommendations": card.recommendations,
    }


async def get_recent_safety_cards() -> List[Dict[str, Any]]:
    return [
        {
            "model_name": "gpt-4",
            "created_at": "2025-03-27T10:00:00",
            "overall_safety_score": 85,
        }
    ]


async def check_ollama_status(base_url: str = "http://localhost:11434") -> Dict[str, Any]:
    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url.rstrip('/')}/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    return {
                        "status": "success",
                        "message": "Ollama is reachable",
                        "models": models,
                    }
                return {
                    "status": "error",
                    "message": f"HTTP {resp.status}",
                }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }