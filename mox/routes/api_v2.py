"""API v2 compatibility layer — delegates to v1 registry-backed handlers."""

import warnings
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from mox.core.auth import get_optional_active_user, User
from mox.routes.services.specialized_attack import run_specialized_attack_response
from mox.routes.services.advanced_handlers import (
    run_semantic_firewall,
    run_output_validator,
    run_constitutional_ai,
    generate_safety_card,
    get_recent_safety_cards,
    check_ollama_status,
)

warnings.warn(
    "mox.routes.api_v2 is a compatibility layer; prefer /api/v1/* endpoints.",
    DeprecationWarning,
    stacklevel=2,
)

router = APIRouter(prefix="/api/v2", tags=["API v2 (deprecated)"])


class AgentAttackRequest(BaseModel):
    attack_type: str = "tool_chaining"
    prompt: str
    target_behavior: Optional[str] = None
    model_name: str = "gpt-4"
    tools: List[str] = Field(default_factory=lambda: ["read_file", "http_request"])
    use_ollama: bool = False
    ollama_base_url: str = "http://localhost:11434/v1"
    agent_mode: Optional[str] = None
    max_agent_steps: Optional[int] = Field(default=None, ge=1, le=50)


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
    agent_mode: Optional[str] = None,
    max_agent_steps: Optional[int] = None,
    source: str,
    max_iterations: int = 100,
) -> Dict[str, Any]:
    return await run_specialized_attack_response(
        attack_type,
        prompt,
        request_model,
        target_behavior=target_behavior,
        max_iterations=max_iterations,
        use_ollama=use_ollama,
        ollama_base_url=ollama_base_url,
        agent_mode=agent_mode,
        max_agent_steps=max_agent_steps,
        source=source,
    )


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
            agent_mode=request.agent_mode,
            max_agent_steps=request.max_agent_steps,
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
async def run_semantic_firewall_v2(
    request: SemanticFirewallRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        return await run_semantic_firewall(
            request.text,
            context=request.context,
            source="api_v2_semantic_firewall",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/defense/output-validator")
async def run_output_validator_v2(
    request: OutputValidationRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        return await run_output_validator(
            request.text,
            check_pii=request.check_pii,
            check_sensitive=request.check_sensitive,
            source="api_v2_output_validator",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/defense/constitutional-ai")
async def run_constitutional_ai_v2(
    request: ConstitutionalAIRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        return await run_constitutional_ai(request.text, request.model_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/safety-cards/generate")
async def generate_safety_card_v2(
    request: SafetyCardRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        return await generate_safety_card(
            request.model_name,
            include_tests=request.include_tests,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safety-cards/recent")
async def get_recent_safety_cards_v2(
    current_user: User = Depends(get_optional_active_user),
) -> List[Dict[str, Any]]:
    return await get_recent_safety_cards()


@router.post("/ollama/status")
async def check_ollama_status_v2(
    request: OllamaStatusRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    return await check_ollama_status(request.base_url)
