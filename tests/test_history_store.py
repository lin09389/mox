"""history_store helper unit tests."""

import asyncio
from dataclasses import dataclass
from pathlib import Path

import pytest

from mox.core.database import close_database, init_database, reset_database
from mox.core.history_store import persist_advanced_attack_batch


@dataclass
class _FakeAdvancedResult:
    template_name: str
    category: str
    severity: str
    prompt: str
    response: str
    success: bool
    confidence: float


@pytest.mark.asyncio
async def test_persist_advanced_attack_batch_writes_summary(tmp_path: Path):
    reset_database()
    await init_database(db_path=tmp_path / "adv.db")

    record_id = await persist_advanced_attack_batch(
        "advanced_attack",
        "llama3",
        "ignore safety",
        [
            _FakeAdvancedResult("t1", "cat", "high", "p1", "r1", True, 0.9),
            _FakeAdvancedResult("t2", "cat", "med", "p2", "r2", False, 0.2),
        ],
        source="test",
    )

    assert record_id is not None
    from mox.core.database import get_database

    records = await get_database().get_attack_records(limit=5)
    assert len(records) == 1
    assert records[0].attack_type == "advanced_attack"
    assert records[0].record_meta["total_templates"] == 2

    await close_database()
    reset_database()