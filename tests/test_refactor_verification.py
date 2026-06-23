"""Gating checks for the five-target refactor."""

import ast
import importlib
import inspect
import warnings
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _find_attack_loop_runner_definitions() -> list[str]:
    """Return module paths that define class AttackLoopRunner."""
    found: list[str] = []
    scan_roots = (REPO_ROOT / "mox", REPO_ROOT / "tests")
    for root in scan_roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            rel = path.relative_to(REPO_ROOT).as_posix()
            if "/__pycache__/" in rel:
                continue
            try:
                source = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            try:
                tree = ast.parse(source, filename=rel)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == "AttackLoopRunner":
                    found.append(rel)
                    break
    return sorted(found)


def test_loop_engine_not_importable():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("mox.attacks.loop_engine")


def test_single_attack_loop_runner_definition():
    definitions = _find_attack_loop_runner_definitions()
    assert definitions == ["mox/attack_loop/core.py"], (
        f"expected exactly one AttackLoopRunner, found: {definitions}"
    )


def test_attacks_attack_loop_is_shim_only():
    shim_dir = REPO_ROOT / "mox" / "attacks" / "attack_loop"
    py_files = sorted(p.name for p in shim_dir.glob("*.py"))
    assert py_files == ["__init__.py"], f"attack_loop must be shim-only, found: {py_files}"


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
    assert "EvaluationResult" not in attacks.__all__
    assert "AttackEvaluator" not in attacks.__all__
    for symbol in (
        "BaseAttack",
        "AttackConfig",
        "get_registry",
        "create_attack_instance",
        "PromptInjectionAttack",
    ):
        assert hasattr(attacks, symbol)


def test_import_mox_attacks_without_deprecation_warnings():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        importlib.reload(importlib.import_module("mox.attacks"))
    deprecation_msgs = [
        w.message for w in caught if issubclass(w.category, DeprecationWarning)
    ]
    assert not deprecation_msgs, f"unexpected deprecations on import: {deprecation_msgs}"


def test_redteam_attack_mapping_populated():
    from mox.evaluation.redteam import AttackTechnique, get_attack_mapping

    mapping = get_attack_mapping()
    assert mapping, "attack mapping must not be empty after lazy init"
    assert AttackTechnique.TAP in mapping
    assert AttackTechnique.JAILBREAK in mapping


def test_attack_orchestrator_not_in_public_exports():
    import mox.attacks as attacks

    assert "AttackOrchestrator" not in attacks.__all__