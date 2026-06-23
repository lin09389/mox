"""Shared optional-auth helpers for platform routes."""

from typing import Optional

from fastapi import Depends, HTTPException, status

from mox.core.auth import User, get_optional_active_user
from mox.core.config import settings


async def require_optional_access(
    current_user: Optional[User] = Depends(get_optional_active_user),
) -> User:
    """Allow dev bypass when REQUIRE_AUTH is disabled."""
    if not settings.REQUIRE_AUTH:
        return current_user or User(
            username="dev_user",
            email="dev@mox.ai",
            scopes=["read", "attack", "defense", "eval"],
        )
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
