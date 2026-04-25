import asyncio
import heapq
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from mox.core.types import TaskInfo, TaskStatus, TaskPriority
from mox.infrastructure.database import get_database

logger = logging.getLogger(__name__)

PRIORITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


class PriorityQueue:
    """异步优先级队列，使用 asyncio 原语实现"""

    def __init__(self):
        self._heap: List[tuple] = []
        self._enqueued: set = set()
        self._unfinished = 0
        self._not_empty = asyncio.Event()

    def put(self, task_id: int, priority: str = "medium"):
        """按优先级插入任务"""
        if task_id in self._enqueued:
            return
        order = PRIORITY_ORDER.get(priority, 2)
        heapq.heappush(self._heap, (order, task_id))
        self._enqueued.add(task_id)
        self._unfinished += 1
        self._not_empty.set()

    async def get(self) -> int:
        """获取下一个任务（阻塞直到有任务可用）"""
        while True:
            if self._heap:
                _, task_id = heapq.heappop(self._heap)
                return task_id
            self._not_empty.clear()
            # 双重检查，避免竞态
            if self._heap:
                continue
            await self._not_empty.wait()

    def task_done(self, task_id: int):
        """标记任务完成"""
        self._enqueued.discard(task_id)
        if self._unfinished > 0:
            self._unfinished -= 1

    def clear(self):
        """清除所有待处理任务"""
        self._heap.clear()
        self._enqueued.clear()
        self._unfinished = 0
        self._not_empty.clear()

    def empty(self) -> bool:
        return len(self._heap) == 0


class BackgroundTaskManager:
    """后台任务管理器，处理长耗时任务（如攻击、评估）"""

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.queue = PriorityQueue()
        self.workers: List[asyncio.Task] = []
        self._handlers: Dict[str, Callable] = {}
        self._running = False
        self._db = None
        self._start_lock = asyncio.Lock()

    async def start(self):
        """启动后台工作线程"""
        async with self._start_lock:
            if self._running:
                return

            self._running = True
            self._db = get_database()

            # 启动工作协程
            for i in range(self.max_concurrent):
                worker = asyncio.create_task(self._worker_loop(i))
                self.workers.append(worker)

            logger.info("BackgroundTaskManager started with %d workers", self.max_concurrent)

            # 恢复未完成的任务
            await self._recover_tasks()

    async def stop(self):
        """停止后台工作线程"""
        self._running = False
        for worker in self.workers:
            worker.cancel()

        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)

        self.workers = []
        self.queue.clear()
        self._db = None
        logger.info("BackgroundTaskManager stopped")

    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self._handlers[task_type] = handler
        logger.debug("Registered handler for task type: %s", task_type)

    async def submit_task(self,
                          task_type: str,
                          payload: Dict[str, Any],
                          name: Optional[str] = None,
                          priority: TaskPriority = TaskPriority.MEDIUM) -> TaskInfo:
        """提交新任务到队列"""
        if not self._db:
            self._db = get_database()

        # 1. 持久化到数据库
        task_id = await self._db.save_task(
            task_type=task_type,
            task_name=name or f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            payload=payload,
            priority=priority.value
        )

        task_info = await self._db.get_task(task_id)

        # 2. 加入优先级队列
        self.queue.put(task_id, priority.value)
        logger.info("Task %d (%s, priority=%s) submitted to queue", task_id, task_type, priority.value)

        return task_info

    async def _worker_loop(self, worker_id: int):
        """工作协程循环"""
        while self._running:
            try:
                task_id = await self.queue.get()

                try:
                    await self._execute_task(task_id)
                finally:
                    self.queue.task_done(task_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Worker %d error: %s", worker_id, e, exc_info=True)
                await asyncio.sleep(1)

    async def _execute_task(self, task_id: int):
        """执行单个任务"""
        task_info = await self._db.get_task(task_id)
        if not task_info:
            return

        if task_info.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
            return

        # 更新状态为运行中
        await self._db.update_task(
            task_id,
            status=TaskStatus.RUNNING.value,
            started_at=datetime.now()
        )
        logger.info("Executing task %d (%s)", task_id, task_info.task_type)

        handler = self._handlers.get(task_info.task_type)
        if not handler:
            error_msg = f"No handler registered for task type: {task_info.task_type}"
            await self._db.update_task(
                task_id,
                status=TaskStatus.FAILED.value,
                error=error_msg,
                finished_at=datetime.now()
            )
            logger.error(error_msg)
            return

        try:
            result = await handler(
                task_info.payload,
                progress_callback=lambda p: self._db.update_task(task_id, progress=p)
            )

            await self._db.update_task(
                task_id,
                status=TaskStatus.COMPLETED.value,
                result=result,
                progress=100.0,
                finished_at=datetime.now()
            )
            logger.info("Task %d completed successfully", task_id)

        except Exception as e:
            error_msg = str(e)
            await self._db.update_task(
                task_id,
                status=TaskStatus.FAILED.value,
                error=error_msg,
                finished_at=datetime.now()
            )
            logger.error("Task %d failed: %s", task_id, error_msg, exc_info=True)

    async def _recover_tasks(self):
        """恢复系统异常退出前未完成的任务"""
        pending_tasks = await self._db.get_pending_tasks()
        if not pending_tasks:
            return

        logger.info("Recovering %d pending/running tasks", len(pending_tasks))
        for task in pending_tasks:
            self.queue.put(task.id, task.priority.value if task.priority else "medium")


def reset_task_manager_singleton():
    """测试专用：重置全局单例"""
    global task_manager
    task_manager = BackgroundTaskManager()


# 全局任务管理器实例
task_manager = BackgroundTaskManager()
