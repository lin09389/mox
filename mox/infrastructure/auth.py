"""认证和安全模块"""
import json
import os
import threading
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum

from jose import JWTError, jwt
import bcrypt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings
from .logging import get_logger

logger = get_logger("auth")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

_SECRET_KEY_WARNED = False


class TokenType(Enum):
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass
class TokenData:
    """Token数据"""

    sub: str
    exp: datetime
    token_type: TokenType = TokenType.ACCESS
    scopes: List[str] = field(default_factory=list)


@dataclass
class User:
    """用户模型"""

    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    scopes: List[str] = None


class PasswordManager:

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password[:72].encode("utf-8"),
                hashed_password.encode("utf-8") if isinstance(hashed_password, str) else hashed_password,
            )
        except Exception:
            return False

    @staticmethod
    def get_password_hash(password: str) -> str:
        return bcrypt.hashpw(
            password[:72].encode("utf-8"),
            bcrypt.gensalt(rounds=12),
        ).decode("utf-8")


class TokenManager:
    """Token管理"""

    @staticmethod
    def _check_secret_key():
        global _SECRET_KEY_WARNED
        if not _SECRET_KEY_WARNED and settings.SECRET_KEY.startswith("MOX_") is False:
            import os

            if len(settings.SECRET_KEY) == 64:
                try:
                    bytes.fromhex(settings.SECRET_KEY)
                    if not _SECRET_KEY_WARNED:
                        warnings.warn(
                            "SECRET_KEY is auto-generated (random hex). "
                            "All JWT tokens will be invalidated on restart. "
                            "Set MOX_SECRET_KEY environment variable for production use.",
                            stacklevel=3,
                        )
                        _SECRET_KEY_WARNED = True
                except ValueError:
                    pass

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        TokenManager._check_secret_key()
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
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[ALGORITHM],
                options={"require": ["exp"]},
            )
            sub: str = payload.get("sub")
            exp: int = payload.get("exp")
            token_type: str = payload.get("token_type", "access")

            if sub is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                )

            # Explicitly check token expiration
            if exp is not None and datetime.now(timezone.utc) > datetime.fromtimestamp(exp, tz=timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                )

            return TokenData(
                sub=sub,
                exp=datetime.fromtimestamp(exp, tz=timezone.utc) if exp else datetime.now(timezone.utc),
                token_type=TokenType(token_type),
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )


class AuthManager:
    """认证管理器

    The in-memory ``users_db`` is mirrored to a JSON file so that
    user accounts created at runtime (via ``create_user``) survive
    process restarts.  The file location is controlled by the
    ``MOX_USERS_FILE`` environment variable; default is
    ``<project>/mox_users.json``.
    """

    def __init__(self):
        self._users_path = Path(
            os.environ.get("MOX_USERS_FILE", str(Path("mox_users.json").resolve()))
        )
        self._users_lock = threading.Lock()
        self.users_db: dict[str, User] = {}
        self._password_hashes: dict[str, str] = {}

        # Load existing users (if any) BEFORE creating default users
        # so defaults don't clobber stored accounts with the same name.
        self._load_users()

        # Existing on-disk accounts that aren't in DEFAULT_USERS are
        # preserved; new DEFAULT_USERS are added.
        self._init_default_users()

    # ----------------------------------------------------------------
    # Persistence
    # ----------------------------------------------------------------

    def _load_users(self) -> None:
        if not self._users_path.exists():
            return
        try:
            data = json.loads(self._users_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Failed to load users file %s: %s", self._users_path, e)
            return

        if not isinstance(data, dict):
            logger.warning(
                "Users file %s is not a JSON object -- ignoring",
                self._users_path,
            )
            return

        for username, record in data.items():
            if not isinstance(record, dict):
                continue
            try:
                self.users_db[username] = User(
                    username=username,
                    email=record.get("email"),
                    full_name=record.get("full_name"),
                    disabled=bool(record.get("disabled", False)),
                    scopes=record.get("scopes") or ["read"],
                )
                password_hash = record.get("password_hash")
                if password_hash:
                    self._password_hashes[username] = password_hash
            except Exception as e:
                logger.warning("Skipping malformed user record %r: %s", username, e)

    def _save_users(self) -> None:
        """Write the current ``users_db`` to disk as JSON.

        Uses a temp-file + os.replace atomic write so a crash
        mid-write doesn't leave a half-written file that would
        fail to parse on next startup.
        """
        with self._users_lock:
            payload = {
                username: {
                    "email": user.email,
                    "full_name": user.full_name,
                    "disabled": user.disabled,
                    "scopes": user.scopes or [],
                    # Stored as bcrypt hash, not plaintext.
                    "password_hash": self._password_hashes.get(username, ""),
                }
                for username, user in self.users_db.items()
            }
            try:
                self._users_path.parent.mkdir(parents=True, exist_ok=True)
                tmp = self._users_path.with_suffix(self._users_path.suffix + ".tmp")
                tmp.write_text(
                    json.dumps(payload, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                os.replace(tmp, self._users_path)
            except Exception as e:
                logger.error("Failed to write users file %s: %s", self._users_path, e)

    # ----------------------------------------------------------------
    # User CRUD
    # ----------------------------------------------------------------

    def _init_default_users(self):
        """初始化默认用户 - 仅当配置了默认用户密码时才创建"""
        import warnings

        # 从环境变量获取默认用户配置，格式: username:password:email:scopes
        # 示例: admin:secure_password_here:admin@mox.ai:admin,attack,defense,eval
        default_users_env = settings.DEFAULT_USERS

        if not default_users_env:
            # 没有配置默认用户，这是生产环境的推荐配置
            return

        new_users_added = False
        for user_config in default_users_env:
            try:
                parts = user_config.split(":")
                if len(parts) < 2:
                    warnings.warn(
                        f"Invalid default user config (need username:password): {user_config}"
                    )
                    continue

                username = parts[0]
                if username in self.users_db:
                    # Don't overwrite an on-disk account with the
                    # default -- the on-disk version is presumably
                    # updated (e.g. password rotated).
                    continue
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
                new_users_added = True
            except Exception as e:
                warnings.warn(
                    f"Failed to initialize default user from config: {user_config}, error: {e}"
                )

        if new_users_added:
            self._save_users()

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        with self._users_lock:
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
        with self._users_lock:
            return self.users_db.get(username)

    def create_user(self, user: User, password: str) -> User:
        password_hash = PasswordManager.get_password_hash(password)
        user.scopes = user.scopes or ["read"]
        with self._users_lock:
            self.users_db[user.username] = user
            self._password_hashes[user.username] = password_hash
        # Persist outside the lock so we don't hold it across
        # disk I/O.  Worst case two concurrent create_user calls
        # each write the file -- last writer wins, but both
        # writes are consistent.
        self._save_users()
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


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> Optional[User]:
    """可选认证 - 开发模式下允许无认证访问"""
    from .config import settings

    # 如果禁用认证要求，返回一个默认用户
    if not settings.REQUIRE_AUTH:
        return User(
            username="dev_user",
            email="dev@mox.ai",
            scopes=["admin", "attack", "defense", "eval"],
        )

    # 如果没有提供 token，返回 None
    if credentials is None:
        return None

    # 验证 token
    try:
        token_data = TokenManager.verify_token(credentials.credentials)
        user = auth_manager.get_user(token_data.sub)
        if user and not user.disabled:
            return user
    except HTTPException:
        pass

    return None


async def get_optional_active_user(
    current_user: Optional[User] = Depends(get_optional_user),
) -> Optional[User]:
    """可选活跃用户 - 开发模式下允许无认证访问"""
    if current_user is None:
        # 开发模式下返回默认用户
        from .config import settings

        if not settings.REQUIRE_AUTH:
            return User(
                username="dev_user",
                email="dev@mox.ai",
                scopes=["admin", "attack", "defense", "eval"],
            )
        return None
    if current_user.disabled:
        return None
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
