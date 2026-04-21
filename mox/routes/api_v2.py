
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from mox.core import BaseLLM, LLMFactory, AttackType, settings
from mox.infrastructure.auth import get_optional_active_user, User

router = APIRouter(prefix="/api/v2", tags=["API v2"])


# ============        ============

class AgentAttackRequest(BaseModel):
    attack_type: str = "tool_chaining"
    prompt: str
    target_behavior: Optional[str] = None
    model_name: str = "gpt-4"
    tools: List[str] = Field(default_factory=lambda: ["read_file", "http_request"])
    # Ollama   
    use_ollama: bool = False
    ollama_base_url: str = "http://localhost:11434/v1"


class MultimodalAttackRequest(BaseModel):
    attack_type: str = "image_injection"
    prompt: str
    model_name: str = "gpt-4-vision"
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    template: Optional[str] = None
    # Ollama   
    use_ollama: bool = False
    ollama_base_url: str = "http://localhost:11434/v1"


class NovelAttackRequest(BaseModel):
    attack_type: str = "many_shot"
    prompt: str
    target_behavior: Optional[str] = None
    model_name: str = "gpt-4"
    # Ollama   
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


# ============ LLM     ============

_llm_cache: Dict[str, BaseLLM] = {}


def get_llm(model: str, use_ollama: bool = False, ollama_base_url: str = "http://localhost:11434/v1") -> BaseLLM:
    cache_key = f"{model}:{use_ollama}:{ollama_base_url}"

    if cache_key not in _llm_cache:
        if use_ollama:
            #     Ollama      
            _llm_cache[cache_key] = LLMFactory.create_from_model_name(
                model,
                base_url=ollama_base_url,
                api_key="ollama",
            )
        else:
            _llm_cache[cache_key] = LLMFactory.create_from_model_name(model)

    return _llm_cache[cache_key]


# ============ Ollama       ?============

@router.get("/ollama/status")
async def get_ollama_status(
    base_url: str = "http://localhost:11434",
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/tags", timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [
                        {
                            "name": m["name"],
                            "size": m.get("size", 0),
                            "modified_at": m.get("modified_at", ""),
                        }
                        for m in data.get("models", [])
                    ]
                    return {
                        "status": "running",
                        "base_url": base_url,
                        "models": models,
                        "model_count": len(models),
                    }
                return {
                    "status": "error",
                    "message": f"HTTP {resp.status}",
                }
    except Exception as e:
        return {
            "status": "unavailable",
            "message": str(e),
            "hint": "    ?Ollama         : ollama serve",
        }


@router.post("/ollama/pull")
async def pull_ollama_model(
    model: str,
    base_url: str = "http://localhost:11434",
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/api/pull",
                json={"name": model},
                timeout=300,
            ) as resp:
                if resp.status == 200:
                    return {
                        "status": "success",
                        "message": f"    {model}       ",
                    }
                return {
                    "status": "error",
                    "message": f"      : HTTP {resp.status}",
                }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


# ============ Agent       ============

@router.post("/attacks/agent")
async def run_agent_attack(
    request: AgentAttackRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        from mox.attacks.agent_attacks_v2 import (
            ToolChainingAttack,
            IndirectToolInjection,
            PrivilegeEscalationAttack,
            ToolConfusionAttack,
            DataExfiltrationAttack,
            MultiAgentAttack,
            CompositeAgentAttack,
            DEFAULT_TOOLS,
        )
        from mox.attacks.base import AttackConfig
        from mox.core import AttackPayload

        #    Ollama      
        llm = get_llm(
            request.model_name,
            use_ollama=request.use_ollama,
            ollama_base_url=request.ollama_base_url,
        )
        config = AttackConfig()

        #          
        attack_map = {
            "tool_chaining": ToolChainingAttack,
            "indirect_injection": IndirectToolInjection,
            "privilege_escalation": PrivilegeEscalationAttack,
            "tool_confusion": ToolConfusionAttack,
            "data_exfiltration": DataExfiltrationAttack,
            "multi_agent": MultiAgentAttack,
            "composite": CompositeAgentAttack,
        }

        attack_class = attack_map.get(request.attack_type, ToolChainingAttack)
        attack = attack_class(llm, config)

        #          
        payload = AttackPayload(
            attack_type=AttackType.AGENT_ATTACK,
            prompt=request.prompt,
            target_behavior=request.target_behavior or request.prompt,
        )

        #      
        outcome = await attack.generate_attack(payload)

        return {
            "result": outcome.result.value if hasattr(outcome.result, 'value') else str(outcome.result),
            "success_score": outcome.success_score,
            "adversarial_prompt": outcome.adversarial_prompt,
            "model_response": outcome.response,
            "iterations": outcome.iterations,
            "metadata": outcome.metadata,
            "model_used": request.model_name,
            "ollama_mode": request.use_ollama,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============           ?============

@router.post("/attacks/multimodal")
async def run_multimodal_attack(
    request: MultimodalAttackRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        from mox.attacks.multimodal_attacks import (
            ImageInjectionAttack,
            AudioInjectionAttack,
            CrossModalAttack,
            FigStepAttack,
            MultimodalJailbreakAttack,
        )
        from mox.attacks.base import AttackConfig
        from mox.core import AttackPayload

        #    Ollama      
        llm = get_llm(
            request.model_name,
            use_ollama=request.use_ollama,
            ollama_base_url=request.ollama_base_url,
        )
        config = AttackConfig()

        #          
        attack_map = {
            "image_injection": ImageInjectionAttack,
            "audio_injection": AudioInjectionAttack,
            "cross_modal": CrossModalAttack,
            "figstep": FigStepAttack,
            "multimodal_jailbreak": MultimodalJailbreakAttack,
        }

        attack_class = attack_map.get(request.attack_type, ImageInjectionAttack)
        attack = attack_class(llm, config)

        #          
        payload = AttackPayload(
            attack_type=AttackType.MULTIMODAL_ADVERSARIAL,
            prompt=request.prompt,
            target_behavior=request.prompt,
        )

        #      
        outcome = await attack.generate_attack(payload)

        return {
            "result": outcome.result.value if hasattr(outcome.result, 'value') else str(outcome.result),
            "success_score": outcome.success_score,
            "adversarial_prompt": outcome.adversarial_prompt,
            "model_response": outcome.response,
            "detected_patterns": outcome.metadata.get("detected_patterns", []),
            "model_used": request.model_name,
            "ollama_mode": request.use_ollama,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============          ============

@router.post("/attacks/novel")
async def run_novel_attack(
    request: NovelAttackRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        from mox.attacks.novel_attacks_v3 import (
            ManyShotJailbreakAttack,
            SkeletonKeyAttack,
            DeceptiveAlignmentAttack,
            CognitiveOverloadAttack,
            ContextOverflowAttack,
            RoleConfusionAttack,
        )
        from mox.attacks.base import AttackConfig
        from mox.core import AttackPayload

        #    Ollama      
        llm = get_llm(
            request.model_name,
            use_ollama=request.use_ollama,
            ollama_base_url=request.ollama_base_url,
        )
        config = AttackConfig()

        attack_map = {
            "many_shot": ManyShotJailbreakAttack,
            "skeleton_key": SkeletonKeyAttack,
            "deceptive_alignment": DeceptiveAlignmentAttack,
            "cognitive_overload": CognitiveOverloadAttack,
            "context_overflow": ContextOverflowAttack,
            "role_confusion": RoleConfusionAttack,
        }

        attack_class = attack_map.get(request.attack_type, ManyShotJailbreakAttack)
        attack = attack_class(llm, config)

        payload = AttackPayload(
            attack_type=AttackType.JAILBREAK,
            prompt=request.prompt,
            target_behavior=request.target_behavior or request.prompt,
        )

        outcome = await attack.generate_attack(payload)

        return {
            "result": outcome.result.value if hasattr(outcome.result, 'value') else str(outcome.result),
            "success_score": outcome.success_score,
            "adversarial_prompt": outcome.adversarial_prompt,
            "model_response": outcome.response,
            "iterations": outcome.iterations,
            "model_used": request.model_name,
            "ollama_mode": request.use_ollama,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============       ============

@router.post("/defense/semantic-firewall")
async def run_semantic_firewall(
    request: SemanticFirewallRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        from mox.defense.semantic_firewall import SemanticFirewall

        firewall = SemanticFirewall()
        result = await firewall.analyze(request.text, request.context)

        return {
            "is_malicious": result.is_malicious,
            "threat_level": result.threat_level.value if hasattr(result.threat_level, 'value') else str(result.threat_level),
            "confidence": result.confidence,
            "intent": result.metadata.get("intent", "unknown"),
            "risk_score": result.metadata.get("risk_score", 0.0),
            "detected_patterns": result.detected_patterns,
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
        result = await validator.validate(request.text)

        return {
            "is_valid": result.is_valid,
            "has_pii": result.metadata.get("has_pii", False),
            "has_sensitive": result.metadata.get("has_sensitive", False),
            "pii_types": result.metadata.get("pii_types", []),
            "sensitive_types": result.metadata.get("sensitive_types", []),
            "sanitized_text": result.sanitized_output,
            "warnings": result.warnings,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



class ConstitutionalAIRequest(BaseModel):
    text: str
    model_name: str = "gpt-4"


@router.post("/defense/constitutional-ai")
async def run_constitutional_ai_v2(
    request: ConstitutionalAIRequest,
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        from mox.defense.constitutional_ai import ConstitutionalAI

        llm = get_llm(request.model_name)
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


# ============          ============

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
            "overall_risk_level": card.overall_risk_level.value if hasattr(card.overall_risk_level, 'value') else str(card.overall_risk_level),
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
                    "level": r.level.value if hasattr(r.level, 'value') else str(r.level),
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
    #                         ?
    return [
        {
            "model_name": "gpt-4",
            "created_at": "2025-03-27T10:00:00",
            "overall_safety_score": 85,
        },
        {
            "model_name": "claude-3-opus",
            "created_at": "2025-03-26T15:30:00",
            "overall_safety_score": 88,
        },
    ]


# ============          ============

@router.get("/benchmarks/cases")
async def get_benchmark_cases(
    benchmark_type: str = "harmbench_v2",
    current_user: User = Depends(get_optional_active_user),
) -> Dict[str, Any]:
    try:
        from mox.evaluation.benchmarks_v2 import (
            HARMBENCH_V2_CASES,
            AGENTBENCH_CASES,
            MM_SAFETY_BENCH_CASES,
            SAFETY_BENCH_CASES,
            RED_TEAM_BENCH_CASES,
        )

        benchmark_map = {
            "harmbench_v2": HARMBENCH_V2_CASES,
            "agentbench": AGENTBENCH_CASES,
            "mm_safety_bench": MM_SAFETY_BENCH_CASES,
            "safety_bench": SAFETY_BENCH_CASES,
            "red_team_bench": RED_TEAM_BENCH_CASES,
        }

        cases = benchmark_map.get(benchmark_type, HARMBENCH_V2_CASES)

        return {
            "benchmark_type": benchmark_type,
            "total_cases": len(cases),
            "cases": [
                {
                    "id": c.id,
                    "category": c.category.value if hasattr(c.category, 'value') else str(c.category),
                    "prompt": c.prompt,
                    "severity": c.severity.value if hasattr(c.severity, 'value') else str(c.severity),
                }
                for c in cases[:20]  #     ?0 ?
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============       ============

__all__ = ["router"]
