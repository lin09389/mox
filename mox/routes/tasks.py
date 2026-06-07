"""异步任务相关路由"""
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from mox.infrastructure.auth import User, get_current_active_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ============ 请求模型 ============

class TaskSubmitRequest(BaseModel):
    name: str
    func: str = Field(
        ...,
        description=(
            "Registered task function name. Must be one of the names "
            "returned by GET /tasks/registered. The previous "
            "implementation accepted any string and silently ignored "
            "it; we now reject unknown names with 400 so callers know "
            "the request is a no-op."
        ),
    )
    args: List[Any] = Field(default_factory=list)
    kwargs: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=1, ge=0, le=3)


# ============ 路由端点 ============


@router.get("/registered")
async def list_registered_tasks() -> Dict[str, Any]:
    """Return the list of task function names accepted by /submit.

    New endpoint — the previous version of the submit endpoint
    silently dropped the request body and ran a no-op lambda, so
    callers had no way to discover which functions were actually
    dispatchable.  This endpoint makes the allow-list explicit.
    """
    from mox.infrastructure.tasks import get_registered_task_names

    return {"registered_tasks": get_registered_task_names()}


@router.post("/submit")
async def submit_task(
    request: TaskSubmitRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Submit an async task for background execution.

    The previous implementation ignored ``func``/``args``/``kwargs``
    and always submitted a no-op lambda:

        func=lambda: {"status": "completed"}

    That made the endpoint a placeholder.  Now we look up
    ``request.func`` in the allow-listed TASK_REGISTRY and pass
    the user-supplied args/kwargs through.  Unknown function names
    return 400 with the list of valid names.
    """
    from mox.infrastructure.tasks import (
        TASK_REGISTRY,
        TaskPriority,
        get_registered_task_names,
        get_task_queue,
    )

    if request.func not in TASK_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unknown_task_function",
                "requested": request.func,
                "registered": get_registered_task_names(),
            },
        )

    target = TASK_REGISTRY[request.func]
    # Build a wrapper that actually invokes the registered callable
    # with the caller's args/kwargs, then submit that wrapper.
    async def runner() -> Dict[str, Any]:
        return await target(*request.args, **request.kwargs)

    try:
        task_queue = get_task_queue()
        priority = TaskPriority(request.priority)
        task_id = task_queue.submit(
            name=request.name,
            func=runner,
            priority=priority,
        )

        return {
            "task_id": task_id,
            "status": "submitted",
            "func": request.func,
            "priority": priority.name,
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
        from mox.infrastructure.tasks import get_task_queue

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


@router.get("/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """获取任务状态"""
    try:
        from mox.infrastructure.tasks import get_task_queue

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