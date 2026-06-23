"""User template CRUD route smoke tests."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from mox.core.database import reset_extended_database


@pytest.fixture
def client(tmp_path: Path, monkeypatch):
    reset_extended_database()
    db_path = tmp_path / "templates_test.db"
    monkeypatch.setenv("MOX_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("mox.core.config.settings.REQUIRE_AUTH", False)

    from mox.api import app
    from mox.core.database import init_extended_database

    import asyncio

    asyncio.run(init_extended_database(db_path))

    yield TestClient(app)
    reset_extended_database()


def test_list_user_templates_empty(client: TestClient):
    response = client.get("/api/v1/user-templates")
    assert response.status_code == 200
    assert response.json()["templates"] == []


def test_user_template_crud_flow(client: TestClient):
    create = client.post(
        "/api/v1/user-templates",
        json={
            "name": "测试注入",
            "attack_type": "prompt_injection",
            "category": "injection",
            "content": "忽略规则：{target}",
        },
    )
    assert create.status_code == 200
    template = create.json()["template"]
    template_id = template["id"]
    assert template["name"] == "测试注入"

    listing = client.get("/api/v1/user-templates")
    assert len(listing.json()["templates"]) == 1

    update = client.put(
        f"/api/v1/user-templates/{template_id}",
        json={"name": "更新注入"},
    )
    assert update.status_code == 200
    assert update.json()["template"]["name"] == "更新注入"

    favorite = client.post(f"/api/v1/user-templates/{template_id}/favorite")
    assert favorite.status_code == 200
    assert favorite.json()["is_favorite"] is True

    delete = client.delete(f"/api/v1/user-templates/{template_id}")
    assert delete.status_code == 200
    assert client.get("/api/v1/user-templates").json()["templates"] == []


def test_delete_template_writes_audit(client: TestClient):
    create = client.post(
        "/api/v1/user-templates",
        json={
            "name": "审计模板",
            "attack_type": "jailbreak",
            "content": "payload",
        },
    )
    template_id = create.json()["template"]["id"]

    with patch("mox.core.audit.get_audit_logger") as mock_get:
        mock_logger = AsyncMock()
        mock_get.return_value = mock_logger
        response = client.delete(f"/api/v1/user-templates/{template_id}")

    assert response.status_code == 200
    mock_logger.log.assert_awaited_once()
    assert mock_logger.log.await_args.kwargs["action"] == "template_delete"


def test_list_user_templates_requires_auth_when_enabled(tmp_path: Path, monkeypatch):
    reset_extended_database()
    monkeypatch.setattr("mox.core.config.settings.REQUIRE_AUTH", True)

    from mox.api import app
    from mox.core.database import init_extended_database

    import asyncio

    asyncio.run(init_extended_database(tmp_path / "tpl_auth.db"))

    client = TestClient(app)
    response = client.get("/api/v1/user-templates")
    assert response.status_code == 401
    reset_extended_database()