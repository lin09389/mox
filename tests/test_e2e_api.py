"""Full-app API smoke tests (E2E via TestClient)."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from mox.api import app
from mox.core.auth import User, get_current_active_user, get_optional_active_user
from mox.core.database import close_database, init_database, reset_database

pytestmark = pytest.mark.integration


@pytest.fixture
def client(tmp_path, monkeypatch):
    reset_database()
    monkeypatch.setenv("MOX_DATA_DIR", str(tmp_path))
    asyncio.run(init_database(tmp_path / "e2e.db"))

    user = User(username="e2e_user", scopes=["admin", "attack", "defense", "eval"])
    app.dependency_overrides[get_current_active_user] = lambda: user
    app.dependency_overrides[get_optional_active_user] = lambda: user
    # Avoid lifespan startup in TestClient — it can deadlock on Windows CI runners.
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()
    asyncio.run(close_database())
    reset_database()


def test_root_metadata(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "version" in data


def test_health_endpoints(client: TestClient):
    liveness = client.get("/health")
    assert liveness.status_code == 200
    assert liveness.json()["status"] == "alive"

    for path in ("/api/v1/health", "/api/health"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


def test_models_and_templates(client: TestClient):
    models = client.get("/api/v1/models")
    assert models.status_code == 200
    assert "models" in models.json()
    assert isinstance(models.json()["models"], list)

    templates = client.get("/api/v1/templates")
    assert templates.status_code == 200
    body = templates.json()
    assert "success" in body or "error" in body


def test_monitoring_and_platform_stats(client: TestClient):
    monitoring = client.get("/api/v1/monitoring/stats")
    assert monitoring.status_code == 200

    visualization = client.get("/api/v1/monitoring/visualization")
    assert visualization.status_code == 200
    viz = visualization.json()
    assert "trends" in viz
    assert "radar" in viz
    assert "topology" in viz

    overview = client.get("/api/v1/stats/overview")
    assert overview.status_code == 200


def test_tasks_and_audit_routes(client: TestClient):
    tasks = client.get("/api/v1/tasks")
    assert tasks.status_code == 200
    assert isinstance(tasks.json(), list)

    audit = client.get("/api/v1/audit/logs")
    assert audit.status_code == 200
    assert "logs" in audit.json()


def test_prometheus_metrics(client: TestClient):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")


def test_reports_get_returns_content(client: TestClient):
    import asyncio

    from mox.core.database import get_extended_database

    async def _seed():
        return await get_extended_database().save_report(
            {
                "report_name": "auto-redteam-e2e",
                "report_type": "auto_redteam",
                "model_name": "llama3",
                "format": "json",
                "content": '{"task_id":"e2e-1","status":"completed","steps":3}',
                "summary": {
                    "attack_success_rate": 0.82,
                    "defense_success_rate": 0.18,
                },
            }
        )

    report_id = asyncio.run(_seed())

    listed = client.get("/api/v1/reports")
    assert listed.status_code == 200
    items = listed.json()["reports"]
    assert any(item["id"] == report_id for item in items)

    detail = client.get(f"/api/v1/reports/{report_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["report_type"] == "auto_redteam"
    assert body["content"] is not None
    assert "task_id" in body["content"] or "steps" in str(body["content"])