"""Attack-loop report persistence smoke tests."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from mox.routes.attack_loop import AttackLoopConfig, AttackLoopTask, _persist_attack_loop_report


class _FakeResult:
    def __init__(self, success: bool):
        self.success = success


@pytest.mark.asyncio
async def test_persist_attack_loop_report_returns_report_id():
    config = AttackLoopConfig(
        models=["llama3"],
        attack_types=["jailbreak"],
        prompts=["hi"],
        checkpoint_enabled=False,
    )
    task = AttackLoopTask("loop-test-1", config=config)
    task.results = [_FakeResult(True), _FakeResult(False)]

    with patch("mox.core.database.get_extended_database") as mock_db_factory:
        mock_db = AsyncMock()
        mock_db.save_report = AsyncMock(return_value=101)
        mock_db_factory.return_value = mock_db

        with patch("mox.routes.attack_loop.TestStatistics.calculate") as mock_stats:
            stats = mock_stats.return_value
            stats.total_tests = 2
            stats.successful_tests = 1
            stats.to_dict.return_value = {"total_tests": 2, "successful_tests": 1}

            report_id = await _persist_attack_loop_report(task)

    assert report_id == 101
    mock_db.save_report.assert_awaited_once()
    payload = mock_db.save_report.await_args.args[0]
    assert payload["report_type"] == "evaluation"
    assert payload["created_by"] == "attack_loop"
    assert json.loads(payload["content"])["total_tests"] == 2