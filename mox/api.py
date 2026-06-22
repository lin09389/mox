"""FastAPI service entrypoint and app factory."""

from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from mox.core.config import settings
from mox.core.exceptions import MoxException
from mox.core.version import PACKAGE_VERSION
from mox.middleware.rate_limit import RateLimitMiddleware
from mox.middleware.audit_logging import AuditLoggingMiddleware
from mox.routes import (
    attack_router,
    audit_router,
    platform_router,
    datasets_router,
    reports_router,
    user_templates_router,
    auth_router,
    benchmark_router,
    defense_router,
    gateway_router,
    monitoring_router,
    tasks_router,
)
from mox.routes.attack_loop import router as attack_loop_router
from mox.routes.auto_redteam import router as auto_redteam_router
from mox.routes.api_v2 import router as api_v2_router
from mox.routes.canvas import router as canvas_router
from mox.routes.websocket import manager as ws_manager
from mox.routes.websocket import router as websocket_router

API_V1_PREFIX = "/api/v1"
COMPAT_PREFIX = "/api"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown resources."""
    from mox.core.database import init_database

    await init_database()

    from mox.core.user_store import load_users_into_auth_manager

    await load_users_into_auth_manager()

    from mox.core.tasks import get_task_queue

    task_queue = get_task_queue()
    await task_queue.start()

    yield

    await task_queue.stop()
    from mox.core.database import close_database

    await close_database()


def _get_cors_origins() -> list[str]:
    if settings.CORS_ORIGINS:
        return settings.CORS_ORIGINS
    return ["http://localhost:3000", "http://localhost:5173"]


def _register_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_get_cors_origins(),
        allow_credentials=True,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    app.add_middleware(AuditLoggingMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
        burst_size=settings.RATE_LIMIT_BURST,
        enabled=settings.REQUIRE_AUTH,
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
    app.include_router(attack_loop_router, prefix=API_V1_PREFIX)
    app.include_router(auto_redteam_router, prefix=f"{API_V1_PREFIX}/auto-redteam")
    app.include_router(canvas_router, prefix=API_V1_PREFIX)
    app.include_router(defense_router, prefix=API_V1_PREFIX)
    app.include_router(benchmark_router, prefix=API_V1_PREFIX)
    app.include_router(monitoring_router, prefix=API_V1_PREFIX)
    app.include_router(gateway_router, prefix=API_V1_PREFIX)
    app.include_router(tasks_router, prefix=API_V1_PREFIX)
    app.include_router(audit_router, prefix=API_V1_PREFIX)
    app.include_router(platform_router, prefix=API_V1_PREFIX)
    app.include_router(datasets_router, prefix=API_V1_PREFIX)
    app.include_router(reports_router, prefix=API_V1_PREFIX)
    app.include_router(user_templates_router, prefix=API_V1_PREFIX)
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
    app.include_router(audit_router, prefix=COMPAT_PREFIX)
    app.include_router(platform_router, prefix=COMPAT_PREFIX)
    app.include_router(datasets_router, prefix=COMPAT_PREFIX)
    app.include_router(reports_router, prefix=COMPAT_PREFIX)
    app.include_router(user_templates_router, prefix=COMPAT_PREFIX)


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


@app.get(f"{API_V1_PREFIX}/health")
@app.get(f"{COMPAT_PREFIX}/health")
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
        from mox.core.observability import get_health_checker

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


@app.get(f"{API_V1_PREFIX}/models")
@app.get(f"{COMPAT_PREFIX}/models")
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
    except Exception as exc:
        from mox.core.logging import get_logger
        get_logger("api").debug(f"Ollama 模型发现失败（Ollama 可能未运行）: {exc}")

    return {"models": models}


@app.get(f"{API_V1_PREFIX}/templates")
@app.get(f"{COMPAT_PREFIX}/templates")
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
        return {"success": False, "error": str(exc)}


@app.get(f"{API_V1_PREFIX}/ws/stats")
@app.get(f"{COMPAT_PREFIX}/ws/stats")
async def get_ws_stats():
    """Return WebSocket connection statistics."""
    return {"active_connections": len(ws_manager.active_connections)}


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
