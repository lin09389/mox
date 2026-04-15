"""异步任务队列模块"""

import asyncio
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from .logging import get_logger

logger = get_logger("tasks")


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class TaskResult:
    """任务结果"""

    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """任务定义"""

    task_id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskQueue:
    """异步任务队列

    修复: 使用 (priority, sequence_number) 作为 PriorityQueue 的排序键，
    避免相同优先级任务因不可比较的 Task 对象而抛出 TypeError。
    """

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._tasks: Dict[str, Task] = {}
        self._workers: List[asyncio.Task] = []
        self._running = False
        self._sequence = 0

    async def start(self):
        """启动任务队列"""
        self._running = True
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)
        logger.info(f"Task queue started with {self.max_workers} workers")

    async def stop(self):
        """停止任务队列"""
        self._running = False
        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("Task queue stopped")

    async def _worker(self, worker_id: int):
        """工作协程"""
        while self._running:
            try:
                priority, seq, task = await self._queue.get()
                await self._execute_task(task)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")

    async def _execute_task(self, task: Task):
        """执行任务"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        logger.info(f"Executing task: {task.name} ({task.task_id})")

        try:
            if asyncio.iscoroutinefunction(task.func):
                task.result = await task.func(*task.args, **task.kwargs)
            else:
                task.result = task.func(*task.args, **task.kwargs)

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            logger.info(f"Task completed: {task.name} ({task.task_id})")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            logger.error(f"Task failed: {task.name} ({task.task_id}): {e}")

    def submit(
        self,
        name: str,
        func: Callable,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        **kwargs,
    ) -> str:
        """提交任务"""
        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
        )
        self._tasks[task_id] = task
        self._sequence += 1
        self._queue.put_nowait((priority.value, self._sequence, task))
        logger.info(f"Task submitted: {name} ({task_id})")
        return task_id

    async def get_result(self, task_id: str, timeout: Optional[float] = None) -> TaskResult:
        """获取任务结果"""
        if task_id not in self._tasks:
            raise ValueError(f"Task not found: {task_id}")

        task = self._tasks[task_id]
        if timeout:
            start = datetime.now()
            while task.status == TaskStatus.PENDING or task.status == TaskStatus.RUNNING:
                if (datetime.now() - start).total_seconds() > timeout:
                    raise TimeoutError(f"Task timeout: {task_id}")
                await asyncio.sleep(0.1)

        return TaskResult(
            task_id=task.task_id,
            status=task.status,
            result=task.result,
            error=task.error,
            started_at=task.started_at,
            completed_at=task.completed_at,
        )

    def get_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        if task_id in self._tasks:
            return self._tasks[task_id].status
        return None

    def cancel(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                return True
        return False

    def get_queue_size(self) -> Dict[str, int]:
        """获取队列大小"""
        return {
            "pending": self._queue.qsize(),
            "total_tasks": len(self._tasks),
        }


_task_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """获取全局任务队列实例"""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue(max_workers=4)
    return _task_queue
