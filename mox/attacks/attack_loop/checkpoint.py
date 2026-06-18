"""检查点管理器

支持断点续跑：
- 任务执行过程中按间隔自动保存检查点
- 任务中断后可以从检查点恢复，跳过已完成测试
- 检查点持久化到 output_dir/checkpoints/{task_id}/checkpoint.json
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .result import AttackTestResult


logger = logging.getLogger(__name__)


class CheckpointManager:
    """检查点管理器

    检查点文件结构：
    {
        "task_id": "...",
        "timestamp": "2024-01-01T00:00:00",
        "completed_tests": ["test_id_1", "test_id_2", ...],
        "results": [...AttackTestResult...],
        "config_hash": "...",
        "results_count": 100
    }

    持久化策略：
    - 检查点保存在 output_dir/checkpoints/{task_id}/checkpoint.json
    - 每个 task_id 有独立的检查点目录，避免冲突
    - 任务完成后可通过 clear() 清理检查点
    """

    def __init__(self, output_dir: str, task_id: Optional[str] = None):
        """
        Args:
            output_dir: 输出根目录
            task_id: 任务 ID，决定检查点子目录
        """
        self.output_dir = Path(output_dir)
        self.task_id = task_id or "default"
        self.checkpoint_dir = self.output_dir / "checkpoints" / self.task_id
        self.checkpoint_file = self.checkpoint_dir / "checkpoint.json"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """加载检查点

        Returns:
            检查点数据字典，至少包含 completed_tests 和 results 字段
        """
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 将 results 反序列化为 AttackTestResult 对象
                results_dicts = data.get("results", [])
                results = [AttackTestResult.from_dict(r) for r in results_dicts]
                data["results"] = results

                completed = data.get("completed_tests", [])
                logger.info(
                    f"加载检查点成功: task_id={self.task_id}, "
                    f"已完成 {len(completed)} 个测试, "
                    f"结果 {len(results)} 条"
                )
                return data
            except Exception as e:
                logger.warning(f"加载检查点失败，将从头开始: {e}")

        return {"completed_tests": [], "results": [], "task_id": self.task_id}

    def save(
        self,
        completed_tests: List[str],
        results: List[AttackTestResult],
        config_hash: Optional[str] = None,
    ):
        """保存检查点

        Args:
            completed_tests: 已完成测试的 ID 列表
            results: 所有测试结果
            config_hash: 配置哈希，用于验证续跑时配置是否一致
        """
        try:
            # 原子写入：先写临时文件再替换
            tmp_file = self.checkpoint_file.with_suffix(".json.tmp")
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "task_id": self.task_id,
                        "timestamp": datetime.now().isoformat(),
                        "completed_tests": completed_tests,
                        "results": [r.to_dict() for r in results],
                        "config_hash": config_hash,
                        "results_count": len(results),
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            tmp_file.replace(self.checkpoint_file)

            logger.debug(
                f"检查点已保存: task_id={self.task_id}, "
                f"completed={len(completed_tests)}, results={len(results)}"
            )
        except Exception as e:
            logger.error(f"保存检查点失败: {e}")

    def clear(self):
        """清除检查点文件"""
        if self.checkpoint_file.exists():
            try:
                self.checkpoint_file.unlink()
                logger.info(f"检查点已清除: task_id={self.task_id}")
            except Exception as e:
                logger.warning(f"清除检查点失败: {e}")

    def exists(self) -> bool:
        """检查检查点是否存在"""
        return self.checkpoint_file.exists()

    def get_checkpoint_path(self) -> Path:
        """获取检查点文件路径"""
        return self.checkpoint_file
