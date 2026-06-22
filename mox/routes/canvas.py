"""Canvas API routes."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from mox.workflows.canvas_engine import engine

router = APIRouter(prefix="/canvas", tags=["Canvas"])


class CanvasDeployRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


@router.post("/deploy")
async def deploy_canvas(request: CanvasDeployRequest):
    """Deploy a DAG from the frontend canvas."""
    try:
        run_id = await engine.dispatch(request.model_dump())
        return {
            "status": "success",
            "message": "Canvas DAG deployed successfully",
            "run_id": run_id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/runs")
async def list_canvas_runs(limit: int = 20):
    """List recent canvas runs."""
    return {"runs": engine.list_runs(limit=limit)}


@router.get("/runs/{run_id}")
async def get_canvas_run(run_id: str):
    """Get canvas run status and results."""
    state = engine.get_run(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="Run not found")
    return state