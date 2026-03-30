"""Version helpers for runtime and API metadata."""

from __future__ import annotations

from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
import tomllib


@lru_cache(maxsize=1)
def get_version() -> str:
    """Return the installed package version, falling back to pyproject in dev."""
    try:
        return package_version("mox")
    except PackageNotFoundError:
        pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        return data["project"]["version"]


PACKAGE_VERSION = get_version()
