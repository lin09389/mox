"""视觉 / 多模态 LLM 辅助判断"""

from __future__ import annotations

VISION_MODEL_HINTS = (
    "gpt-4o",
    "gpt-4-vision",
    "gpt-4.1",
    "o1",
    "o3",
    "o4",
    "claude-3",
    "claude-sonnet-4",
    "claude-opus",
    "gemini",
    "gemini-2",
    "llava",
    "qwen-vl",
    "qwen2-vl",
    "glm-4v",
    "pixtral",
    "vision",
)


def supports_vision(model_name: str) -> bool:
    """启发式判断模型是否可能支持原生视觉输入"""
    name = (model_name or "").lower()
    return any(hint in name for hint in VISION_MODEL_HINTS)


def vision_data_url(image_base64: str, mime: str = "image/png") -> str:
    if image_base64.startswith("data:"):
        return image_base64
    return f"data:{mime};base64,{image_base64}"


__all__ = ["supports_vision", "vision_data_url", "VISION_MODEL_HINTS"]