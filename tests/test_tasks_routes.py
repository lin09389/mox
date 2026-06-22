"""Task list formatting helpers."""

from mox.routes.tasks import _format_task


def test_format_task_auto_redteam_defaults():
    item = _format_task(
        {
            "id": "art-abc123",
            "source": "auto_redteam",
            "status": "running",
            "target_model": "llama3",
            "max_steps": 10,
        }
    )
    assert item["id"] == "art-abc123"
    assert item["name"] == "自动红队 (llama3)"
    assert item["source"] == "auto_redteam"
    assert item["status"] == "running"


def test_format_task_completed_status_normalized():
    item = _format_task(
        {
            "id": "loop-1",
            "source": "attack_loop",
            "status": "completed (max steps reached)",
            "progress": 100,
        }
    )
    assert item["status"] == "completed"
    assert item["progress"] == 100


def test_format_task_includes_report_id():
    item = _format_task(
        {
            "id": "loop-9",
            "source": "attack_loop",
            "status": "completed",
            "progress": 100,
            "report_id": 55,
        }
    )
    assert item["report_id"] == 55