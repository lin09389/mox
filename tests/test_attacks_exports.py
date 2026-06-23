"""Validate mox.attacks public export surface."""

import importlib

import pytest

import mox.attacks as attacks


@pytest.mark.parametrize("symbol", attacks.__all__)
def test_all_exports_resolve(symbol: str):
    assert hasattr(attacks, symbol), f"missing export: {symbol}"
    assert getattr(attacks, symbol) is not None


def test_export_count_below_legacy_surface():
    assert len(attacks.__all__) < 152, f"export surface too large: {len(attacks.__all__)}"


def test_core_exports_importable_from_package_root():
    root = importlib.import_module("mox.attacks")
    for name in (
        "BaseAttack",
        "AttackConfig",
        "PromptInjectionAttack",
        "get_registry",
        "create_attack_instance",
        "get_all_attack_types",
    ):
        assert hasattr(root, name)


def test_backward_compat_symbols_still_importable():
    root = importlib.import_module("mox.attacks")
    for name in (
        "AdvancedPromptInjection",
        "MultiTurnJailbreakAttack",
        "AgentToolManipulationAttack",
        "GCGAttack",
    ):
        assert hasattr(root, name), f"backward compat symbol missing: {name}"