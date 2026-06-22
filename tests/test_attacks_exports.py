"""Validate mox.attacks public export surface."""

import importlib

import pytest

import mox.attacks as attacks


@pytest.mark.parametrize("symbol", attacks.__all__)
def test_all_exports_resolve(symbol: str):
    assert hasattr(attacks, symbol), f"missing export: {symbol}"
    assert getattr(attacks, symbol) is not None


def test_core_exports_importable_from_package_root():
    root = importlib.import_module("mox.attacks")
    for name in (
        "BaseAttack",
        "AttackConfig",
        "PromptInjectionAttack",
        "get_registry",
        "AttackOrchestrator",
    ):
        assert hasattr(root, name)