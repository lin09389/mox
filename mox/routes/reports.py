"""评估报告 API — 基于统一 Database 的 ReportRecord。"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

from mox.core.auth import User
from mox.core.database import ReportRecord, get_extended_database
from mox.routes.auth_helpers import require_optional_access

router = APIRouter(prefix="/reports", tags=["Reports"])

require_report_access = require_optional_access


def _format_timestamp(value: Optional[datetime]) -> str:
    if not value:
        return ""
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _report_to_dict(record: ReportRecord) -> Dict[str, Any]:
    summary = record.summary if isinstance(record.summary, dict) else {}
    attack_rate = float(summary.get("attack_success_rate", 0) or 0)
    defense_rate = float(summary.get("defense_success_rate", max(0.0, 1.0 - attack_rate)) or 0)
    return {
        "id": record.id,
        "report_name": record.report_name,
        "report_type": record.report_type or "evaluation",
        "model_name": record.model_name or "unknown",
        "attack_success_rate": attack_rate,
        "defense_success_rate": defense_rate,
        "created_at": _format_timestamp(record.created_at),
        "format": record.format or "json",
        "summary": summary,
    }


@router.get("")
async def list_reports(
    limit: int = 50,
    report_type: Optional[str] = None,
    current_user: User = Depends(require_report_access),
) -> Dict[str, List[Dict[str, Any]]]:
    db = get_extended_database()
    records = await db.get_reports(limit=min(limit, 200), report_type=report_type)
    return {"reports": [_report_to_dict(record) for record in records]}


@router.get("/{report_id}")
async def get_report(
    report_id: int,
    current_user: User = Depends(require_report_access),
) -> Dict[str, Any]:
    db = get_extended_database()
    record = await db.get_report(report_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")
    payload = _report_to_dict(record)
    payload["content"] = record.content
    return payload


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    current_user: User = Depends(require_report_access),
):
    db = get_extended_database()
    record = await db.get_report(report_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")

    content = record.content or "{}"
    fmt = (record.format or "json").lower()
    filename = f"{record.report_name or 'report'}.{fmt}".replace(" ", "_")

    if fmt == "json":
        try:
            parsed = json.loads(content)
            return JSONResponse(
                content=parsed,
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except json.JSONDecodeError:
            pass

    media = "text/html" if fmt == "html" else "text/markdown" if fmt == "md" else "text/plain"
    return PlainTextResponse(
        content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    current_user: User = Depends(require_report_access),
) -> Dict[str, Any]:
    db = get_extended_database()
    record = await db.get_report(report_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")

    deleted = await db.delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")

    try:
        from mox.core.audit import get_audit_logger

        await get_audit_logger().log(
            action="report_delete",
            resource=f"report:{report_id}",
            context=get_audit_logger().create_context(
                user_id=current_user.username,
                username=current_user.username,
                endpoint=f"/api/v1/reports/{report_id}",
                method="DELETE",
            ),
            request_body={
                "report_id": report_id,
                "report_name": record.report_name,
                "report_type": record.report_type,
            },
            response_status=200,
        )
    except Exception:
        pass

    return {"deleted": True, "id": report_id}
