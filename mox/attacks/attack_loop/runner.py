"""攻击循环运行器

整合配置、执行器、检查点、报告生成器，提供完整的攻击循环运行能力。
支持：
- 并发执行（基于 max_concurrency 的信号量控制）
- 断点续跑（基于 CheckpointManager）
- 随机提示生成
- 进度回调
- 停止/暂停控制
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Any, Optional

from .checkpoint import CheckpointManager
from .config import AttackLoopConfig
from .executor import AttackExecutor
from .prompt_generator import PromptGenerator
from .report import ReportGenerator
from .result import AttackTestResult, TestStatistics


logger = logging.getLogger(__name__)

# 进度回调函数类型
ProgressCallback = Callable[[Dict[str, Any]], None]


class AttackLoopRunner:
    """攻击循环运行器

    完整的攻击循环编排器，负责：
    1. 生成测试用例（含随机提示）
    2. 管理并发执行
    3. 自动保存检查点
    4. 支持从检查点恢复
    5. 进度回调通知
    6. 生成最终报告
    """

    def __init__(
        self,
        config: AttackLoopConfig,
        task_id: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        """
        Args:
            config: 攻击循环配置
            task_id: 任务 ID，用于检查点和日志标识
            progress_callback: 进度回调函数，接收状态字典
        """
        self.config = config
        self.task_id = task_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.progress_callback = progress_callback

        # 执行器和报告生成器
        self.executor = AttackExecutor(config)
        self.report_gen = ReportGenerator(config.output_dir)

        # 运行时状态
        self.results: List[AttackTestResult] = []
        self.completed_tests: List[str] = []
        self._stop_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # 初始状态为非暂停

        # 检查点管理器
        self.checkpoint_manager: Optional[CheckpointManager] = None
        if config.checkpoint_enabled:
            self.checkpoint_manager = CheckpointManager(
                output_dir=config.output_dir,
                task_id=self.task_id,
            )

        # 统计
        self.start_time: Optional[datetime] = None
        self.total_tests: int = 0

    def _compute_config_hash(self) -> str:
        """计算配置哈希，用于验证续跑时配置一致性"""
        config_dict = self.config.to_dict()
        # 排除不影响测试用例的字段
        for key in ["checkpoint_enabled", "checkpoint_interval", "log_file", "log_level", "output_dir"]:
            config_dict.pop(key, None)
        config_str = json.dumps(config_dict, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(config_str.encode("utf-8")).hexdigest()

    def _generate_prompts(self) -> List[str]:
        """生成测试提示列表

        如果启用了随机提示，则使用 PromptGenerator 生成；
        否则使用配置中的 prompts。
        """
        if self.config.random_prompts:
            templates = self.config.random_prompt_templates or None
            generator = PromptGenerator(templates=templates)
            return generator.generate_unique(self.config.random_prompt_count)
        return list(self.config.prompts)

    def _generate_test_cases(self, prompts: List[str]) -> List[Dict[str, Any]]:
        """生成所有测试用例

        Returns:
            测试用例列表，每个用例包含 test_id, model, attack_type, prompt
        """
        test_cases = []
        for model in self.config.models:
            for attack_type in self.config.attack_types:
                for i, prompt in enumerate(prompts):
                    for j in range(self.config.iterations_per_combo):
                        test_id = f"{model}_{attack_type}_p{i}_iter{j}"
                        test_cases.append({
                            "test_id": test_id,
                            "model": model,
                            "attack_type": attack_type,
                            "prompt": prompt,
                        })
        return test_cases

    def _report_progress(self, **kwargs):
        """触发进度回调"""
        if self.progress_callback:
            elapsed = 0.0
            if self.start_time:
                elapsed = (datetime.now() - self.start_time).total_seconds()

            completed = len(self.completed_tests)
            successful = sum(1 for r in self.results if r.success)
            failed = sum(1 for r in self.results if not r.success and not r.error)
            errors = sum(1 for r in self.results if r.error)

            progress = {
                "task_id": self.task_id,
                "total": self.total_tests,
                "completed": completed,
                "successful": successful,
                "failed": failed,
                "errors": errors,
                "elapsed_seconds": elapsed,
                "progress_percent": (
                    completed / self.total_tests * 100
                    if self.total_tests > 0
                    else 0
                ),
                **kwargs,
            }
            try:
                self.progress_callback(progress)
            except Exception as e:
                logger.warning(f"进度回调执行失败: {e}")

    def _should_save_checkpoint(self) -> bool:
        """判断是否应该保存检查点"""
        if not self.config.checkpoint_enabled or self.checkpoint_manager is None:
            return False
        completed = len(self.completed_tests)
        return completed > 0 and completed % self.config.checkpoint_interval == 0

    def _save_checkpoint(self):
        """保存检查点"""
        if self.checkpoint_manager:
            self.checkpoint_manager.save(
                completed_tests=self.completed_tests.copy(),
                results=self.results.copy(),
                config_hash=self._compute_config_hash(),
            )

    def load_checkpoint(self) -> Dict[str, Any]:
        """加载检查点

        Returns:
            检查点数据，包含 completed_tests 和 results
        """
        if not self.checkpoint_manager:
            return {"completed_tests": [], "results": []}

        data = self.checkpoint_manager.load()

        # 验证配置哈希
        config_hash = data.get("config_hash")
        if config_hash and config_hash != self._compute_config_hash():
            logger.warning(
                "检查点配置哈希不匹配，可能配置已变更。"
                "为保证结果一致性，将忽略检查点从头开始。"
            )
            return {"completed_tests": [], "results": []}

        return data

    def stop(self):
        """请求停止任务"""
        self._stop_event.set()
        self._pause_event.set()  # 确保不会卡在暂停状态

    def pause(self):
        """暂停任务"""
        self._pause_event.clear()

    def resume(self):
        """恢复任务"""
        self._pause_event.set()

    async def run(self, resume: bool = True) -> Dict[str, Any]:
        """运行完整的攻击循环

        Args:
            resume: 是否从检查点恢复（如果存在）

        Returns:
            运行结果字典，包含 results, stats, report_paths 等
        """
        self.start_time = datetime.now()
        self._report_progress(status="starting")

        # 1. 生成提示
        prompts = self._generate_prompts()
        if not prompts:
            raise ValueError("没有可用的测试提示（prompts 为空且未启用随机提示）")

        # 2. 生成所有测试用例
        all_test_cases = self._generate_test_cases(prompts)
        self.total_tests = len(all_test_cases)
        logger.info(f"生成 {len(all_test_cases)} 个测试用例")

        # 3. 从检查点恢复
        if resume and self.config.checkpoint_enabled:
            checkpoint_data = self.load_checkpoint()
            self.completed_tests = checkpoint_data.get("completed_tests", [])
            self.results = checkpoint_data.get("results", [])

            if self.completed_tests:
                logger.info(
                    f"从检查点恢复: 已完成 {len(self.completed_tests)}/{self.total_tests} 个测试，"
                    f"剩余 {self.total_tests - len(self.completed_tests)} 个"
                )
                self._report_progress(status="resuming")

        # 4. 过滤掉已完成的测试
        completed_set = set(self.completed_tests)
        remaining_cases = [tc for tc in all_test_cases if tc["test_id"] not in completed_set]

        if not remaining_cases:
            logger.info("所有测试均已完成，无需重新执行")
            self._report_progress(status="completed")
            return self._finalize()

        # 5. 并发执行剩余测试
        self._report_progress(status="running")
        await self._execute_with_concurrency(remaining_cases)

        # 6. 最终检查点和报告
        final_status = "stopped" if self._stop_event.is_set() else "completed"
        self._report_progress(status=final_status)

        return self._finalize(status=final_status)

    async def _execute_with_concurrency(self, test_cases: List[Dict[str, Any]]):
        """按并发限制执行测试用例

        使用信号量控制并发，按批处理以支持检查点保存和进度更新。
        """
        semaphore = asyncio.Semaphore(self.config.max_concurrency)
        completed_in_batch = 0

        async def _run_with_semaphore(test_case: Dict[str, Any]) -> AttackTestResult:
            async with semaphore:
                # 检查暂停
                await self._pause_event.wait()
                # 检查停止
                if self._stop_event.is_set():
                    # 返回 None 表示跳过（停止时不执行）
                    return None  # type: ignore
                return await self.executor.execute_single(**{
                    k: v for k, v in test_case.items()
                    if k in ("model", "attack_type", "prompt", "test_id")
                })

        # 分批处理，每批大小等于并发数，便于在批次间保存检查点
        batch_size = max(self.config.max_concurrency, self.config.checkpoint_interval)
        total = len(test_cases)

        for start_idx in range(0, total, batch_size):
            if self._stop_event.is_set():
                break

            batch = test_cases[start_idx:start_idx + batch_size]
            tasks = [_run_with_semaphore(tc) for tc in batch]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for test_case, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"测试执行异常: {test_case['test_id']} - {result}")
                    continue

                if result is None:
                    continue  # 被停止的任务

                self.results.append(result)
                self.completed_tests.append(test_case["test_id"])
                completed_in_batch += 1

                # 检查是否需要保存检查点
                if self._should_save_checkpoint():
                    self._save_checkpoint()

            # 延迟
            if not self._stop_event.is_set() and start_idx + batch_size < total:
                await asyncio.sleep(self.config.delay_between_tests)

            # 更新进度
            self._report_progress(status="running")

        # 任务结束时保存一次最终检查点
        if self.config.checkpoint_enabled:
            self._save_checkpoint()

    def _finalize(self, status: str = "completed") -> Dict[str, Any]:
        """完成运行，生成统计和报告"""
        stats = TestStatistics.calculate(self.results)

        # 生成报告
        report_paths = {}
        if self.results:
            report_paths = self.report_gen.save_all_reports(
                self.results, stats, self.config
            )
            logger.info(f"报告已生成: {report_paths}")

        # 任务完成后清理检查点
        if status == "completed" and self.checkpoint_manager:
            self.checkpoint_manager.clear()

        elapsed = (
            (datetime.now() - self.start_time).total_seconds()
            if self.start_time
            else 0
        )

        return {
            "task_id": self.task_id,
            "status": status,
            "total_tests": self.total_tests,
            "completed": len(self.completed_tests),
            "results": self.results,
            "stats": stats,
            "report_paths": report_paths,
            "elapsed_seconds": elapsed,
        }


def run_attack_loop(
    config: AttackLoopConfig,
    task_id: Optional[str] = None,
    progress_callback: Optional[ProgressCallback] = None,
    resume: bool = True,
) -> Dict[str, Any]:
    """同步运行攻击循环的便捷函数

    Args:
        config: 攻击循环配置
        task_id: 任务 ID
        progress_callback: 进度回调
        resume: 是否从检查点恢复

    Returns:
        运行结果字典
    """
    runner = AttackLoopRunner(config, task_id=task_id, progress_callback=progress_callback)
    return asyncio.run(runner.run(resume=resume))


async def run_attack_loop_async(
    config: AttackLoopConfig,
    task_id: Optional[str] = None,
    progress_callback: Optional[ProgressCallback] = None,
    resume: bool = True,
) -> Dict[str, Any]:
    """异步运行攻击循环的便捷函数"""
    runner = AttackLoopRunner(config, task_id=task_id, progress_callback=progress_callback)
    return await runner.run(resume=resume)
