"""Legacy mox_ext.db -> unified mox.db one-time migration tests."""

from pathlib import Path

import pytest
from sqlalchemy import select

from mox.core.config import settings
from mox.core.database import (
    Base,
    Database,
    ReportRecord,
    UserAccountRecord,
    _EXTENDED_TABLES,
    _LEGACY_EXT_MARKER,
    get_default_db_path,
    init_database,
    reset_database,
)


@pytest.fixture(autouse=True)
def _reset_singletons():
    reset_database()
    yield
    reset_database()


async def _seed_legacy_extended_db(legacy_path: Path) -> None:
    legacy = Database(db_path=legacy_path)
    async with legacy.engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn, tables=list(_EXTENDED_TABLES)
            )
        )
    async with legacy.get_session() as session:
        session.add(
            UserAccountRecord(
                username="legacy_user",
                email="legacy@test.local",
                password_hash="hash",
                scopes=["read"],
            )
        )
        session.add(
            ReportRecord(
                report_name="legacy-report",
                report_type="security",
                model_name="legacy-model",
                content="{}",
            )
        )
    await legacy.close()


@pytest.mark.asyncio
async def test_migrate_legacy_extended_database(monkeypatch, tmp_path: Path):
    data_dir = tmp_path / "data"
    monkeypatch.setenv("MOX_DATA_DIR", str(data_dir))
    settings.DATA_DIR = str(data_dir)

    legacy_path = get_default_db_path("mox_ext.db")
    main_path = get_default_db_path("mox.db")
    await _seed_legacy_extended_db(legacy_path)
    assert legacy_path.exists()

    db = await init_database(main_path)
    try:
        users = await db.list_user_accounts()
        reports = await db.get_reports(limit=10)
        assert any(u.username == "legacy_user" for u in users)
        assert any(r.report_name == "legacy-report" for r in reports)

        assert not legacy_path.exists()
        assert legacy_path.with_suffix(".db.bak").exists()
        marker = data_dir / _LEGACY_EXT_MARKER
        assert marker.exists()
        assert "rows=2" in marker.read_text(encoding="utf-8")
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_migration_skips_when_marker_present(monkeypatch, tmp_path: Path):
    data_dir = tmp_path / "data2"
    monkeypatch.setenv("MOX_DATA_DIR", str(data_dir))
    settings.DATA_DIR = str(data_dir)

    legacy_path = get_default_db_path("mox_ext.db")
    main_path = get_default_db_path("mox.db")
    await _seed_legacy_extended_db(legacy_path)
    (data_dir / _LEGACY_EXT_MARKER).write_text("rows=0\n", encoding="utf-8")

    db = await init_database(main_path)
    try:
        users = await db.list_user_accounts()
        assert users == []
        assert legacy_path.exists()
    finally:
        await db.close()