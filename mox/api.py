"""FastAPI service entrypoint and app factory."""

from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Request, Response, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from mox.infrastructure.auth import get_current_active_user, User

from mox.infrastructure.config import settings
from mox.core.exceptions import MoxException
from mox.core.version import PACKAGE_VERSION
from mox.middleware.rate_limit import RateLimitMiddleware
from mox.routes import (
    attack_router,
    auth_router,
    benchmark_router,
    defense_router,
    gateway_router,
    monitoring_router,
    tasks_router,
)
from mox.routes.api_v2 import router as api_v2_router
from mox.routes.websocket import manager as ws_manager
from mox.routes.websocket import router as websocket_router

API_V1_PREFIX = "/api/v1"
COMPAT_PREFIX = "/api"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown resources."""
    from mox.infrastructure.database import get_database, init_database
    from mox.infrastructure.event_handlers import register_persistence_handlers

    await init_database()
    register_persistence_handlers()
    yield

    db = get_database()
    await db.close()


def _get_cors_origins() -> list[str]:
    if settings.CORS_ORIGINS:
        # Extend with additional localhost ports if not already included
        origins = list(settings.CORS_ORIGINS)
        extra_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://localhost:3003",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:3002",
            "http://127.0.0.1:3003",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
        ]
        for origin in extra_origins:
            if origin not in origins:
                origins.append(origin)
        return origins
    # Allow all localhost ports for development
    return [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]


def _register_middleware(app: FastAPI) -> None:
    cors_origins = _get_cors_origins()
    allow_credentials = settings.CORS_ALLOW_CREDENTIALS
    if cors_origins == ["*"]:
        allow_credentials = False
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
        burst_size=settings.RATE_LIMIT_BURST,
        enabled=True,
    )

    @app.middleware("http")
    async def add_compatibility_headers(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith(f"{COMPAT_PREFIX}/") and not request.url.path.startswith(
            f"{API_V1_PREFIX}/"
        ):
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = "2026-12-31"
            response.headers["Link"] = f'<{API_V1_PREFIX}>; rel="successor-version"'
        return response


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(MoxException)
    async def mox_exception_handler(request: Request, exc: MoxException):
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "HTTP_ERROR", "message": exc.detail},
        )


def _register_routers(app: FastAPI) -> None:
    app.include_router(auth_router, prefix=API_V1_PREFIX)
    app.include_router(attack_router, prefix=API_V1_PREFIX)
    app.include_router(defense_router, prefix=API_V1_PREFIX)
    app.include_router(benchmark_router, prefix=API_V1_PREFIX)
    app.include_router(monitoring_router, prefix=API_V1_PREFIX)
    app.include_router(gateway_router, prefix=API_V1_PREFIX)
    app.include_router(tasks_router, prefix=API_V1_PREFIX)
    app.include_router(websocket_router)
    app.include_router(api_v2_router)

    # Temporary compatibility during migration to /api/v1.
    app.include_router(auth_router, prefix=COMPAT_PREFIX)
    app.include_router(attack_router, prefix=COMPAT_PREFIX)
    app.include_router(defense_router, prefix=COMPAT_PREFIX)
    app.include_router(benchmark_router, prefix=COMPAT_PREFIX)
    app.include_router(monitoring_router, prefix=COMPAT_PREFIX)
    app.include_router(gateway_router, prefix=COMPAT_PREFIX)
    app.include_router(tasks_router, prefix=COMPAT_PREFIX)


def create_app() -> FastAPI:
    application = FastAPI(
        title="Mox - LLM Adversarial Attack and Defense Platform",
        description="LLM Adversarial Attack and Defense Platform API",
        version=PACKAGE_VERSION,
        lifespan=lifespan,
    )
    _register_middleware(application)
    _register_exception_handlers(application)
    _register_routers(application)
    return application


app = create_app()

from fastapi import APIRouter
api_router = APIRouter()


@app.get("/")
async def root():
    """Return service metadata."""
    return {
        "name": "Mox - LLM Adversarial Attack & Defense Platform",
        "version": PACKAGE_VERSION,
        "status": "running",
        "api_version": "v1",
        "docs": "/docs",
    }


@api_router.get("/health")
async def health_check():
    """Return API health."""
    return {"status": "healthy"}


@app.get("/health")
async def liveness_check():
    """Return liveness status."""
    return {"status": "alive"}


@app.get("/ready")
async def readiness_check():
    """Return readiness status."""
    try:
        from mox.infrastructure.observability import get_health_checker

        checker = get_health_checker()
        result = await checker.check_all()

        if result.status == "healthy":
            return {"status": "ready", "checks": result.checks}
        return {"status": "not_ready", "checks": result.checks}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {exc}",
        ) from exc


@app.get("/metrics")
async def prometheus_metrics():
    """Expose Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@api_router.get("/models")
async def list_models() -> Dict[str, List[str]]:
    """List supported models."""
    models = [
        "qwen3:4b",
        "qwen2.5:14b",
        "llama3:8b",
        "abab2.5-chat",
        "abab6.5s-chat",
        "abab6.5g-chat",
        "abab6.5t-chat",
        "abab5.5-chat",
        "gpt-4",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-sonnet-4-20250514",
        "gemini-2.0-flash",
    ]

    try:
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                for model_info in response.json().get("models", []):
                    model_name = model_info.get("name", "")
                    if model_name and model_name not in models:
                        models.append(model_name)
    except Exception as e:
        from mox.infrastructure.logging import get_logger

        logger = get_logger("api")
        logger.warning(f"Failed to discover Ollama models: {e}")

    return {"models": models}


@api_router.get("/templates")
async def get_templates():
    """Return attack templates for the frontend."""
    try:
        from mox.attacks.advanced_templates import (
            ADVANCED_ATTACK_TEMPLATES,
            get_all_categories,
            get_templates_by_category,
        )

        categories = get_all_categories()
        templates_by_category: Dict[str, Any] = {}
        severity_stats = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for category in categories:
            templates = get_templates_by_category(category)
            templates_by_category[category] = [
                {
                    "id": template.id,
                    "name": template.name,
                    "description": template.description,
                    "severity": template.severity,
                    "category": template.category,
                    "template": template.template,
                    "targets": template.targets,
                }
                for template in templates
            ]

        for template in ADVANCED_ATTACK_TEMPLATES:
            if template.severity in severity_stats:
                severity_stats[template.severity] += 1

        return {
            "success": True,
            "summary": {
                "total_templates": len(ADVANCED_ATTACK_TEMPLATES),
                "severity_stats": severity_stats,
            },
            "categories": categories,
            "templates_by_category": templates_by_category,
        }
    except Exception as exc:
        from mox.infrastructure.logging import get_logger

        logger = get_logger("api")
        logger.error(f"Failed to get templates: {exc}")
        return {"success": False, "error": "Failed to load templates"}


@api_router.get("/hardening/prompt")
async def get_hardened_prompt(custom_instructions: str | None = None) -> Dict[str, str]:
    """Generate a hardened system prompt."""
    from mox.defense import SystemPromptHardening

    hardening = SystemPromptHardening()
    prompt = hardening.get_hardened_prompt(custom_instructions)
    return {"hardened_prompt": prompt}


@api_router.get("/hardening/injection-defense")
async def get_injection_defense_prompt() -> Dict[str, str]:
    """Generate an injection defense prompt."""
    from mox.defense import SystemPromptHardening

    hardening = SystemPromptHardening()
    prompt = hardening.get_injection_defense_prompt()
    return {"injection_defense_prompt": prompt}


@api_router.get("/stats/overview")
async def get_stats_overview() -> Dict[str, Any]:
    """Return dashboard overview statistics."""
    total_attacks = 0
    successful_attacks = 0
    total_defenses = 0
    blocked_attacks = 0
    recent_attacks_data: List[Dict[str, Any]] = []

    try:
        from mox.infrastructure.database import get_database

        db = get_database()
        total_attacks = await db.count_attack_records()
        total_defenses = await db.count_defense_records()

        recent_attacks = await db.get_attack_records(limit=10)
        for record in recent_attacks:
            recent_attacks_data.append(
                {
                    "id": record.id,
                    "attack_type": record.attack_type,
                    "result": record.result,
                    "success_score": record.success_score,
                    "timestamp": record.created_at.isoformat() if record.created_at else None,
                }
            )
            if record.result == "success":
                successful_attacks += 1
            if record.is_malicious:
                blocked_attacks += 1

        return {
            "total_attacks": total_attacks,
            "successful_attacks": successful_attacks,
            "total_defenses": total_defenses,
            "blocked_attacks": blocked_attacks,
            "recent_attacks": recent_attacks_data,
        }
    except Exception as exc:
        from mox.infrastructure.logging import get_logger

        logger = get_logger("api")
        logger.error(f"Failed to get stats overview: {exc}")
        return {
            "total_attacks": total_attacks,
            "successful_attacks": successful_attacks,
            "total_defenses": total_defenses,
            "blocked_attacks": blocked_attacks,
            "recent_attacks": recent_attacks_data,
        }


@api_router.get("/cache/stats")
async def get_cache_stats():
    """Return cache statistics."""
    try:
        from mox.infrastructure.cache import CacheManager

        cache = CacheManager()
        return cache.get_stats()
    except Exception as e:
        from mox.infrastructure.logging import get_logger

        logger = get_logger("api")
        logger.error(f"Failed to get cache stats: {e}")
        return {"enabled": False, "size": 0}


@api_router.post("/cache/clear")
async def clear_cache(current_user: User = Depends(get_current_active_user)):
    """Clear runtime caches."""
    try:
        from mox.infrastructure.cache import CacheManager

        cache = CacheManager()
        await cache.clear()
        return {"success": True}
    except Exception as exc:
        from mox.infrastructure.logging import get_logger

        logger = get_logger("api")
        logger.error(f"Failed to clear cache: {exc}")
        raise HTTPException(status_code=500, detail="Failed to clear cache") from exc


class OWASPRequest(BaseModel):
    model: str = "gpt-4"


@api_router.post("/owasp/run")
async def run_owasp_tests(request: OWASPRequest) -> Dict[str, Any]:
    """Run the OWASP LLM test suite."""
    try:
        from mox.core import LLMFactory, MiniMaxLLM
        from mox.infrastructure.config import settings as runtime_settings
        from mox.evaluation.owasp_tests import OWASPLLMTop10

        if request.model.startswith("abab"):
            llm = MiniMaxLLM(
                model=request.model,
                api_key=runtime_settings.MINIMAX_API_KEY,
                group_id=runtime_settings.MINIMAX_GROUP_ID,
            )
        else:
            llm = LLMFactory.create_from_model_name(request.model)

        suite = OWASPLLMTop10(llm)
        results = await suite.run_all_tests()

        test_results = []
        for result in results:
            test_results.append(
                {
                    "category": result.category.value,
                    "test": result.test_name.replace("_", " ").title(),
                    "passed": result.passed,
                    "vulnerable": not result.passed,
                    "severity": result.details.get("severity", "medium"),
                    "model_response": result.model_response or "No model response provided.",
                }
            )

        return {"results": test_results}
    except Exception as exc:
        from mox.infrastructure.logging import get_logger

        logger = get_logger("api")
        logger.error(f"OWASP test execution failed: {exc}")
        return {"results": [], "error": "OWASP test execution failed"}


class RedTeamRequest(BaseModel):
    model: str = "gpt-4"
    techniques: List[str] = []


@api_router.post("/redteam/run")
async def run_redteam(request: RedTeamRequest) -> Dict[str, Any]:
    """Run the red-team orchestrator."""
    try:
        from mox.core import LLMFactory, MiniMaxLLM
        from mox.infrastructure.config import settings as runtime_settings
        from mox.evaluation.redteam import RedTeamOrchestrator

        if request.model.startswith("abab"):
            llm = MiniMaxLLM(
                model=request.model,
                api_key=runtime_settings.MINIMAX_API_KEY,
                group_id=runtime_settings.MINIMAX_GROUP_ID,
            )
        else:
            llm = LLMFactory.create_from_model_name(request.model)

        orchestrator = RedTeamOrchestrator(llm)
        return await orchestrator.run_comprehensive_evaluation(techniques=request.techniques)
    except Exception as exc:
        from mox.infrastructure.logging import get_logger

        logger = get_logger("api")
        logger.error(f"Red team execution failed: {exc}")
        return {
            "results": [],
            "error": "Red team execution failed",
            "summary": {
                "total_scenarios": 0,
                "successful_attacks": 0,
                "success_rate": "0%",
            },
        }


class CodeSecurityRequest(BaseModel):
    prompt: str
    model: str = "qwen:4b"


@api_router.post("/code/security")
async def code_security_scan(request: CodeSecurityRequest) -> Dict[str, Any]:
    """Run code generation security checks."""
    try:
        from mox.attacks.code_security import CodeSecurityAttacker
        from mox.core import LLMFactory, MiniMaxLLM
        from mox.infrastructure.config import settings as runtime_settings

        if request.model.startswith("abab"):
            llm = MiniMaxLLM(
                model=request.model,
                api_key=runtime_settings.MINIMAX_API_KEY,
                group_id=runtime_settings.MINIMAX_GROUP_ID,
            )
        else:
            llm = LLMFactory.create_from_model_name(request.model)

        attacker = CodeSecurityAttacker(llm=llm)
        report = await attacker.test_code_generation(request.prompt, llm)

        return {
            "total_issues": report.total_issues,
            "critical": report.critical,
            "high": report.high,
            "medium": report.medium,
            "low": report.low,
            "overall_score": report.overall_score,
            "passed": report.passed,
        }
    except Exception as exc:
        from mox.infrastructure.logging import get_logger

        logger = get_logger("api")
        logger.error(f"Code security scan failed: {exc}")
        raise HTTPException(status_code=500, detail="Code security scan failed") from exc


class BiasDetectRequest(BaseModel):
    prompt: str
    model: str = "qwen:4b"


@api_router.post("/bias/detect")
async def bias_detection(request: BiasDetectRequest) -> Dict[str, Any]:
    """Run demographic bias detection."""
    try:
        from mox.core import LLMFactory, MiniMaxLLM
        from mox.infrastructure.config import settings as runtime_settings
        from mox.defense.hallucination import BiasDetector

        if request.model.startswith("abab"):
            llm = MiniMaxLLM(
                model=request.model,
                api_key=runtime_settings.MINIMAX_API_KEY,
                group_id=runtime_settings.MINIMAX_GROUP_ID,
            )
        else:
            llm = LLMFactory.create_from_model_name(request.model)

        detector = BiasDetector(llm)
        groups = ["male", "female", "black", "white", "asian"]
        result = await detector.test_demographic_parity(request.prompt, groups)
        return result.get("bias_result", {"bias_detected": False})
    except Exception as exc:
        from mox.infrastructure.logging import get_logger

        logger = get_logger("api")
        logger.error(f"Bias detection failed: {exc}")
        raise HTTPException(status_code=500, detail="Bias detection failed") from exc


@api_router.get("/ws/stats")
async def get_ws_stats():
    """Return WebSocket connection statistics."""
    return {"active_connections": len(ws_manager.active_connections)}


app.include_router(api_router, prefix=API_V1_PREFIX)
app.include_router(api_router, prefix=COMPAT_PREFIX)

def run_server():
    """Run the API server with Uvicorn."""
    import uvicorn

    uvicorn.run(
        "mox.api:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    run_server()
