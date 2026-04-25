import logging
from typing import Dict, Any, Optional

from mox.core.types import TaskInfo, TaskPriority, AttackPayload
from mox.core.llm import LLMFactory, ModelProvider
from mox.infrastructure.worker import task_manager
from mox.attacks.registry import create_attack_instance

logger = logging.getLogger(__name__)


class AttackOrchestrator:
    """攻击编排器，负责提交和管理攻击任务"""

    def __init__(self):
        self._initialized = False

    async def initialize(self):
        """初始化编排器，注册处理器并启动任务管理器"""
        if self._initialized:
            return

        task_manager.register_handler("attack", self._handle_attack_task)

        await task_manager.start()
        self._initialized = True
        logger.info("AttackOrchestrator initialized")

    async def shutdown(self):
        """关闭编排器，停止任务管理器并重置状态"""
        logger.info("Shutting down AttackOrchestrator")
        await task_manager.stop()
        self._initialized = False

    async def submit_attack(self,
                            attack_name: str,
                            target_config: Dict[str, Any],
                            attack_params: Optional[Dict[str, Any]] = None,
                            name: Optional[str] = None,
                            priority: TaskPriority = TaskPriority.MEDIUM) -> TaskInfo:
        """提交一个攻击任务"""
        if not self._initialized:
            await self.initialize()

        payload = {
            "attack_name": attack_name,
            "target_config": target_config,
            "attack_params": attack_params or {}
        }

        return await task_manager.submit_task(
            task_type="attack",
            payload=payload,
            name=name or f"Attack_{attack_name}",
            priority=priority
        )

    async def _handle_attack_task(self, payload: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """具体的攻击任务处理逻辑"""
        attack_name = payload["attack_name"]
        target_config = payload["target_config"]
        attack_params = payload.get("attack_params", {})

        # 1. 从 target_config 构建真正的 BaseLLM 实例
        target_llm = self._build_llm_from_config(target_config)

        # 2. 创建攻击实例
        attack_instance = create_attack_instance(attack_name, target_llm)
        if not attack_instance:
            raise ValueError(f"Failed to create attack instance for: {attack_name}")

        # 3. 构造攻击载荷
        prompt_text = attack_params.get("prompt", f"Execute {attack_name} attack")
        target_behavior = attack_params.get("target_behavior", "bypass safety restrictions")

        attack_payload = AttackPayload(
            attack_type=attack_name,
            prompt=prompt_text,
            target_behavior=target_behavior,
            metadata=attack_params.get("metadata", {}),
        )

        # 4. 执行攻击
        logger.info("Executing attack '%s' on model '%s'", attack_name, target_llm.model)

        if progress_callback:
            await progress_callback(10.0)

        try:
            outcome = await attack_instance.generate_attack(attack_payload)
        except Exception as e:
            logger.error("Attack '%s' failed: %s", attack_name, e, exc_info=True)
            raise

        if progress_callback:
            await progress_callback(100.0)

        return {
            "status": "success",
            "attack_name": attack_name,
            "result": outcome.result.value,
            "success_score": outcome.success_score,
            "response": outcome.response,
            "adversarial_prompt": outcome.adversarial_prompt,
            "iterations": outcome.iterations,
        }

    @staticmethod
    def _build_llm_from_config(target_config: Dict[str, Any]):
        """从配置字典构建 BaseLLM 实例（而非 LLMConfig 模型）"""
        provider_str = target_config.get("provider", "").lower()
        model_str = target_config.get("model", "gpt-3.5-turbo")
        temperature = target_config.get("temperature", 0.7)
        max_tokens = target_config.get("max_tokens", 2048)
        extra_kwargs = {
            k: v for k, v in target_config.items()
            if k not in ("provider", "model", "temperature", "max_tokens")
        }

        if provider_str:
            try:
                provider = ModelProvider(provider_str)
                return LLMFactory.create(
                    provider=provider,
                    model=model_str,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **extra_kwargs,
                )
            except (ValueError, KeyError) as e:
                logger.warning(
                    "Unknown provider '%s', falling back to model-name lookup: %s",
                    provider_str, e
                )

        return LLMFactory.create_from_model_name(
            model=model_str,
            temperature=temperature,
            max_tokens=max_tokens,
            **extra_kwargs,
        )


_orchestrator_instance: Optional[AttackOrchestrator] = None


def get_orchestrator() -> AttackOrchestrator:
    """获取全局编排器实例（惰性创建，每次获取时检查是否需要重新初始化）"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AttackOrchestrator()
    return _orchestrator_instance


orchestrator = get_orchestrator()
