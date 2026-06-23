"""Benchmark route smoke tests (mocked LLM, no external calls)."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from mox.core.database import reset_extended_database
from mox.core import AttackType
from mox.core.types import AttackOutcome, AttackResult, AttackPayload


@pytest.fixture
def client(tmp_path: Path, monkeypatch):
    reset_extended_database()
    db_path = tmp_path / "benchmark_test.db"
    monkeypatch.setenv("MOX_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("mox.core.config.settings.REQUIRE_AUTH", False)

    from mox.api import app
    from mox.core.database import init_extended_database

    import asyncio

    asyncio.run(init_extended_database(db_path))

    yield TestClient(app)
    reset_extended_database()


def _mock_outcome(success: bool = True) -> AttackOutcome:
    return AttackOutcome(
        result=AttackResult.SUCCESS if success else AttackResult.FAILURE,
        success_score=0.9 if success else 0.1,
        iterations=3,
        attack_prompt="test",
        model_response="ok",
    )


def _mock_payloads():
    return [
        AttackPayload(
            attack_type=AttackType.PROMPT_INJECTION,
            prompt="payload-a",
            target_behavior="behavior-a",
        ),
        AttackPayload(
            attack_type=AttackType.PROMPT_INJECTION,
            prompt="payload-b",
            target_behavior="behavior-b",
        ),
    ]


def test_run_benchmark_persists_report(client: TestClient):
    with patch("mox.routes.benchmark.get_cached_llm", return_value=MagicMock()):
        with patch(
            "mox.routes.benchmark.execute_registry_attack",
            new_callable=AsyncMock,
            return_value=_mock_outcome(True),
        ):
            with patch(
                "mox.routes.benchmark.benchmark_dataset.get_attack_payloads",
                return_value=_mock_payloads(),
            ):
                response = client.post(
                    "/api/v1/benchmark/run",
                    json={
                        "dataset": "advbench",
                        "attack_type": "prompt_injection",
                        "model": "llama3",
                        "max_cases": 2,
                    },
                )

    assert response.status_code == 200
    body = response.json()
    assert body["total_cases"] == 2
    assert body["successful_attacks"] == 2
    assert "report_id" in body

    listing = client.get("/api/v1/reports")
    assert listing.status_code == 200
    reports = listing.json()["reports"]
    assert any(item["id"] == body["report_id"] for item in reports)
    saved = next(item for item in reports if item["id"] == body["report_id"])
    assert saved["report_type"] == "benchmark"


def test_list_benchmark_datasets(client: TestClient):
    response = client.get("/api/v1/benchmark/datasets")
    assert response.status_code == 200
    assert "datasets" in response.json()