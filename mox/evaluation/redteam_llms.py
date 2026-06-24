"""红队三模型 LLM 解析（CLI / API 共用）。"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

DEFAULT_REDTEAM_AGENT_MODE = "langchain"

AGENT_TECHNIQUE_VALUES = frozenset(
    {
        "tool_abuse",
        "tool_chaining",
        "indirect_injection",
        "privilege_escalation",
        "data_exfiltration",
        "agent_data_exfiltration",
        "agent_tool_manipulation",
        "agent",
        "composite",
        "composite_agent",
        "tool_confusion",
        "multi_agent",
    }
)


def _default_llm_factory(model: str):
    from mox.core import LLMFactory, MiniMaxLLM
    from mox.core.config import settings as runtime_settings

    if model.startswith("abab"):
        return MiniMaxLLM(
            model=model,
            api_key=runtime_settings.MINIMAX_API_KEY,
            group_id=runtime_settings.MINIMAX_GROUP_ID,
        )
    return LLMFactory.create_from_model_name(model)


def resolve_redteam_llms(
    *,
    target_model: str,
    attacker_model: Optional[str] = None,
    judge_model: Optional[str] = None,
    judge_mode: str = "hybrid",
    llm_factory: Optional[Callable[[str], Any]] = None,
) -> Dict[str, Any]:
    """解析红队三模型：attacker / target / judge（pattern 模式下 judge 为 None）。"""
    factory = llm_factory or _default_llm_factory
    target_llm = factory(target_model)
    attacker_name = attacker_model or target_model
    attacker_llm = factory(attacker_name)

    judge_llm = None
    judge_name: Optional[str] = None
    if judge_mode != "pattern":
        judge_name = judge_model or target_model
        judge_llm = factory(judge_name)

    return {
        "target_llm": target_llm,
        "attacker_llm": attacker_llm,
        "judge_llm": judge_llm,
        "models": {
            "target": target_model,
            "attacker": attacker_name,
            "judge": judge_name,
        },
    }


def resolve_redteam_agent_mode(
    agent_mode: Optional[str],
    *,
    scenario_type: Optional[str] = None,
    techniques: Optional[List[str]] = None,
) -> Optional[str]:
    """未显式指定时，Agent 相关红队场景默认使用 langchain 多步工具循环。"""
    if agent_mode is not None:
        return agent_mode
    if scenario_type == "agent":
        return DEFAULT_REDTEAM_AGENT_MODE
    if techniques and any(t in AGENT_TECHNIQUE_VALUES for t in techniques):
        return DEFAULT_REDTEAM_AGENT_MODE
    return None


__all__ = [
    "DEFAULT_REDTEAM_AGENT_MODE",
    "AGENT_TECHNIQUE_VALUES",
    "resolve_redteam_llms",
    "resolve_redteam_agent_mode",
]