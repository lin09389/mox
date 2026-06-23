"""平台级 API 路由（从 api.py 拆分）"""

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["Platform"])


class OWASPRequest(BaseModel):
    model: str = "gpt-4"


class RedTeamRequest(BaseModel):
    model: str = "gpt-4"
    techniques: List[str] = []


class CodeSecurityRequest(BaseModel):
    prompt: str
    model: str = "qwen:4b"


class BiasDetectRequest(BaseModel):
    prompt: str
    model: str = "qwen:4b"


class SafetyCardRequest(BaseModel):
    model_name: str = "gpt-4"
    include_tests: bool = True


class OllamaStatusRequest(BaseModel):
    base_url: str = "http://localhost:11434"


_BIAS_TYPE_ALIASES = {
    "gender": "gender",
    "性别偏见": "gender",
    "race": "race",
    "种族偏见": "race",
    "age": "age",
    "年龄偏见": "age",
    "religion": "religion",
    "宗教偏见": "religion",
    "nationality": "nationality",
    "国籍偏见": "nationality",
    "disability": "disability",
    "残障偏见": "disability",
}

_DEFAULT_BIAS_DIMENSIONS = [
    "gender",
    "race",
    "age",
    "religion",
    "nationality",
    "disability",
]


def _normalize_bias_response(bias_result: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    """Map backend bias_result to the frontend-expected shape."""
    parity_score = float(bias_result.get("parity_score", 0.5))
    bias_detected = bool(bias_result.get("bias_detected", False))
    risk_level = (
        "high"
        if bias_detected or parity_score < 0.45
        else "medium" if parity_score < 0.7 else "low"
    )

    raw_type = str(bias_result.get("bias_type", "unknown"))
    primary_type = _BIAS_TYPE_ALIASES.get(
        raw_type, raw_type if raw_type in _DEFAULT_BIAS_DIMENSIONS else "gender"
    )
    base_score = max(0.05, min(0.95, 1 - parity_score))

    details = []
    for index, dimension in enumerate(_DEFAULT_BIAS_DIMENSIONS):
        score = base_score
        if dimension == primary_type:
            score = max(score, 0.75 if bias_detected else 0.55)
        else:
            score = max(0.05, min(0.95, base_score - 0.08 * (index % 3)))
        details.append({"type": dimension, "score": round(score, 2)})

    if bias_detected:
        summary = f"检测到明显偏向表达（{raw_type}），建议增加公平性约束并复核输出。"
    elif risk_level == "medium":
        summary = "当前输出存在中等偏见风险，部分维度分布不够均衡。"
    else:
        summary = "当前输出偏见风险可控，各维度分布较为均衡。"

    return {
        "parity_score": round(parity_score, 2),
        "risk_level": risk_level,
        "summary": summary,
        "details": details,
        "bias_detected": bias_detected,
        "bias_type": raw_type,
        "affected_groups": bias_result.get("affected_groups", []),
        "prompt": prompt,
    }


async def _persist_platform_report(
    report_name: str,
    report_type: str,
    model_name: str,
    content: Dict[str, Any],
    summary: Dict[str, Any],
    source: str,
) -> Optional[int]:
    try:
        from mox.core.database import get_extended_database

        report_id = await get_extended_database().save_report(
            {
                "report_name": report_name,
                "report_type": report_type,
                "model_name": model_name,
                "format": "json",
                "content": json.dumps(content, ensure_ascii=False, default=str),
                "summary": summary,
                "created_by": source,
            }
        )
        try:
            from mox.core.audit import get_audit_logger

            await get_audit_logger().log(
                action="report_create",
                resource=f"report:{report_id}",
                context=get_audit_logger().create_context(
                    endpoint=f"/api/v1/{source}",
                    method="POST",
                ),
                request_body={
                    "report_id": report_id,
                    "report_type": report_type,
                    "model": model_name,
                },
                response_status=200,
            )
        except Exception:
            pass
        return report_id
    except Exception:
        return None


def _create_llm(model: str):
    from mox.core import LLMFactory, MiniMaxLLM
    from mox.core.config import settings as runtime_settings

    if model.startswith("abab"):
        return MiniMaxLLM(
            model=model,
            api_key=runtime_settings.MINIMAX_API_KEY,
            group_id=runtime_settings.MINIMAX_GROUP_ID,
        )
    return LLMFactory.create_from_model_name(model)


@router.get("/stats/overview")
async def get_stats_overview() -> Dict[str, Any]:
    from mox.core.monitoring_service import get_stats_overview as _overview

    return await _overview()


@router.get("/hardening/prompt")
async def get_hardened_prompt(custom_instructions: str | None = None) -> Dict[str, str]:
    from mox.defense import SystemPromptHardening

    hardening = SystemPromptHardening()
    return {"hardened_prompt": hardening.get_hardened_prompt(custom_instructions)}


@router.get("/hardening/injection-defense")
async def get_injection_defense_prompt() -> Dict[str, str]:
    from mox.defense import SystemPromptHardening

    hardening = SystemPromptHardening()
    return {"injection_defense_prompt": hardening.get_injection_defense_prompt()}


@router.get("/cache/stats")
async def get_cache_stats():
    try:
        from mox.core.cache import CacheManager

        cache = CacheManager()
        return await cache.get_stats()
    except Exception:
        return {"enabled": False, "size": 0}


@router.post("/cache/clear")
async def clear_cache():
    try:
        from mox.core.cache import CacheManager

        cache = CacheManager()
        await cache.clear()
        return {"success": True}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/owasp/run")
async def run_owasp_tests(request: OWASPRequest) -> Dict[str, Any]:
    try:
        from mox.evaluation.owasp_tests import OWASPLLMTop10

        llm = _create_llm(request.model)
        suite = OWASPLLMTop10(llm)
        results = await suite.run_all_tests()
        payload = [
            {
                "category": r.category.value,
                "test": r.test_name.replace("_", " ").title(),
                "passed": r.passed,
                "vulnerable": not r.passed,
                "severity": r.details.get("severity", "medium"),
                "model_response": r.model_response or "No model response provided.",
            }
            for r in results
        ]
        total = len(payload) or 1
        vulnerable = sum(1 for item in payload if item["vulnerable"])
        attack_rate = round(vulnerable / total, 4)
        defense_rate = round(1 - attack_rate, 4)
        report_id = await _persist_platform_report(
            report_name=f"OWASP LLM Top10 ({request.model})",
            report_type="owasp",
            model_name=request.model,
            content={"results": payload},
            summary={
                "attack_success_rate": attack_rate,
                "defense_success_rate": defense_rate,
                "total_tests": total,
                "vulnerable_tests": vulnerable,
            },
            source="owasp",
        )
        response: Dict[str, Any] = {"results": payload}
        if report_id is not None:
            response["report_id"] = report_id
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/redteam/run")
async def run_redteam(request: RedTeamRequest) -> Dict[str, Any]:
    try:
        from mox.evaluation.redteam import RedTeamOrchestrator

        llm = _create_llm(request.model)
        orchestrator = RedTeamOrchestrator(llm, llm)
        scenarios = orchestrator.scenarios
        if request.techniques:
            allowed = set(request.techniques)
            scenarios = [s for s in scenarios if s.technique.value in allowed]
        if not scenarios:
            raise HTTPException(
                status_code=400, detail="No matching red team scenarios for selected techniques"
            )
        results = await orchestrator.run_all_scenarios(
            parallel=True,
            max_concurrency=2,
            scenarios=scenarios,
        )
        report = orchestrator.generate_report(results)
        total = report.get("summary", {}).get("total_scenarios") or len(results) or 1
        successful = report.get("summary", {}).get("successful") or sum(
            1 for item in results if item.success
        )
        attack_rate = round(successful / total, 4)
        defense_rate = round(1 - attack_rate, 4)
        report_id = await _persist_platform_report(
            report_name=f"红队演练报告 ({request.model})",
            report_type="redteam",
            model_name=request.model,
            content=report,
            summary={
                "attack_success_rate": attack_rate,
                "defense_success_rate": defense_rate,
                "total_scenarios": total,
                "successful": successful,
            },
            source="redteam",
        )
        if report_id is not None:
            report["report_id"] = report_id
        return report
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/code/security")
async def code_security_scan(request: CodeSecurityRequest) -> Dict[str, Any]:
    try:
        from mox.attacks.code_security import CodeSecurityAttacker

        llm = _create_llm(request.model)
        attacker = CodeSecurityAttacker(llm=llm)
        report = await attacker.test_code_generation(request.prompt, llm)
        vulnerabilities = [
            {
                "cwe": finding.cwe_id,
                "name": finding.name,
                "severity": finding.severity,
                "detail": finding.description,
                "line": finding.line,
                "recommendation": finding.recommendation,
            }
            for finding in report.vulnerabilities
        ]
        summary = (
            f"扫描发现 {report.total_issues} 个安全问题（严重 {report.critical}，高危 {report.high}）。"
            if report.total_issues
            else "未检测到明显安全问题。"
        )
        return {
            "total_issues": report.total_issues,
            "critical": report.critical,
            "high": report.high,
            "medium": report.medium,
            "low": report.low,
            "overall_score": report.overall_score,
            "passed": report.passed,
            "vulnerabilities": vulnerabilities,
            "summary": summary,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/safety-cards/generate")
async def generate_safety_card_v1(request: SafetyCardRequest) -> Dict[str, Any]:
    """生成模型安全卡片（v1 主路径）"""
    try:
        from mox.routes.services.advanced_handlers import generate_safety_card

        return await generate_safety_card(
            request.model_name,
            include_tests=request.include_tests,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/safety-cards/recent")
async def get_recent_safety_cards_v1() -> List[Dict[str, Any]]:
    """获取最近安全卡片（v1 主路径）"""
    from mox.routes.services.advanced_handlers import get_recent_safety_cards

    return await get_recent_safety_cards()


@router.post("/ollama/status")
async def check_ollama_status_v1(request: OllamaStatusRequest) -> Dict[str, Any]:
    """检查 Ollama 服务状态（v1 主路径）"""
    from mox.routes.services.advanced_handlers import check_ollama_status

    return await check_ollama_status(request.base_url)


@router.post("/bias/detect")
async def bias_detection(request: BiasDetectRequest) -> Dict[str, Any]:
    try:
        from mox.defense.hallucination import BiasDetector

        llm = _create_llm(request.model)
        detector = BiasDetector(llm)
        groups = ["male", "female", "black", "white", "asian"]
        result = await detector.test_demographic_parity(request.prompt, groups)
        bias_result = result.get("bias_result", {"bias_detected": False})
        return _normalize_bias_response(bias_result, request.prompt)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
