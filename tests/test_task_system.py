import pytest
import asyncio
import os

from mox.infrastructure.database import init_database, close_database, reset_database_singleton
from mox.infrastructure.worker import BackgroundTaskManager, reset_task_manager_singleton
from mox.core.types import TaskStatus, TaskPriority


@pytest.fixture(autouse=True)
def _reset_globals():
    """每个测试前后重置全局单例，防止状态串扰"""
    reset_database_singleton()
    reset_task_manager_singleton()
    yield
    reset_database_singleton()
    reset_task_manager_singleton()


@pytest.fixture
def db_file():
    path = "test_mox.db"
    if os.path.exists(path):
        os.remove(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def db_file2():
    path = "test_mox_recovery.db"
    if os.path.exists(path):
        os.remove(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.mark.asyncio
async def test_task_submission_and_successful_execution(db_file):
    """验证任务从提交到成功完成的完整链路，使用 stub handler 不依赖真实 LLM"""
    db = await init_database(db_url=f"sqlite+aiosqlite:///{db_file}")
    tm = BackgroundTaskManager(max_concurrent=1)

    handler_called = asyncio.Event()
    handler_result = {"status": "success", "data": "stub"}

    async def stub_handler(payload, progress_callback=None):
        if progress_callback:
            await progress_callback(50.0)
        handler_called.set()
        return handler_result

    tm.register_handler("attack", stub_handler)
    await tm.start()

    try:
        task_info = await tm.submit_task(
            task_type="attack",
            payload={"attack_name": "gcg", "n_steps": 10},
            name="stub_attack",
            priority=TaskPriority.HIGH,
        )

        assert task_info.id is not None
        assert task_info.status == TaskStatus.PENDING

        # Wait for task to complete (with timeout)
        max_wait = 10
        while max_wait > 0:
            updated = await db.get_task(task_info.id)
            if updated.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                break
            await asyncio.sleep(0.5)
            max_wait -= 1

        final = await db.get_task(task_info.id)
        assert handler_called.is_set(), "Handler was never invoked"
        assert final.status == TaskStatus.COMPLETED, f"Task should be COMPLETED, got {final.status}"
        assert final.result == handler_result
        assert final.error is None, f"Unexpected error: {final.error}"
        assert final.progress == 100.0

    finally:
        await tm.stop()


@pytest.mark.asyncio
async def test_task_recovery(db_file2):
    """验证重启后 pending 任务能被恢复并执行"""
    db = await init_database(db_url=f"sqlite+aiosqlite:///{db_file2}")

    task_id = await db.save_task(
        task_type="attack",
        task_name="RecoverMe",
        payload={"attack_name": "test"},
        priority="high",
    )

    tm = BackgroundTaskManager(max_concurrent=1)
    handler_called = asyncio.Event()

    async def stub_handler(payload, progress_callback=None):
        handler_called.set()
        return {"ok": True}

    tm.register_handler("attack", stub_handler)
    await tm.start()

    try:
        await asyncio.sleep(2)
        recovered = await db.get_task(task_id)
        assert handler_called.is_set(), "Recovery handler was not called"
        assert recovered.status in (TaskStatus.COMPLETED,), \
            f"Task should be COMPLETED, got {recovered.status}. Error: {recovered.error}"

    finally:
        await tm.stop()


@pytest.mark.asyncio
async def test_priority_ordering(db_file):
    """验证高优先级任务先于低优先级任务执行"""
    db = await init_database(db_url=f"sqlite+aiosqlite:///{db_file}")
    tm = BackgroundTaskManager(max_concurrent=1)

    execution_order = []

    async def ordered_handler(payload, progress_callback=None):
        execution_order.append(payload["name"])
        return {}

    tm.register_handler("attack", ordered_handler)

    # 在启动 worker 之前先提交所有任务，确保优先级排序生效
    await tm.submit_task(
        task_type="attack", payload={"name": "low"}, name="low",
        priority=TaskPriority.LOW
    )
    await tm.submit_task(
        task_type="attack", payload={"name": "medium"}, name="medium",
        priority=TaskPriority.MEDIUM
    )
    await tm.submit_task(
        task_type="attack", payload={"name": "high"}, name="high",
        priority=TaskPriority.HIGH
    )
    await tm.submit_task(
        task_type="attack", payload={"name": "critical"}, name="critical",
        priority=TaskPriority.CRITICAL
    )

    await tm.start()

    try:
        await asyncio.sleep(2)

        assert execution_order == ["critical", "high", "medium", "low"], \
            f"Expected [critical, high, medium, low], got {execution_order}"

    finally:
        await tm.stop()
