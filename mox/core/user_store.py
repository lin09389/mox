"""Persistent user account storage backed by unified Database."""

from __future__ import annotations

from typing import List

from mox.core.auth import User, auth_manager
from mox.core.database import UserAccountRecord, get_extended_database


async def load_users_into_auth_manager() -> int:
    """Hydrate in-memory auth from SQLite user accounts."""
    db = get_extended_database()
    accounts: List[UserAccountRecord] = await db.list_user_accounts()
    loaded = 0
    for account in accounts:
        if auth_manager.get_user(account.username):
            continue
        user = User(
            username=account.username,
            email=account.email,
            scopes=account.scopes or ["read"],
            disabled=bool(account.disabled),
        )
        auth_manager.users_db[user.username] = user
        auth_manager._password_hashes[user.username] = account.password_hash
        loaded += 1
    return loaded


async def persist_user_account(user: User, password_hash: str) -> int:
    """Save a newly registered user to persistent storage."""
    db = get_extended_database()
    existing = await db.get_user_account(user.username)
    if existing:
        raise ValueError(f"Username already registered: {user.username}")

    return await db.save_user_account(
        {
            "username": user.username,
            "email": user.email,
            "password_hash": password_hash,
            "scopes": user.scopes or ["read"],
            "disabled": user.disabled,
        }
    )