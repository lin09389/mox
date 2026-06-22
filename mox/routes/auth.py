"""认证相关路由"""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from mox.core.auth import (
    auth_manager,
    TokenManager,
    get_current_active_user,
    User,
)
from mox.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============ 请求/响应模型 ============


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800
    user: dict


class TokenRefreshRequest(BaseModel):
    refresh_token: str


# ============ 路由端点 ============


@router.post("/register")
async def register(request: RegisterRequest):
    """注册新用户（持久化至统一数据库，重启后仍可用）。"""
    from mox.core.database import get_extended_database
    from mox.core.user_store import persist_user_account

    if auth_manager.get_user(request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    existing = await get_extended_database().get_user_account(request.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    user = User(
        username=request.username,
        email=request.email,
        scopes=["read", "attack", "defense", "eval"],
    )
    auth_manager.create_user(user, request.password)
    try:
        await persist_user_account(user, auth_manager._password_hashes[user.username])
    except ValueError as exc:
        auth_manager.users_db.pop(user.username, None)
        auth_manager._password_hashes.pop(user.username, None)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return {
        "message": "registered",
        "username": user.username,
        "email": user.email,
    }


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """用户登录"""
    user = auth_manager.authenticate_user(request.username, request.password)
    if not user:
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
