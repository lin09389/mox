"""Centralized LLM instance caching for API routes."""

from typing import Dict

from mox.core import BaseLLM, LLMFactory
from mox.core.config import settings

_llm_cache: Dict[str, BaseLLM] = {}


def get_cached_llm(
    model: str,
    *,
    use_ollama: bool = False,
    ollama_base_url: str = "http://localhost:11434/v1",
) -> BaseLLM:
    """Return a cached LLM instance for the given model configuration."""
    cache_key = f"{model}:{use_ollama}:{ollama_base_url}"

    if cache_key not in _llm_cache:
        if use_ollama:
            _llm_cache[cache_key] = LLMFactory.create_from_model_name(
                model,
                base_url=ollama_base_url,
            )
        elif model.startswith("abab") or model.startswith("minimax"):
            from mox.core import MiniMaxLLM

            _llm_cache[cache_key] = MiniMaxLLM(
                model=model,
                api_key=settings.MINIMAX_API_KEY,
                group_id=settings.MINIMAX_GROUP_ID,
            )
        else:
            _llm_cache[cache_key] = LLMFactory.create_from_model_name(model)

    return _llm_cache[cache_key]


def clear_llm_cache() -> None:
    """Clear the route-level LLM cache (primarily for tests)."""
    _llm_cache.clear()
