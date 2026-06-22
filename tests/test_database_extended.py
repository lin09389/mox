"""Extended database inline tests."""

from pathlib import Path

import pytest

from mox.core.auth import User, auth_manager
from mox.core.database import (
    Base,
    ExtendedDatabase,
    ReportRecord,
    UserAccountRecord,
    AuditLogRecord,
    get_extended_database,
    init_extended_database,
    reset_extended_database,
)
from mox.core.user_store import load_users_into_auth_manager, persist_user_account


async def _close_and_reset(db: ExtendedDatabase) -> None:
    await db.close()
    reset_extended_database()


@pytest.mark.asyncio
async def test_init_extended_database_creates_tables(tmp_path: Path):
    db_path = tmp_path / "test_ext.db"
    db = await init_extended_database(db_path)
    try:
        report_id = await db.save_report(
            {
                "report_name": "unit-test",
                "report_type": "security",
                "model_name": "test-model",
                "content": "{}",
            }
        )
        assert report_id >= 1
        reports = await db.get_reports(limit=5)
        assert len(reports) >= 1
        assert reports[0].report_name == "unit-test"
    finally:
        await _close_and_reset(db)


@pytest.mark.asyncio
async def test_save_audit_log(tmp_path: Path):
    db = ExtendedDatabase(tmp_path / "audit.db")
    await db.init_db()
    try:
        log_id = await db.save_audit_log(
            {
                "user_id": "u1",
                "username": "tester",
                "action": "GET",
                "endpoint": "/api/v1/health",
                "response_status": 200,
            }
        )
        assert log_id >= 1
        logs = await db.get_audit_logs(limit=10, action="GET")
        assert any(log.id == log_id for log in logs)
    finally:
        await db.close()


def test_get_extended_database_singleton():
    db1 = get_extended_database()
    db2 = get_extended_database()
    assert db1 is db2


def test_extended_models_registered():
    assert ReportRecord.__tablename__ == "report_records"
    assert UserAccountRecord.__tablename__ == "user_accounts"
    assert AuditLogRecord.__tablename__ == "audit_log_records"
    assert issubclass(ReportRecord, Base)
    assert issubclass(UserAccountRecord, Base)
    assert issubclass(AuditLogRecord, Base)


@pytest.mark.asyncio
async def test_user_account_persistence_and_reload(tmp_path: Path):
    reset_extended_database()
    auth_manager.users_db.clear()
    auth_manager._password_hashes.clear()

    db_path = tmp_path / "users.db"
    db = await init_extended_database(db_path)
    try:
        user = User(username="persisted_user", email="u@test.local", scopes=["read", "attack"])
        auth_manager.create_user(user, "secret-pass-123")
        await persist_user_account(user, auth_manager._password_hashes[user.username])

        auth_manager.users_db.clear()
        auth_manager._password_hashes.clear()
        loaded = await load_users_into_auth_manager()
        assert loaded == 1
        assert auth_manager.authenticate_user("persisted_user", "secret-pass-123") is not None
    finally:
        await _close_and_reset(db)