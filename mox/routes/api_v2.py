"""API v2 compatibility layer — thin wrappers over v1 registry-backed routes."""

import warnings
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from mox.core import AttackType
from mox.core.auth import get_optional_active_user, User
from mox.core.history_store import persist_attack_outcome, persist_defense_scan
from mox.routes.services import get_cached_llm, execute_registry_attack
from mox.routes.services.attack_service import format_attack_outcome

warnings.warn(
    "mox.routes.api_v2 is a compatibility layer; prefer /api/v1/attack/* endpoints.",
    DeprecationWarning,
    stacklevel=2,
)

router = APIRouter(prefix="/api/v2", tags=["API v2"])


class AgentAttackRequest(BaseModel):
    attack_type: str = "tool_chaining"
    prompt: str
    target_behavior: Optional[str] = None
    model_name: str = "gpt-4"
    tools: List[str] = Field(default_factory=lambda: ["read_file", "http_request"])
    use_ollama: bool = False
    ollama_base_url: str = "http://localhost:11434/v1"


class MultimodalAttackRequest(BaseModel):
    attack_type: str = "image_injection"
    prompt: str
    model_name: str = "gpt-4-vision"
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    template: Optional[str] = None
    use_ollama: bool = False
    ollama_base_url: str = "http://localhost:11434/v1"


class NovelAttackRequest(BaseModel):
    attack_type: str = "many_shot"
    prompt: str
    target_behavior: Optional[str] = None
    model_name: str = "gpt-4"
    use_ollama: bool = False
    ollama_base_url: str = "http://localhost:11434/v1"


class SafetyCardRequest(BaseModel):
    model_name: str = "gpt-4"
    include_tests: bool = True


class SemanticFirewallRequest(BaseModel):
    text: str
    context: Optional[str] = None
    user_id: Optional[str] = None


class OutputValidationRequest(BaseModel):
    text: str
    check_pii: bool = True
    check_sensitive: bool = True


class OllamaStatusRequest(BaseModel):
    base_url: str = "http://localhost:11434"


class ConstitutionalAIRequest(BaseModel):
    text: str
    model_name: str = "gpt-4"


async def _registry_attack_response(
    attack_type: str,
    request_model: str,
    prompt: str,
    *,
    target_behavior: Optional[str] = None,
    use_ollama: bool = False,
    ollama_base_url: str = "http://localhost:11434/v1",
    source: str,
    max_iterations: int = 100,
) -> Dict[str, Any]:
    llm = get_cached_llm(
        request_model,
        use_ollama=use_ollama,
        ollama_base_url=ollama_base_url,
    )
    outcome = await execute_registry_attack(
        attack_type,
        llm,
        prompt,
        target_behavior=target_behavior,
        max_iterations=max_iterations,
    )
    record_id = await persist_attack_outcome(
        attack_type,
        request_model,
        outcome,
        source=source,
    )
    payload = format_attack_outcome(outcome)
    payload["model_used"] = request_model
    payload["ollama_mode"] = use_ollama
    payload["record_id"] = record_id
    return payload


@router.post("/attacks/agent")
async def run_agent_attack(
    request: AgentAttackRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        return await _registry_attack_response(
            request.attack_type,
            request.model_name,
            request.prompt,
            target_behavior=request.target_behavior,
            use_ollama=request.use_ollama,
            ollama_base_url=request.ollama_base_url,
            source="api_v2_agent",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/attacks/multimodal")
async def run_multimodal_attack(
    request: MultimodalAttackRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        return await _registry_attack_response(
            request.attack_type,
            request.model_name,
            request.prompt,
            use_ollama=request.use_ollama,
            ollama_base_url=request.ollama_base_url,
            source="api_v2_multimodal",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/attacks/novel")
async def run_novel_attack(
    request: NovelAttackRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        return await _registry_attack_response(
            request.attack_type,
            request.model_name,
            request.prompt,
            target_behavior=request.target_behavior,
            use_ollama=request.use_ollama,
            ollama_base_url=request.ollama_base_url,
            source="api_v2_novel",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/defense/semantic-firewall")
async def run_semantic_firewall(
    request: SemanticFirewallRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        from mox.defense.semantic_firewall import SemanticFirewall

        firewall = SemanticFirewall()
        result = await firewall.analyze(request.text, request.context)
        record_id = await persist_defense_scan(
            "semantic_firewall",
            request.text,
            is_malicious=result.is_malicious,
            confidence=result.confidence,
            detected_patterns=result.detected_patterns,
            source="api_v2_semantic_firewall",
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/defense/output-validator")
async def run_output_validator(
    request: OutputValidationRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        from mox.defense.output_validator import OutputValidator

        validator = OutputValidator()
        validation = await validator.validate(request.text)
        defense = validation.to_defense_result()
        record_id = await persist_defense_scan(
            "output_validator",
            request.text,
            output_text=validation.sanitized_output,
            is_malicious=defense.is_malicious,
            confidence=defense.confidence,
            detected_patterns=defense.detected_patterns,
            source="api_v2_output_validator",
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/defense/constitutional-ai")
async def run_constitutional_ai_v2(
    request: ConstitutionalAIRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        from mox.defense.constitutional_ai import ConstitutionalAI

        llm = get_cached_llm(request.model_name)
        cai = ConstitutionalAI(llm)
        result = await cai.process(request.text)

        return {
            "original_text": request.text,
            "revised_text": result.revised_text,
            "violations_found": result.violations,
            "corrections_made": result.corrections,
            "is_compliant": result.is_compliant,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/safety-cards/generate")
async def generate_safety_card(
    request: SafetyCardRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        from mox.evaluation.safety_card import SafetyCardGenerator

        generator = SafetyCardGenerator()
        card = await generator.generate(request.model_name, include_tests=request.include_tests)

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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safety-cards/recent")
async def get_recent_safety_cards(
    current_user: User = Depends(get_optional_active_user),
) -> List[Dict[str, Any]]:
    return [
        {
            "model_name": "gpt-4",
            "created_at": "2025-03-27T10:00:00",
            "overall_safety_score": 85,
        }
    ]


@router.post("/ollama/status")
async def check_ollama_status(
    request: OllamaStatusRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{request.base_url.rstrip('/')}/api/tags") as resp:
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
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }