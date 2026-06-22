"""CI/CD 集成模块"""

import hmac
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

import aiohttp

from mox.core.logging import get_logger

logger = get_logger("cicd")


class CICDStatus(Enum):
    """CI/CD状态"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class SecurityTestConfig:
    """安全测试配置"""

    config_id: Optional[int] = None
    config_name: str = ""
    project_name: str = ""
    project_url: str = ""
    security_threshold: float = 0.8
    attack_types: List[str] = field(default_factory=lambda: ["prompt_injection", "jailbreak"])
    defense_types: List[str] = field(default_factory=lambda: ["input_filter", "llm_judge"])
    auto_approve: bool = False
    webhook_url: str = ""
    webhook_secret: str = ""
    is_active: bool = True


@dataclass
class SecurityTestResult:
    """安全测试结果"""

    run_id: str
    config_name: str
    status: CICDStatus
    start_time: datetime
    end_time: Optional[datetime] = None

    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    success_rate: float = 0.0

    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


class CICDIntegration:
    """CI/CD集成"""

    def __init__(self):
        self._db = None

    def _get_db(self):
        from mox.core.database import get_extended_database

        if self._db is None:
            self._db = get_extended_database()
        return self._db

    async def create_security_test(
        self,
        config: SecurityTestConfig,
        created_by: str = "system",
    ) -> int:
        """创建安全测试配置"""
        db = self._get_db()
        data = {
            "config_name": config.config_name,
            "project_name": config.project_name,
            "project_url": config.project_url,
            "security_threshold": config.security_threshold,
            "attack_types": config.attack_types,
            "defense_types": config.defense_types,
            "auto_approve": config.auto_approve,
            "webhook_url": config.webhook_url,
            "webhook_secret": config.webhook_secret,
            "is_active": config.is_active,
            "created_by": created_by,
        }
        return await db.save_cicd_config(data)

    async def get_configs(self, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """获取CI/CD配置列表"""
        db = self._get_db()
        configs = await db.get_cicd_configs(is_active)
        return [
            {
                "id": c.id,
                "config_name": c.config_name,
                "project_name": c.project_name,
                "project_url": c.project_url,
                "security_threshold": c.security_threshold,
                "attack_types": c.attack_types,
                "is_active": c.is_active,
                "last_run_at": c.last_run_at.isoformat() if c.last_run_at else None,
            }
            for c in configs
        ]

    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        secret: str,
    ) -> bool:
        """验证Webhook签名"""
        if not signature or not secret:
            return False

        expected = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected}", signature)

    async def run_security_test(
        self,
        config: SecurityTestConfig,
        target_model: str,
    ) -> SecurityTestResult:
        """运行安全测试"""
        import uuid

        result = SecurityTestResult(
            run_id=str(uuid.uuid4()),
            config_name=config.config_name,
            status=CICDStatus.RUNNING,
            start_time=datetime.now(),
        )

        logger.info(f"Starting security test: {result.run_id}")

        try:
            from mox import LLMFactory, AttackEvaluator, DefenseEvaluator

            llm = LLMFactory.create_from_model_name(target_model)

            total_tests = 0
            passed_tests = 0

            for attack_type in config.attack_types:
                evaluator = AttackEvaluator(target_llm=llm, attack_type=attack_type)
                test_results = await evaluator.evaluate(max_cases=10)

                total_tests += len(test_results)
                passed_tests += sum(1 for r in test_results if r.success)

            for defense_type in config.defense_types:
                evaluator = DefenseEvaluator(target_llm=llm, defense_type=defense_type)
                test_results = await evaluator.evaluate(max_cases=10)

                total_tests += len(test_results)
                passed_tests += sum(1 for r in test_results if r.defense_success)

            result.total_tests = total_tests
            result.passed_tests = passed_tests
            result.failed_tests = total_tests - passed_tests
            result.success_rate = passed_tests / total_tests if total_tests > 0 else 0

            result.status = (
                CICDStatus.SUCCESS
                if result.success_rate >= config.security_threshold
                else CICDStatus.FAILED
            )

            if config.webhook_url:
                await self._send_webhook(config, result)

        except Exception as e:
            result.status = CICDStatus.FAILED
            result.error_message = str(e)
            logger.error(f"Security test failed: {e}")

        result.end_time = datetime.now()

        await self._save_run_history(config, result)

        return result

    async def _send_webhook(
        self,
        config: SecurityTestConfig,
        result: SecurityTestResult,
    ) -> None:
        """发送Webhook通知"""
        payload = {
            "run_id": result.run_id,
            "config_name": result.config_name,
            "status": result.status.value,
            "success_rate": result.success_rate,
            "total_tests": result.total_tests,
            "passed_tests": result.passed_tests,
            "timestamp": result.end_time.isoformat(),
        }

        headers = {"Content-Type": "application/json"}
        if config.webhook_secret:
            import json

            payload_str = json.dumps(payload)
            signature = hmac.new(
                config.webhook_secret.encode(),
                payload_str.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Signature"] = f"sha256={signature}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    config.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status < 200 or resp.status >= 300:
                        logger.warning(f"Webhook failed: {resp.status}")
                    else:
                        logger.info("Webhook sent successfully")
        except Exception as e:
            logger.error(f"Webhook error: {e}")

    async def _save_run_history(
        self,
        config: SecurityTestConfig,
        result: SecurityTestResult,
    ) -> None:
        """保存运行历史"""
        if config.config_id:
            db = self._get_db()
            run_result = {
                "run_id": result.run_id,
                "status": result.status.value,
                "success_rate": result.success_rate,
                "total_tests": result.total_tests,
                "passed_tests": result.passed_tests,
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat() if result.end_time else None,
            }
            await db.update_cicd_run_history(config.config_id, run_result)


_default_cicd: Optional[CICDIntegration] = None


def get_cicd_integration() -> CICDIntegration:
    """获取CI/CD集成实例"""
    global _default_cicd
    if _default_cicd is None:
        _default_cicd = CICDIntegration()
    return _default_cicd
