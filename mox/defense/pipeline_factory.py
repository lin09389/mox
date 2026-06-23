"""默认防御管道工厂 — 组合多层防御供红队闭环评测使用"""

from typing import Optional

from mox.defense.input_filter import DefensePipeline, InputFilter, KeywordDetector
from mox.defense.injection_detector import PromptInjectionDetector
from mox.defense.output_filter import OutputFilter


def create_default_defense_pipeline(
    use_llm_judge: bool = False,
    judge_llm=None,
) -> DefensePipeline:
    """构建标准多层防御管道：关键词 → 注入检测 → 输出过滤"""
    filters = [
        KeywordDetector(),
        InputFilter(),
        PromptInjectionDetector(judge_llm=judge_llm if use_llm_judge else None),
        OutputFilter(),
    ]
    return DefensePipeline(filters=filters)


__all__ = ["create_default_defense_pipeline"]