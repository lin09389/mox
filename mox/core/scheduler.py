"""定时任务调度模块"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import croniter

from mox.core.logging import get_logger
from mox.core.database import get_extended_database

logger = get_logger("scheduler")


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduleType(Enum):
    """调度类型"""

    CRON = "cron"
    INTERVAL = "interval"
    ONCE = "once"


@dataclass
class ScheduledTask:
    """定时任务"""

    task_id: str
    name: str
    task_type: str
    func: Callable[..., Awaitable[Any]]
    func_args: tuple = field(default_factory=tuple)
    func_kwargs: Dict[str, Any] = field(default_factory=dict)

    schedule_type: ScheduleType = ScheduleType.INTERVAL
    cron_expression: Optional[str] = None
    interval_minutes: Optional[int] = None

    is_active: bool = True
    enabled: bool = True

    status: TaskStatus = TaskStatus.PENDING
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    last_result: Any = None
    last_error: Optional[str] = None

    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self._db = None
        self._scheduler_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    def _get_db(self):
        if self._db is None:
            self._db = get_extended_database()
        return self._db

    def add_task(
        self,
        task_id: str,
        name: str,
        task_type: str,
        func: Callable[..., Awaitable[Any]],
        schedule_type: ScheduleType = ScheduleType.INTERVAL,
        cron_expression: Optional[str] = None,
        interval_minutes: int = 60,
        func_args: tuple = (),
        func_kwargs: Dict[str, Any] = None,
    ) -> ScheduledTask:
        """添加定时任务"""
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            task_type=task_type,
            func=func,
            schedule_type=schedule_type,
            cron_expression=cron_expression,
            interval_minutes=interval_minutes,
            func_args=func_args,
            func_kwargs=func_kwargs or {},
        )

        self._calculate_next_run(task)
        self.tasks[task_id] = task

        logger.info(f"Task added: {task_id} ({name}), next run: {task.next_run_at}")
        return task

    def _calculate_next_run(self, task: ScheduledTask) -> None:
        """计算下次运行时间"""
        now = datetime.now()

        if task.schedule_type == ScheduleType.CRON and task.cron_expression:
            try:
                cron = croniter.croniter(task.cron_expression, now)
                task.next_run_at = cron.get_next(datetime)
            except Exception as e:
                logger.error(f"Invalid cron expression: {task.cron_expression}: {e}")
                task.next_run_at = None
        elif task.schedule_type == ScheduleType.INTERVAL:
            task.next_run_at = now + timedelta(minutes=task.interval_minutes or 60)

    def remove_task(self, task_id: str) -> bool:
        """移除定时任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"Task removed: {task_id}")
            return True
        return False

    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self._calculate_next_run(self.tasks[task_id])
            return True
        return False

    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            self.tasks[task_id].next_run_at = None
            return True
        return False

    async def _execute_task(self, task: ScheduledTask) -> Any:
        """执行任务"""
        task.status = TaskStatus.RUNNING
        task.last_run_at = datetime.now()

        try:
            logger.info(f"Executing task: {task.task_id}")
            result = await task.func(*task.func_args, **task.func_kwargs)
            task.status = TaskStatus.SUCCESS
            task.last_result = result
            task.last_error = None
            task.success_count += 1
            logger.info(f"Task completed successfully: {task.task_id}")
            return result
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.last_error = str(e)
            task.failure_count += 1
            logger.error(f"Task failed: {task.task_id}: {e}")
            raise

    async def _run_scheduler(self):
        """调度器主循环"""
        while not self._stop_event.is_set():
            now = datetime.now()

            for task_id, task in list(self.tasks.items()):
                if not task.enabled or not task.is_active:
                    continue

                if task.status == TaskStatus.RUNNING:
                    continue

                if task.next_run_at and now >= task.next_run_at:
                    self._calculate_next_run(task)
                    task.run_count += 1

                    try:
                        await self._execute_task(task)

                        if self._db:
                            await self._db.update_scheduled_task_status(
                                task_id, success=(task.status == TaskStatus.SUCCESS)
                            )
                    except Exception as e:
                        logger.error(f"Task execution error: {task_id}: {e}")

            await asyncio.sleep(10)

    async def start(self):
        """启动调度器"""
        if self._scheduler_task is None:
            self._stop_event.clear()
            self._scheduler_task = asyncio.create_task(self._run_scheduler())
            logger.info("Task scheduler started")

    async def stop(self):
        """停止调度器"""
        self._stop_event.set()
        if self._scheduler_task:
            await self._scheduler_task
            self._scheduler_task = None
        logger.info("Task scheduler stopped")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            return {
                "task_id": task.task_id,
                "name": task.name,
                "task_type": task.task_type,
                "status": task.status.value,
                "enabled": task.enabled,
                "last_run_at": task.last_run_at.isoformat() if task.last_run_at else None,
                "next_run_at": task.next_run_at.isoformat() if task.next_run_at else None,
                "run_count": task.run_count,
                "success_count": task.success_count,
                "failure_count": task.failure_count,
                "last_error": task.last_error,
            }
        return None

    def get_all_tasks_status(self) -> List[Dict[str, Any]]:
        """获取所有任务状态"""
        return [self.get_task_status(task_id) for task_id in self.tasks]

    async def run_task_now(self, task_id: str) -> Any:
        """立即运行任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            return await self._execute_task(task)
        raise ValueError(f"Task not found: {task_id}")


_default_scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """获取全局调度器"""
    global _default_scheduler
    if _default_scheduler is None:
        _default_scheduler = TaskScheduler()
    return _default_scheduler
