"""认证和安全模块"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class TokenType(Enum):
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass
class TokenData:
    """Token数据"""

    sub: str
    exp: datetime
    token_type: TokenType = TokenType.ACCESS
    scopes: List[str] = None


@dataclass
class User:
    """用户模型"""

    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    scopes: List[str] = None


class PasswordManager:
    """密码管理"""

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return PasswordManager.pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return PasswordManager.pwd_context.hash(password)


class TokenManager:
    """Token管理"""

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "token_type": TokenType.ACCESS.value})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=7)
        to_encode.update({"exp": expire, "token_type": TokenType.REFRESH.value})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> TokenData:
        try:
            # First, verify the algorithm header to prevent algorithm confusion attacks
            unverified_header = jwt.get_unverified_header(token)
            if unverified_header.get("alg") != ALGORITHM:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token algorithm",
                )
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            sub: str = payload.get("sub")
            exp: int = payload.get("exp")
            token_type: str = payload.get("token_type", "access")

            if sub is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                )

            return TokenData(
                sub=sub,
                exp=datetime.fromtimestamp(exp),
                token_type=TokenType(token_type),
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )


class AuthManager:
    """认证管理器"""

    def __init__(self):
        self.users_db = {}
        self._password_hashes = {}  # Store password hashes separately
        self._init_default_users()

    def _init_default_users(self):
        """初始化默认用户 - 仅当配置了默认用户密码时才创建"""
        import warnings

        # 从环境变量获取默认用户配置，格式: username:password:email:scopes
        # 示例: admin:secure_password_here:admin@mox.ai:admin,attack,defense,eval
        default_users_env = settings.DEFAULT_USERS

        if not default_users_env:
            # 没有配置默认用户，这是生产环境的推荐配置
            return

        for user_config in default_users_env:
            try:
                parts = user_config.split(":")
                if len(parts) < 2:
                    warnings.warn(f"Invalid default user config (need username:password): {user_config}")
                    continue

                username = parts[0]
                password = parts[1]
                email = parts[2] if len(parts) > 2 else f"{username}@mox.ai"
                scopes = parts[3].split(",") if len(parts) > 3 else ["read"]

                user = User(
                    username=username,
                    email=email,
                    scopes=scopes,
                )
                self.users_db[username] = user
                self._password_hashes[username] = PasswordManager.get_password_hash(password)
            except Exception as e:
                warnings.warn(f"Failed to initialize default user from config: {user_config}, error: {e}")

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.users_db.get(username)
        if not user:
            return None
        if user.disabled:
            return None
        # Verify password against stored hash
        stored_hash = self._password_hashes.get(username)
        if not stored_hash:
            return None
        if not PasswordManager.verify_password(password, stored_hash):
            return None
        return user

    def get_user(self, username: str) -> Optional[User]:
        return self.users_db.get(username)

    def create_user(self, user: User, password: str) -> User:
        hashed_password = PasswordManager.get_password_hash(password)
        user.scopes = user.scopes or ["read"]
        self.users_db[user.username] = user
        return user


auth_manager = AuthManager()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    token_data = TokenManager.verify_token(credentials.credentials)
    user = auth_manager.get_user(token_data.sub)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_scope(required_scope: str):
    async def scope_checker(current_user: User = Depends(get_current_active_user)):
        if required_scope not in (current_user.scopes or []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope '{required_scope}' required",
            )
        return current_user

    return scope_checker
