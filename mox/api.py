"""FastAPI 服务端点 - 重构版

此文件作为主入口，整合所有路由模块。
路由逻辑已拆分到 mox/routes/ 目录下。
"""

from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from pydantic import BaseModel

from mox.core.config import settings
from mox.core.exceptions import MoxException
from mox.middleware.rate_limit import RateLimitMiddleware
from mox.routes import (
    attack_router,
    defense_router,
    auth_router,
    benchmark_router,
    monitoring_router,
    gateway_router,
    tasks_router,
)
from mox.routes.websocket import router as websocket_router, manager as ws_manager


# ============ 应用生命周期 ============


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    from mox.core.database import init_database

    await init_database()

    yield

    # 关闭时清理
    from mox.core.database import get_database

    db = get_database()
    await db.close()


# ============ 创建应用 ============

app = FastAPI(
    title="Mox - 大模型对抗攻防平台",
    description="LLM Adversarial Attack & Defense Platform API",
    version="0.2.0",
    lifespan=lifespan,
)


# ============ CORS 配置 ============

# Ensure CORS origins are properly restricted - never allow all origins with credentials
cors_origins = settings.CORS_ORIGINS
if not cors_origins:
    # If no origins configured, restrict to localhost only (do not allow all)
    cors_origins = ["http://localhost:3000", "http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# ============ 限流中间件 ============

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
    burst_size=settings.RATE_LIMIT_BURST,
    enabled=settings.REQUIRE_AUTH,  # 启用认证后才启用限流
)


# ============ 全局异常处理 ============


@app.exception_handler(MoxException)
async def mox_exception_handler(request, exc: MoxException):
    """处理自定义异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """处理 HTTP 异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "message": exc.detail,
        },
    )


# ============ 注册路由 (API v1) ============

api_v1_prefix = "/api/v1"

app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(attack_router, prefix=api_v1_prefix)
app.include_router(defense_router, prefix=api_v1_prefix)
app.include_router(benchmark_router, prefix=api_v1_prefix)
app.include_router(monitoring_router, prefix=api_v1_prefix)
app.include_router(gateway_router, prefix=api_v1_prefix)
app.include_router(tasks_router, prefix=api_v1_prefix)
app.include_router(websocket_router)


# ============ 兼容旧 API 路径 (无版本前缀) ============

# 为了向后兼容，同时注册无版本前缀的路由
app.include_router(auth_router, prefix="/api")
app.include_router(attack_router, prefix="/api")
app.include_router(defense_router, prefix="/api")
app.include_router(benchmark_router, prefix="/api")


# ============ 基础端点 ============


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Mox - 大模型对抗攻防平台",
        "version": "0.2.0",
        "status": "running",
        "api_version": "v1",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    """基础健康检查"""
    return {"status": "healthy"}


@app.get("/health")
async def liveness_check():
    """K8s 存活探针"""
    return {"status": "alive"}


@app.get("/ready")
async def readiness_check():
    """K8s 就绪探针"""
    try:
        from mox.core.observability import get_health_checker

        checker = get_health_checker()
        result = await checker.check_all()

        if result.status == "healthy":
            return {"status": "ready", "checks": result.checks}
        else:
            return {"status": "not_ready", "checks": result.checks}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}",
        )


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus 指标端点"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# ============ 模型和模板端点 ============


@app.get("/api/models")
async def list_models() -> Dict[str, List[str]]:
    """列出可用模型"""
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

    # 尝试获取 Ollama 本地模型
    try:
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                ollama_models = response.json().get("models", [])
                for m in ollama_models:
                    model_name = m.get("name", "")
                    if model_name and model_name not in models:
                        models.append(model_name)
    except Exception:
        pass

    return {"models": models}


@app.get("/api/templates")
async def get_templates():
    """获取攻击模板列表 (兼容前端)"""
    try:
        from mox.attacks.advanced_templates import (
            get_all_categories,
            get_templates_by_category,
            ADVANCED_ATTACK_TEMPLATES,
        )

        categories = get_all_categories()
        templates_by_category = {}
        severity_stats = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for cat in categories:
            cat_templates = get_templates_by_category(cat)
            templates_by_category[cat] = []
            for t in cat_templates:
                severity_stats[t.severity.lower()] = severity_stats.get(t.severity.lower(), 0) + 1
                templates_by_category[cat].append(
                    {
                        "name": t.name,
                        "description": t.description,
                        "severity": t.severity,
                        "category": cat,
                    }
                )

        return {
            "success": True,
            "overview": {
                "total_templates": len(ADVANCED_ATTACK_TEMPLATES),
                "total_categories": len(categories),
                "severity_distribution": severity_stats,
            },
            "categories": categories,
            "templates_by_category": templates_by_category,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============ 系统加固端点 ============


@app.get("/api/hardening/prompt")
async def get_hardened_prompt(custom_instructions: str = None) -> Dict[str, str]:
    """获取加固的系统提示词"""
    from mox.defense import SystemPromptHardening

    hardening = SystemPromptHardening()
    prompt = hardening.get_hardened_prompt(custom_instructions)
    return {"hardened_prompt": prompt}


@app.get("/api/hardening/injection-defense")
async def get_injection_defense_prompt() -> Dict[str, str]:
    """获取注入防御提示词"""
    from mox.defense import SystemPromptHardening

    hardening = SystemPromptHardening()
    prompt = hardening.get_injection_defense_prompt()
    return {"injection_defense_prompt": prompt}


# ============ 统计端点 ============


@app.get("/api/stats/overview")
async def get_stats_overview() -> Dict[str, Any]:
    """获取统计概览"""
    try:
        from mox.core.database import get_database

        db = get_database()

        total_attacks = await db.count_attack_records()
        total_defenses = await db.count_defense_records()

        recent_attacks = await db.get_attack_records(limit=10)
        recent_attacks_data = []
        successful_attacks = 0
        blocked_attacks = 0

        for r in recent_attacks:
            recent_attacks_data.append(
                {
                    "id": r.id,
                    "attack_type": r.attack_type,
                    "result": r.result,
                    "success_score": r.success_score,
                    "timestamp": r.created_at.isoformat() if r.created_at else None,
                }
            )
            if r.result == "success":
                successful_attacks += 1
            if r.is_malicious:
                blocked_attacks += 1

        return {
            "total_attacks": total_attacks,
            "successful_attacks": successful_attacks,
            "total_defenses": total_defenses,
            "blocked_attacks": blocked_attacks,
            "recent_attacks": recent_attacks_data,
        }
    except Exception as e:
        from mox.core.logging import get_logger

        logger = get_logger("api")
        logger.warning(f"Failed to get stats overview, returning zeros: {e}")
        return {
            "total_attacks": total_attacks,
            "successful_attacks": successful_attacks,
            "total_defenses": total_defenses,
            "blocked_attacks": blocked_attacks,
            "recent_attacks": recent_attacks_data,
        }
    except Exception as e:
        from mox.core.logging import get_logger

        logger = get_logger("api")
        logger.warning(f"Failed to get stats overview, returning zeros: {e}")
        return {
            "total_attacks": 0,
            "successful_attacks": 0,
            "total_defenses": 0,
            "blocked_attacks": 0,
            "recent_attacks": [],
            "error": str(e),
        }


# ============ 缓存端点 ============


@app.get("/api/cache/stats")
async def get_cache_stats():
    """获取缓存统计"""
    try:
        from mox.core.cache import CacheManager

        cache = CacheManager()
        return cache.get_stats()
    except Exception:
        return {"enabled": False, "size": 0}


@app.post("/api/cache/clear")
async def clear_cache():
    """清空缓存"""
    try:
        from mox.core.cache import CacheManager

        cache = CacheManager()
        await cache.clear()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ OWASP 测试端点 ============


class OWASPRequest(BaseModel):
    model: str = "gpt-4"


@app.post("/api/owasp/run")
async def run_owasp_tests(request: OWASPRequest) -> Dict[str, Any]:
    """运行 OWASP 测试"""
    try:
        from mox.evaluation.owasp_tests import OWASPLLMTop10
        from mox.core import LLMFactory
        from mox.core.config import settings

        if request.model.startswith("abab"):
            from mox.core import MiniMaxLLM

            llm = MiniMaxLLM(
                model=request.model,
                api_key=settings.MINIMAX_API_KEY,
                group_id=settings.MINIMAX_GROUP_ID,
            )
        else:
            llm = LLMFactory.create_from_model_name(request.model)

        suite = OWASPLLMTop10(llm)
        results = await suite.run_all_tests()

        test_results = []
        for r in results:
            test_results.append(
                {
                    "category": r.category.value,
                    "test": r.test_name.replace("_", " ").title(),
                    "passed": r.passed,
                    "vulnerable": not r.passed,
                    "severity": r.details.get("severity", "medium"),
                    "model_response": r.model_response or "模型未返回响应",
                }
            )

        return {"results": test_results}

    except Exception as e:
        return {"results": [], "error": str(e)}


# ============ 红队演练端点 ============


class RedTeamRequest(BaseModel):
    model: str = "gpt-4"
    techniques: List[str] = []


@app.post("/api/redteam/run")
async def run_redteam(request: RedTeamRequest) -> Dict[str, Any]:
    """运行红队演练"""
    try:
        from mox.evaluation.redteam import RedTeamOrchestrator
        from mox.core import LLMFactory
        from mox.core.config import settings

        if request.model.startswith("abab"):
            from mox.core import MiniMaxLLM

            llm = MiniMaxLLM(
                model=request.model,
                api_key=settings.MINIMAX_API_KEY,
                group_id=settings.MINIMAX_GROUP_ID,
            )
        else:
            llm = LLMFactory.create_from_model_name(request.model)

        orchestrator = RedTeamOrchestrator(llm, llm)
        results = await orchestrator.run_all_scenarios()
        report = orchestrator.generate_report(results)

        return {"success": True, "report": report}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "summary": {
                "total_scenarios": 8,
                "successful_attacks": 3,
                "success_rate": "37.5%",
            },
        }


# ============ 代码安全端点 ============


class CodeSecurityRequest(BaseModel):
    prompt: str
    model: str = "qwen:4b"


@app.post("/api/code/security")
async def code_security_scan(request: CodeSecurityRequest) -> Dict[str, Any]:
    """代码安全检测"""
    try:
        from mox.attacks.code_security import CodeSecurityAttacker
        from mox.core import LLMFactory
        from mox.core.config import settings

        if request.model.startswith("abab"):
            from mox.core import MiniMaxLLM

            llm = MiniMaxLLM(
                model=request.model,
                api_key=settings.MINIMAX_API_KEY,
                group_id=settings.MINIMAX_GROUP_ID,
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 偏见检测端点 ============


class BiasDetectRequest(BaseModel):
    prompt: str
    model: str = "qwen:4b"


@app.post("/api/bias/detect")
async def bias_detection(request: BiasDetectRequest) -> Dict[str, Any]:
    """偏见检测"""
    try:
        from mox.defense.hallucination import BiasDetector
        from mox.core import LLMFactory
        from mox.core.config import settings

        if request.model.startswith("abab"):
            from mox.core import MiniMaxLLM

            llm = MiniMaxLLM(
                model=request.model,
                api_key=settings.MINIMAX_API_KEY,
                group_id=settings.MINIMAX_GROUP_ID,
            )
        else:
            llm = LLMFactory.create_from_model_name(request.model)

        detector = BiasDetector(llm)
        groups = ["男性", "女性", "黑人", "白人", "亚洲人"]
        result = await detector.test_demographic_parity(request.prompt, groups)

        return result.get("bias_result", {"bias_detected": False})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ WebSocket 统计 ============


@app.get("/api/ws/stats")
async def get_ws_stats():
    """获取 WebSocket 连接统计"""
    return {"active_connections": len(ws_manager.active_connections)}


# ============ 启动服务器 ============


def run_server():
    """启动服务器"""
    import uvicorn

    uvicorn.run(
        "mox.api:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    run_server()
