"""Reports API smoke tests."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from mox.core.database import ExtendedDatabase, reset_extended_database


@pytest.fixture
def client(tmp_path: Path, monkeypatch):
    reset_extended_database()
    db_path = tmp_path / "reports_test.db"
    monkeypatch.setenv("MOX_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("mox.core.config.settings.REQUIRE_AUTH", False)

    from mox.api import app
    from mox.core.database import init_extended_database

    import asyncio

    asyncio.run(init_extended_database(db_path))

    yield TestClient(app)
    reset_extended_database()


def test_list_reports_requires_auth_when_enabled(tmp_path: Path, monkeypatch):
    reset_extended_database()
    monkeypatch.setattr("mox.core.config.settings.REQUIRE_AUTH", True)

    from mox.api import app
    from mox.core.database import init_extended_database

    import asyncio

    asyncio.run(init_extended_database(tmp_path / "auth.db"))

    client = TestClient(app)
    response = client.get("/api/v1/reports")
    assert response.status_code == 401
    reset_extended_database()


def test_list_reports_empty(client: TestClient):
    response = client.get("/api/v1/reports")
    assert response.status_code == 200
    assert response.json()["reports"] == []


def test_delete_report_writes_audit(client: TestClient):
    import asyncio

    from mox.core.database import get_extended_database

    async def _seed():
        return await get_extended_database().save_report(
            {
                "report_name": "audit-target",
                "report_type": "evaluation",
                "model_name": "llama3",
                "format": "json",
                "content": "{}",
                "summary": {"attack_success_rate": 0.2, "defense_success_rate": 0.8},
            }
        )

    report_id = asyncio.run(_seed())

    with patch("mox.core.audit.get_audit_logger") as mock_get:
        mock_logger = AsyncMock()
        mock_get.return_value = mock_logger
        response = client.delete(f"/api/v1/reports/{report_id}")

    assert response.status_code == 200
    mock_logger.log.assert_awaited_once()
    assert mock_logger.log.await_args.kwargs["action"] == "report_delete"


@pytest.mark.asyncio
async def test_report_crud_flow(tmp_path: Path):
    reset_extended_database()
    db = ExtendedDatabase(tmp_path / "crud.db")
    await db.init_db()
    try:
        report_id = await db.save_report(
            {
                "report_name": "bench-run",
                "report_type": "benchmark",
                "model_name": "llama3",
                "format": "json",
                "content": '{"ok": true}',
                "summary": {
                    "attack_success_rate": 0.4,
                    "defense_success_rate": 0.6,
                },
            }
        )
        record = await db.get_report(report_id)
        assert record is not None
        assert record.report_name == "bench-run"

        deleted = await db.delete_report(report_id)
        assert deleted is True
        assert await db.get_report(report_id) is None
    finally:
        await db.close()
        reset_extended_database()