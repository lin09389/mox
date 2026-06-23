"""自动化红蓝对抗 API 路由 (SSE 实时流)"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from mox.auto_redteam.agent import RedTeamAgent
from mox.core.task_store import get_task_store

router = APIRouter(tags=["Auto-RedTeam"])


async def _persist_auto_redteam_report(agent: RedTeamAgent) -> Optional[int]:
    """Save completed auto-redteam run as a governance report."""
    try:
        from mox.core.database import get_extended_database

        state = agent.state
        steps = max(state.current_step, 1)
        vuln_count = len(state.vulnerabilities)
        attack_rate = round(min(1.0, vuln_count / steps), 4)
        defense_rate = round(1 - attack_rate, 4)
        payload = state.model_dump()

        report_id = await get_extended_database().save_report(
            {
                "report_name": f"自动红队报告 ({state.task_id})",
                "report_type": "auto_redteam",
                "model_name": state.target_model,
                "format": "json",
                "content": json.dumps(payload, ensure_ascii=False, default=str),
                "summary": {
                    "attack_success_rate": attack_rate,
                    "defense_success_rate": defense_rate,
                    "task_id": state.task_id,
                    "vulnerabilities_found": vuln_count,
                    "steps_executed": state.current_step,
                },
                "created_by": "auto_redteam",
            }
        )
        try:
            from mox.core.audit import get_audit_logger

            await get_audit_logger().log(
                action="report_create",
                resource=f"report:{report_id}",
                context=get_audit_logger().create_context(
                    endpoint="/api/v1/auto-redteam/start",
                    method="POST",
                ),
                request_body={
                    "task_id": state.task_id,
                    "report_id": report_id,
                    "report_type": "auto_redteam",
                    "model": state.target_model,
                },
                response_status=200,
            )
        except Exception:
            pass
        return report_id
    except Exception:
        return None


active_tasks: Dict[str, RedTeamAgent] = {}
_background_tasks: Dict[str, asyncio.Task] = {}


class StartAutoRedTeamRequest(BaseModel):
    target_model: str
    commander_model: Optional[str] = None
    max_steps: int = Field(default=10, ge=1, le=50)
    success_threshold: float = Field(default=0.6, ge=0.0, le=1.0)


@router.post("/start")
async def start_auto_redteam(request: StartAutoRedTeamRequest) -> Dict[str, Any]:
    """启动自动化红队任务（后台立即执行）"""
    task_id = f"art-{uuid.uuid4().hex[:8]}"

    agent = RedTeamAgent(
        target_model_name=request.target_model,
        task_id=task_id,
        max_steps=request.max_steps,
        commander_model_name=request.commander_model,
        success_threshold=request.success_threshold,
    )

    active_tasks[task_id] = agent
    get_task_store().set(
        task_id,
        {
            "id": task_id,
            "source": "auto_redteam",
            "status": "running",
            "target_model": request.target_model,
            "max_steps": request.max_steps,
        },
    )

    async def _run_and_finalize():
        report_id: Optional[int] = None
        try:
            async for state in agent.run():
                get_task_store().update(
                    task_id,
                    status=state.get("status", "running"),
                    vulnerabilities_count=len(state.get("vulnerabilities", [])),
                )
        except asyncio.CancelledError:
            if agent.state.status == "running":
                agent.state.status = "cancelled"
            raise
        except Exception as exc:
            agent.state.status = "error"
            agent.state.error_message = str(exc)
            get_task_store().update(task_id, status="error", error=str(exc))
        finally:
            report_id = await _persist_auto_redteam_report(agent)
            if report_id is not None:
                agent.state.report_id = report_id
            get_task_store().update(
                task_id,
                status=agent.state.status,
                report_id=report_id,
                vulnerabilities_count=len(agent.state.vulnerabilities),
                target_model=agent.state.target_model,
            )
            active_tasks.pop(task_id, None)
            _background_tasks.pop(task_id, None)

    _background_tasks[task_id] = asyncio.create_task(_run_and_finalize())

    return {
        "task_id": task_id,
        "message": "Auto-RedTeam task started.",
        "target_model": request.target_model,
    }


@router.get("/{task_id}/stream")
async def stream_task_progress(task_id: str):
    """通过 SSE 实时流式返回 Agent 状态"""
    if task_id not in active_tasks:
        stored = get_task_store().get(task_id)
        if stored:
            return StreamingResponse(
                iter([f"data: {json.dumps(stored, ensure_ascii=False)}\n\n"]),
                media_type="text/event-stream",
            )
        raise HTTPException(status_code=404, detail="Task not found or already completed.")

    agent = active_tasks[task_id]
    last_index = 0

    async def event_generator():
        nonlocal last_index
        while task_id in active_tasks:
            logs = agent.state.logs
            if len(logs) > last_index or agent.state.status != "running":
                state_dict = agent.state.model_dump()
                yield f"data: {json.dumps(state_dict, ensure_ascii=False)}\n\n"
                last_index = len(logs)
                if agent.state.status not in ("running",):
                    break
            await asyncio.sleep(0.5)

        if task_id in active_tasks:
            yield f"data: {json.dumps(agent.state.model_dump(), ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态（轮询备用）"""
    if task_id in active_tasks:
        return active_tasks[task_id].state.model_dump()
    stored = get_task_store().get(task_id)
    if stored:
        return stored
    raise HTTPException(status_code=404, detail="Task not found")


@router.delete("/{task_id}")
async def stop_task(task_id: str):
    """停止一个正在运行的任务"""
    if task_id in active_tasks:
        agent = active_tasks[task_id]
        agent.state.status = "failed"
        agent.state.error_message = "Task cancelled by user."
        bg = _background_tasks.pop(task_id, None)
        if bg:
            bg.cancel()
        active_tasks.pop(task_id, None)
        get_task_store().update(task_id, status="cancelled")
        return {"status": "success", "message": "Task cancelled."}
    return {"status": "error", "message": "Task not found."}
