"""攻击执行器

负责执行单个攻击测试和批量并发测试。
使用统一攻击注册表（mox.attacks.registry）创建攻击实例。
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from mox.core import LLMFactory, AttackPayload, AttackType

from .config import AttackLoopConfig
from .result import AttackTestResult

logger = logging.getLogger(__name__)


class AttackExecutor:
    """攻击执行器

    基于官方攻击注册表创建攻击实例并执行测试。
    支持重试逻辑和批量并发执行。
    """

    def __init__(self, config: AttackLoopConfig):
        self.config = config

    def get_attack_name(self, attack_type: str) -> str:
        """获取攻击类型的显示名称"""
        from mox.attacks.registry import get_attack_type

        info = get_attack_type(attack_type)
        if info:
            return info.description or info.name
        return attack_type

    def attack_type_exists(self, attack_type: str) -> bool:
        """检查攻击类型是否存在"""
        from mox.attacks.registry import has_attack_type

        return has_attack_type(attack_type)

    async def check_ollama_connection(self) -> tuple[bool, Any]:
        """检查 Ollama 服务是否可用

        Returns:
            (是否可用, 模型列表或错误信息)
        """
        try:
            import aiohttp

            base_url = self.config.base_url.replace("/v1", "")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/api/tags", timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = [m["name"] for m in data.get("models", [])]
                        return True, models
                    return False, []
        except ImportError:
            # aiohttp 不可用时跳过检查
            return True, []
        except Exception as e:
            logger.error(f"Ollama 连接检查失败: {e}")
            return False, str(e)

    async def execute_single(
        self,
        model: str,
        attack_type: str,
        prompt: str,
        test_id: str,
    ) -> AttackTestResult:
        """执行单次攻击测试

        Args:
            model: 目标模型名称
            attack_type: 攻击类型
            prompt: 攻击提示
            test_id: 测试唯一标识

        Returns:
            测试结果
        """
        start_time = time.time()

        # 检查攻击类型是否存在
        if not self.attack_type_exists(attack_type):
            return AttackTestResult(
                test_id=test_id,
                timestamp=datetime.now().isoformat(),
                model=model,
                attack_type=attack_type,
                attack_name=f"未知({attack_type})",
                prompt=prompt,
                success=False,
                success_score=0.0,
                iterations=0,
                adversarial_prompt=None,
                model_response=None,
                error=f"未知的攻击类型: {attack_type}",
                duration=time.time() - start_time,
            )

        attack_name = self.get_attack_name(attack_type)

        # 创建 LLM 实例
        try:
            llm = LLMFactory.create_from_model_name(
                model,
                base_url=self.config.base_url,
                api_key="ollama",
            )
        except Exception as e:
            return AttackTestResult(
                test_id=test_id,
                timestamp=datetime.now().isoformat(),
                model=model,
                attack_type=attack_type,
                attack_name=attack_name,
                prompt=prompt,
                success=False,
                success_score=0.0,
                iterations=0,
                adversarial_prompt=None,
                model_response=None,
                error=f"LLM 创建失败: {e}",
                duration=time.time() - start_time,
            )

        # 创建攻击实例（通过统一注册表）
        try:
            from mox.attacks.registry import create_attack_instance

            attack = create_attack_instance(
                attack_type=attack_type,
                llm=llm,
                max_iterations=self.config.max_iterations,
            )
        except Exception as e:
            return AttackTestResult(
                test_id=test_id,
                timestamp=datetime.now().isoformat(),
                model=model,
                attack_type=attack_type,
                attack_name=attack_name,
                prompt=prompt,
                success=False,
                success_score=0.0,
                iterations=0,
                adversarial_prompt=None,
                model_response=None,
                error=f"攻击实例创建失败: {e}",
                duration=time.time() - start_time,
            )

        # 构建攻击载荷
        payload = AttackPayload(
            attack_type=AttackType.JAILBREAK,  # 使用通用类型
            prompt=prompt,
            target_behavior=prompt,
        )

        # 执行攻击（带重试）
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                outcome = await attack.generate_attack(payload)

                success = outcome.success_score >= self.config.success_threshold

                return AttackTestResult(
                    test_id=test_id,
                    timestamp=datetime.now().isoformat(),
                    model=model,
                    attack_type=attack_type,
                    attack_name=attack_name,
                    prompt=prompt,
                    success=success,
                    success_score=outcome.success_score,
                    iterations=outcome.iterations if hasattr(outcome, 'iterations') else 1,
                    adversarial_prompt=outcome.adversarial_prompt if hasattr(outcome, 'adversarial_prompt') else None,
                    model_response=outcome.model_response if hasattr(outcome, 'model_response') else (
                        outcome.response if hasattr(outcome, 'response') else None
                    ),
                    error=None,
                    duration=time.time() - start_time,
                    metadata={"attempt": attempt + 1},
                )
            except Exception as e:
                last_error = e
                logger.warning(
                    f"攻击执行失败 (尝试 {attempt + 1}/{self.config.max_retries}): "
                    f"test_id={test_id}, error={e}"
                )
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)

        # 所有重试都失败
        return AttackTestResult(
            test_id=test_id,
            timestamp=datetime.now().isoformat(),
            model=model,
            attack_type=attack_type,
            attack_name=attack_name,
            prompt=prompt,
            success=False,
            success_score=0.0,
            iterations=0,
            adversarial_prompt=None,
            model_response=None,
            error=f"攻击执行失败 (尝试 {self.config.max_retries} 次): {last_error}",
            duration=time.time() - start_time,
            metadata={"attempt": self.config.max_retries},
        )

    async def execute_batch(
        self,
        test_cases: List[Dict[str, Any]],
    ) -> List[AttackTestResult]:
        """并行执行一批测试

        Args:
            test_cases: 测试用例列表，每个用例包含 model, attack_type, prompt, test_id

        Returns:
            测试结果列表，顺序与输入一致
        """
        tasks = []
        for test in test_cases:
            task = self.execute_single(
                model=test["model"],
                attack_type=test["attack_type"],
                prompt=test["prompt"],
                test_id=test["test_id"],
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                attack_name = self.get_attack_name(test_cases[i]["attack_type"])
                processed_results.append(AttackTestResult(
                    test_id=test_cases[i]["test_id"],
                    timestamp=datetime.now().isoformat(),
                    model=test_cases[i]["model"],
                    attack_type=test_cases[i]["attack_type"],
                    attack_name=attack_name,
                    prompt=test_cases[i]["prompt"],
                    success=False,
                    success_score=0.0,
                    iterations=0,
                    adversarial_prompt=None,
                    model_response=None,
                    error=f"任务异常: {result}",
                    duration=0.0,
                ))
            else:
                processed_results.append(result)

        return processed_results
