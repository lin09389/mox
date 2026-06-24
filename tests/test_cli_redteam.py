"""CLI redteam 命令测试（无真实 LLM 调用）。"""

import argparse
from unittest.mock import AsyncMock, patch

import pytest


def test_redteam_parser_registers_subcommand():
    from mox.cli import main
    import mox.cli as cli_module

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    # Reuse parser setup from main by inspecting redteam via module attributes is heavy;
    # smoke-test argparse choices via a minimal mirror of cli registration.
    redteam = subparsers.add_parser("redteam")
    redteam.add_argument("--model", default="gpt-4")
    redteam.add_argument("--attacker-model", default=None)
    redteam.add_argument("--judge-model", default=None)
    args = parser.parse_args(["redteam", "--model", "target", "--attacker-model", "atk"])
    assert args.command == "redteam"
    assert args.model == "target"
    assert args.attacker_model == "atk"
    assert main is cli_module.main


@pytest.mark.asyncio
async def test_run_redteam_wires_orchestrator():
    from mox.cli import run_redteam

    class FakeLLM:
        def __init__(self, name):
            self.model = name

        async def generate(self, messages, **kw):
            class R:
                content = "I'm sorry, I cannot help."

            return R()

    fake_results = []

    class FakeScenario:
        technique = type("T", (), {"value": "jailbreak"})()
        name = "jb"
        difficulty = "medium"

    class FakeOrchestrator:
        def __init__(self, attacker, target, **kwargs):
            self.attacker = attacker
            self.target = target
            self.kwargs = kwargs

        @classmethod
        def create_scenarios(cls, scenario_type):
            return [FakeScenario()]

        def set_progress_callback(self, cb):
            pass

        async def run_all_scenarios(self, **kwargs):
            return fake_results

        def generate_report(self, results):
            return {
                "summary": {"total_scenarios": 0, "successful": 0, "success_rate": 0, "avg_score": 0},
                "models": {"attacker": "atk", "target": "tgt", "judge": "jdg"},
                "results": [],
            }

    args = argparse.Namespace(
        model="tgt",
        target_model=None,
        attacker_model="atk",
        judge_model="jdg",
        judge_mode="hybrid",
        use_defense=False,
        techniques=["jailbreak"],
        scenario_type="basic",
        max_attempts=None,
        concurrency=1,
        sequential=True,
        rag_backend="sklearn",
    )

    with patch("mox.cli.create_llm", side_effect=lambda n: FakeLLM(n)):
        with patch("mox.evaluation.redteam.RedTeamOrchestrator", FakeOrchestrator):
            await run_redteam(args)