"""自定义攻击插件示例"""

from typing import Dict, Any
from mox.infrastructure.plugin import BasePlugin, PluginMetadata
from mox.core.types import AttackType, AttackPayload, AttackOutcome, AttackResult


metadata = PluginMetadata(
    name="custom_attack",
    version="1.0.0",
    description="Custom attack plugin example",
    author="User",
    tags=["attack", "custom"],
)


class CustomAttackPlugin(BasePlugin):
    """自定义攻击插件"""

    metadata = metadata

    def initialize(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.custom_param = config.get("custom_param", "default")

    def cleanup(self) -> None:
        pass


class CustomAttackHandler:
    """自定义攻击处理器"""

    async def execute(self, payload: AttackPayload) -> AttackOutcome:
        return AttackOutcome(
            result=AttackResult.SUCCESS,
            original_prompt=payload.prompt,
            adversarial_prompt=f"{payload.prompt} [modified]",
            model_response="Custom response",
            iterations=1,
            success_score=1.0,
        )
