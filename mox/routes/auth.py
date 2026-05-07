"""认证相关路由"""

from datetime import timedelta, datetime
from collections import defaultdict
from typing import List, Dict
import asyncio

from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel

from mox.infrastructure.auth import (
    auth_manager,
    TokenManager,
    get_current_active_user,
    User,
)
from mox.infrastructure.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

_login_attempts: Dict[str, List[datetime]] = defaultdict(list)
_login_lock = asyncio.Lock()


async def _check_login_lockout(ip: str) -> bool:
    async with _login_lock:
        now = datetime.now()
        cutoff = now - timedelta(minutes=settings.LOGIN_LOCKOUT_DURATION_MINUTES)
        _login_attempts[ip] = [t for t in _login_attempts[ip] if t > cutoff]
        return len(_login_attempts[ip]) >= settings.MAX_LOGIN_ATTEMPTS


async def _record_failed_login(ip: str):
    async with _login_lock:
        _login_attempts[ip].append(datetime.now())


# ============ 请求/响应模型 ============

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800
    user: dict


class TokenRefreshRequest(BaseModel):
    refresh_token: str


# ============ 路由端点 ============

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, http_request: Request):
    """用户登录"""
    client_ip = http_request.client.host if http_request.client else "unknown"

    if await _check_login_lockout(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {settings.LOGIN_LOCKOUT_DURATION_MINUTES} minutes.",
        )

    user = auth_manager.authenticate_user(request.username, request.password)
    if not user:
        await _record_failed_login(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = TokenManager.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return LoginResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "username": user.username,
            "email": user.email,
            "scopes": user.scopes,
        },
    )


@router.post("/refresh")
async def refresh_token(request: TokenRefreshRequest):
    """刷新Token"""
    try:
        from jose import jwt, JWTError

        # Verify algorithm header to prevent algorithm confusion attacks
        unverified_header = jwt.get_unverified_header(request.refresh_token)
        if unverified_header.get("alg") != "HS256":
            raise HTTPException(status_code=401, detail="Invalid token algorithm")

        payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        access_token = TokenManager.create_access_token(
            data={"sub": username},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "scopes": current_user.scopes,
        "disabled": current_user.disabled,
    }