"""Auto-redteam report persistence helpers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mox.auto_redteam.agent import RedTeamAgent
from mox.auto_redteam.state import RedTeamTask
from mox.routes.auto_redteam import _persist_auto_redteam_report


@pytest.mark.asyncio
async def test_persist_auto_redteam_report_saves_with_summary():
    agent = MagicMock(spec=RedTeamAgent)
    agent.state = RedTeamTask(
        task_id="art-test01",
        target_model="llama3",
        status="completed",
        current_step=3,
    )

    mock_db = AsyncMock()
    mock_db.save_report = AsyncMock(return_value=42)

    with patch("mox.core.database.get_extended_database", return_value=mock_db):
        report_id = await _persist_auto_redteam_report(agent)

    assert report_id == 42
    mock_db.save_report.assert_awaited_once()
    payload = mock_db.save_report.await_args.args[0]
    assert payload["report_type"] == "auto_redteam"
    assert payload["model_name"] == "llama3"
    assert payload["summary"]["task_id"] == "art-test01"
    assert payload["created_by"] == "auto_redteam"