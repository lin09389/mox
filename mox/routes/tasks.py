"""异步任务相关路由"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from mox.routes.auth_helpers import require_optional_access
from mox.core.auth import User

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _format_task(item: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize task store entries for the frontend tray."""
    task_id = item.get("id") or item.get("task_id") or "unknown"
    source = item.get("source") or "queue"
    name = item.get("name")
    if not name:
        if source == "auto_redteam":
            name = f"自动红队 ({item.get('target_model', task_id)})"
        elif source == "attack_loop":
            name = f"攻击循环 ({task_id})"
        else:
            name = f"任务 {task_id}"

    progress = item.get("progress", 0)
    total = item.get("total") or 0
    if (not progress) and total:
        completed = item.get("completed") or 0
        progress = int((completed / total) * 100)

    status = item.get("status") or "unknown"
    if isinstance(status, str) and status.startswith("completed"):
        status = "completed"

    report_id = item.get("report_id")

    return {
        "id": task_id,
        "name": name,
        "status": status,
        "progress": min(100, max(0, int(progress or 0))),
        "source": source,
        "target_model": item.get("target_model"),
        "report_id": report_id,
        "total": total,
        "completed": item.get("completed"),
        "failed": item.get("failed"),
    }


def _collect_stored_tasks() -> List[Dict[str, Any]]:
    """从 TaskStore 收集任务"""
    try:
        from mox.core.task_store import get_task_store

        items = get_task_store().list_by_prefix("")
        return [_format_task(item) for item in items]
    except Exception:
        return []


# ============ 请求模型 ============


class TaskSubmitRequest(BaseModel):
    name: str
    func: str
    args: List[Any] = Field(default_factory=list)
    kwargs: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 1


# ============ 路由端点 ============


@router.get("")
async def list_tasks(
    current_user: User = Depends(require_optional_access),
) -> List[Dict[str, Any]]:
    """列出所有可见任务（攻击循环 + 队列任务）"""
    tasks_list = _collect_stored_tasks()

    try:
        from mox.core.tasks import get_task_queue

        task_queue = get_task_queue()
        for task_id, task in task_queue.list_tasks().items():
            status = task.status.value if hasattr(task.status, "value") else str(task.status)
            tasks_list.append(
                _format_task(
                    {
                        "id": task_id,
                        "name": task.name,
                        "status": status,
                        "progress": 100 if status == "completed" else 0,
                        "source": "queue",
                    }
                )
            )
    except Exception:
        pass

    return tasks_list


@router.post("/submit")
async def submit_task(
    request: TaskSubmitRequest,
    current_user: User = Depends(require_optional_access),
):
    """提交异步任务"""
    try:
        from mox.core.tasks import get_task_queue, TaskPriority

        get_task_queue()
        (TaskPriority(request.priority) if 0 <= request.priority <= 3 else TaskPriority.NORMAL)
        if not request.func:
            raise HTTPException(status_code=400, detail="func is required")

        raise HTTPException(
            status_code=501,
            detail=(
                "Generic task submission is not supported. "
                "Use /api/v1/attack-loop/start or /api/v1/auto-redteam/start instead."
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(require_optional_access),
):
    """获取任务状态"""
    try:
        from mox.core.tasks import get_task_queue

        task_queue = get_task_queue()
        status = task_queue.get_status(task_id)

        if status is None:
            raise HTTPException(status_code=404, detail="Task not found")

        return {
            "task_id": task_id,
            "status": status.value,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
