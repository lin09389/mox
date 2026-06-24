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


def test_resolve_redteam_llms_three_models():
    from mox.evaluation.redteam_llms import resolve_redteam_llms

    created = []

    def fake_create(name):
        llm = type("LLM", (), {"model": name})()
        created.append(name)
        return llm

    with patch("mox.evaluation.redteam_llms._default_llm_factory", side_effect=fake_create):
        bundle = resolve_redteam_llms(
            target_model="gpt-4",
            attacker_model="claude-3",
            judge_model="llama3",
            judge_mode="hybrid",
        )

    assert created == ["gpt-4", "claude-3", "llama3"]
    assert bundle["models"] == {
        "target": "gpt-4",
        "attacker": "claude-3",
        "judge": "llama3",
    }


def test_resolve_redteam_llms_pattern_skips_judge():
    from mox.evaluation.redteam_llms import resolve_redteam_llms

    with patch(
        "mox.evaluation.redteam_llms._default_llm_factory",
        side_effect=lambda n: type("LLM", (), {"model": n})(),
    ):
        bundle = resolve_redteam_llms(
            target_model="gpt-4",
            attacker_model="gpt-4",
            judge_mode="pattern",
        )

    assert bundle["judge_llm"] is None
    assert bundle["models"]["judge"] is None


def test_redteam_run_wires_three_models(client: TestClient):
    target = type("LLM", (), {"model": "target-model"})()
    attacker = type("LLM", (), {"model": "attacker-model"})()
    judge = type("LLM", (), {"model": "judge-model"})()

    with patch(
        "mox.routes.platform.resolve_redteam_llms",
        return_value={
            "target_llm": target,
            "attacker_llm": attacker,
            "judge_llm": judge,
            "models": {
                "target": "target-model",
                "attacker": "attacker-model",
                "judge": "judge-model",
            },
        },
    ):
        with patch("mox.evaluation.redteam.RedTeamOrchestrator") as mock_orch_cls:
            mock_orch = mock_orch_cls.return_value
            mock_orch.scenarios = []
            client.post(
                "/api/v1/redteam/run",
                json={
                    "model": "target-model",
                    "attacker_model": "attacker-model",
                    "judge_model": "judge-model",
                    "techniques": ["nonexistent"],
                },
            )
            mock_orch_cls.assert_called_once_with(
                attacker,
                target,
                judge_llm=judge,
                judge_mode="hybrid",
                rag_backend=None,
                agent_mode=None,
                max_agent_steps=None,
            )


def test_redteam_run_defaults_agent_mode_for_agent_techniques(client: TestClient):
    target = type("LLM", (), {"model": "target-model"})()
    attacker = type("LLM", (), {"model": "attacker-model"})()
    judge = type("LLM", (), {"model": "judge-model"})()

    with patch(
        "mox.routes.platform.resolve_redteam_llms",
        return_value={
            "target_llm": target,
            "attacker_llm": attacker,
            "judge_llm": judge,
            "models": {
                "target": "target-model",
                "attacker": "attacker-model",
                "judge": "judge-model",
            },
        },
    ):
        with patch("mox.evaluation.redteam.RedTeamOrchestrator") as mock_orch_cls:
            mock_orch = mock_orch_cls.return_value
            mock_orch.scenarios = []
            client.post(
                "/api/v1/redteam/run",
                json={
                    "model": "target-model",
                    "techniques": ["tool_chaining"],
                },
            )
            mock_orch_cls.assert_called_once_with(
                attacker,
                target,
                judge_llm=judge,
                judge_mode="hybrid",
                rag_backend=None,
                agent_mode="langchain",
                max_agent_steps=None,
            )