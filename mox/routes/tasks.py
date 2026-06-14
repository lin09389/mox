"""异步任务相关路由"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from mox.core.auth import User, get_current_active_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ============ 请求模型 ============


class TaskSubmitRequest(BaseModel):
    name: str
    func: str
    args: List[Any] = Field(default_factory=list)
    kwargs: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 1


# ============ 路由端点 ============


@router.post("/submit")
async def submit_task(
    request: TaskSubmitRequest,
    current_user: User = Depends(get_current_active_user),
):
    """提交异步任务"""
    try:
        from mox.core.tasks import get_task_queue, TaskPriority

        task_queue = get_task_queue()
        priority = (
            TaskPriority(request.priority) if 0 <= request.priority <= 3 else TaskPriority.NORMAL
        )
        task_id = task_queue.submit(
            name=request.name,
            func=lambda: {"status": "completed"},
            priority=priority,
        )

        return {
            "task_id": task_id,
            "status": "submitted",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
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
