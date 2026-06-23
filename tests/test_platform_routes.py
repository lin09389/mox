"""Platform / datasets route smoke tests (no LLM calls)."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from mox.core.database import reset_extended_database


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("mox.core.config.settings.REQUIRE_AUTH", False)
    from mox.api import app

    return TestClient(app)


def test_list_datasets_returns_builtin(client: TestClient):
    response = client.get("/api/v1/datasets")
    assert response.status_code == 200
    body = response.json()
    assert "datasets" in body
    assert len(body["datasets"]) >= 1
    first = body["datasets"][0]
    assert "id" in first
    assert "name" in first
    assert "samples" in first


def test_delete_builtin_dataset_forbidden(client: TestClient):
    response = client.delete("/api/v1/datasets/advbench")
    assert response.status_code == 403


def test_upload_dataset_not_implemented(client: TestClient):
    response = client.post("/api/v1/datasets/upload")
    assert response.status_code == 501


def test_list_datasets_requires_auth_when_enabled(tmp_path: Path, monkeypatch):
    reset_extended_database()
    monkeypatch.setattr("mox.core.config.settings.REQUIRE_AUTH", True)

    from mox.api import app
    from mox.core.database import init_extended_database

    import asyncio

    asyncio.run(init_extended_database(tmp_path / "datasets_auth.db"))

    client = TestClient(app)
    response = client.get("/api/v1/datasets")
    assert response.status_code == 401
    reset_extended_database()


def test_owasp_run_raises_on_failure(client: TestClient):
    with patch("mox.routes.platform._create_llm", side_effect=RuntimeError("no llm")):
        response = client.post("/api/v1/owasp/run", json={"model": "test-model"})
    assert response.status_code == 500
    body = response.json()
    error_text = body.get("detail") or body.get("message") or ""
    assert "no llm" in str(error_text)


def test_redteam_run_no_matching_techniques(client: TestClient):
    with patch("mox.routes.platform._create_llm") as mock_llm:
        mock_llm.return_value = object()
        with patch("mox.evaluation.redteam.RedTeamOrchestrator") as mock_orch:
            mock_orch.return_value.scenarios = []
            response = client.post(
                "/api/v1/redteam/run",
                json={"model": "test-model", "techniques": ["nonexistent"]},
            )
    assert response.status_code == 400