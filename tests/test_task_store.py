"""TaskStore 测试"""

from mox.core.task_store import TaskStore


def test_task_store_memory_set_get():
    store = TaskStore()
    store._redis = None
    store.set("task-1", {"id": "task-1", "status": "running", "source": "test"})
    data = store.get("task-1")
    assert data is not None
    assert data["status"] == "running"


def test_task_store_update():
    store = TaskStore()
    store._redis = None
    store.set("task-2", {"id": "task-2", "status": "pending"})
    store.update("task-2", status="completed", progress=100)
    data = store.get("task-2")
    assert data["status"] == "completed"
    assert data["progress"] == 100


def test_task_store_delete():
    store = TaskStore()
    store._redis = None
    store.set("task-3", {"id": "task-3"})
    store.delete("task-3")
    assert store.get("task-3") is None