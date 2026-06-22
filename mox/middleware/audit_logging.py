"""HTTP 审计日志中间件"""

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from mox.core.audit import AuditContext, get_audit_logger
from mox.core.logging import get_logger

logger = get_logger("audit.middleware")

_SKIP_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/metrics"}
_SKIP_PREFIXES = ("/docs", "/static")


def _derive_action(method: str, path: str) -> str:
    if "/attack" in path:
        return "attack_run"
    if "/defense" in path:
        return "defense_detect"
    if "/benchmark" in path:
        return "benchmark_run"
    if "/models" in path:
        return "model_list"
    if "/auth/login" in path:
        return "login"
    if "/auth/logout" in path:
        return "logout"
    if "/audit" in path:
        return "audit_query"
    if "/canvas" in path:
        return "canvas_run"
    if "/auto-redteam" in path:
        return "auto_redteam"
    if "/reports" in path:
        if method == "DELETE":
            return "report_delete"
        if method == "GET" and "/download" in path:
            return "report_download"
        return "report_query"
    if "/datasets" in path:
        if method == "DELETE":
            return "dataset_delete"
        if method == "POST":
            return "dataset_upload"
        return "dataset_query"
    if "/auth/register" in path:
        return "register"
    if "/user-templates" in path:
        if method == "DELETE":
            return "template_delete"
        if method == "POST":
            return "template_create" if not path.rstrip("/").split("/")[-1].isdigit() else "template_update"
        if method == "PUT":
            return "template_update"
        return "template_query"
    return f"{method.lower()}_{path.strip('/').replace('/', '_') or 'root'}"


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """记录 API 请求到审计日志"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if path in _SKIP_PATHS or any(path.startswith(p) for p in _SKIP_PREFIXES):
            return await call_next(request)
        if not path.startswith("/api"):
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)

        user_id = None
        username = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from mox.core.auth import AuthManager

                token_data = AuthManager.verify_token(auth_header[7:])
                user_id = str(token_data.sub)
                username = token_data.sub
            except Exception:
                pass

        context = AuditContext(
            user_id=user_id,
            username=username,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            endpoint=path,
            method=request.method,
        )

        try:
            audit_logger = get_audit_logger()
            await audit_logger.log(
                action=_derive_action(request.method, path),
                resource=path,
                context=context,
                response_status=response.status_code,
                duration_ms=duration_ms,
                is_sensitive="/auth" in path,
            )
        except Exception as exc:
            logger.error(f"Audit log failed for {path}: {exc}")

        return response