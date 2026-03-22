"""LLM 网关相关路由"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, validator
from urllib.parse import urlparse

from mox.core.auth import User, get_current_active_user

router = APIRouter(prefix="/gateway", tags=["Gateway"])


# ============ 请求模型 ============

class GatewayRequest(BaseModel):
    input: str


class AddEndpointRequest(BaseModel):
    name: str
    provider: str
    model: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    weight: float = 1.0
    max_rpm: int = 100
    max_tpm: int = 100000

    @validator("base_url")
    def validate_base_url(cls, v):
        if v:
            parsed = urlparse(v)
            if parsed.scheme not in ("http", "https"):
                raise ValueError("URL must start with http or https")
            if parsed.hostname in ("localhost", "127.0.0.1", "0.0.0.0") or parsed.hostname.endswith(".local"):
                raise ValueError("Internal addresses are not allowed")
        return v


# ============ 路由端点 ============

@router.post("/validate")
async def validate_gateway(request: GatewayRequest) -> Dict[str, Any]:
    """验证输入网关"""
    try:
        from mox.core.gateway import InputGateway, GatewayConfig

        config = GatewayConfig()
        gateway = InputGateway(config=config)
        result = await gateway.validate(request.input)

        return {
            "decision": result.decision.value,
            "confidence": result.confidence,
            "reason": result.reason,
            "matched_rules": result.matched_rules,
        }
    except Exception:
        return {"decision": "allow", "confidence": 0, "reason": "Gateway validation failed"}


@router.get("/stats")
async def get_gateway_stats():
    """获取LLM网关统计"""
    try:
        from mox.core.llm_gateway import get_llm_gateway
        gateway = get_llm_gateway()
        return gateway.get_stats()
    except Exception:
        return {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_latency_ms": 0,
        }


@router.post("/endpoints")
async def add_gateway_endpoint(
    request: AddEndpointRequest,
    current_user: User = Depends(get_current_active_user),
):
    """添加LLM端点"""
    if "admin" not in (current_user.scopes or []):
        raise HTTPException(status_code=403, detail="Admin scope required")

    try:
        from mox.core.llm_gateway import get_llm_gateway
        from mox.core.llm import ModelProvider

        gateway = get_llm_gateway()
        gateway.add_endpoint(
            name=request.name,
            provider=ModelProvider(request.provider),
            model=request.model,
            base_url=request.base_url,
            api_key=request.api_key,
            weight=request.weight,
            max_rpm=request.max_rpm,
            max_tpm=request.max_tpm,
        )

        return {"success": True, "endpoint": request.name}
    except Exception:
        raise HTTPException(status_code=500, detail="Gateway operation failed")


@router.delete("/endpoints/{name}")
async def remove_gateway_endpoint(
    name: str,
    current_user: User = Depends(get_current_active_user),
):
    """删除LLM端点"""
    if "admin" not in (current_user.scopes or []):
        raise HTTPException(status_code=403, detail="Admin scope required")

    try:
        from mox.core.llm_gateway import get_llm_gateway
        gateway = get_llm_gateway()
        gateway.remove_endpoint(name)
        return {"success": True}
    except Exception:
        raise HTTPException(status_code=500, detail="Gateway operation failed")