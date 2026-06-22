"""DATA_DIR / MOX_DATA_DIR path resolution tests."""

from pathlib import Path

import pytest

from mox.core.config import settings
from mox.core.database import get_data_dir, get_default_db_path, reset_database, reset_extended_database


@pytest.fixture(autouse=True)
def _reset_singletons():
    reset_database()
    reset_extended_database()
    yield
    reset_database()
    reset_extended_database()


def test_get_default_db_path_uses_data_dir(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("MOX_DATA_DIR", str(tmp_path / "custom-data"))
    settings.DATA_DIR = str(tmp_path / "custom-data")

    main_db = get_default_db_path("mox.db")
    ext_db = get_default_db_path("mox_ext.db")

    assert main_db.parent == tmp_path / "custom-data"
    assert ext_db.name == "mox_ext.db"
    assert get_data_dir().exists()