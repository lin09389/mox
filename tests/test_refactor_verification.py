"""Gating checks for the five-target refactor."""

import importlib
import inspect

import pytest


def test_loop_engine_not_importable():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("mox.attacks.loop_engine")


def test_single_attack_loop_runner_definition():
    runners = []
    for module_name in ("mox.attack_loop.core",):
        mod = importlib.import_module(module_name)
        if hasattr(mod, "AttackLoopRunner"):
            runners.append(module_name)
    assert runners == ["mox.attack_loop.core"]


def test_routes_use_registry_not_hand_maps():
    import mox.routes.attack as attack_routes
    import mox.routes.api_v2 as api_v2_routes
    import mox.routes.benchmark as benchmark_routes

    combined = (
        inspect.getsource(attack_routes)
        + inspect.getsource(api_v2_routes)
        + inspect.getsource(benchmark_routes)
    )
    assert "attack_map" not in combined
    assert "execute_registry_attack" in combined
    assert "get_cached_llm" in combined


def test_attacks_export_surface_slimmed():
    import mox.attacks as attacks

    assert len(attacks.__all__) < 152
    for symbol in (
        "BaseAttack",
        "AttackConfig",
        "get_registry",
        "create_attack_instance",
        "PromptInjectionAttack",
    ):
        assert hasattr(attacks, symbol)


def test_attack_orchestrator_not_in_public_exports():
    import mox.attacks as attacks

    assert "AttackOrchestrator" not in attacks.__all__