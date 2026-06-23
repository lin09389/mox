"""用户自定义攻击模板 CRUD — 基于 AttackTemplateRecord。"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from mox.core.auth import User
from mox.core.database import AttackTemplateRecord, get_extended_database
from mox.routes.auth_helpers import require_optional_access

router = APIRouter(prefix="/user-templates", tags=["User Templates"])

require_template_access = require_optional_access


def _format_timestamp(value: Optional[datetime]) -> str:
    if not value:
        return ""
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _template_to_dict(record: AttackTemplateRecord) -> Dict[str, Any]:
    return {
        "id": record.id,
        "name": record.name,
        "attack_type": record.attack_type,
        "category": record.category or "",
        "content": record.content,
        "description": record.description or "",
        "is_favorite": bool(record.is_favorite),
        "usage_count": record.usage_count or 0,
        "created_at": _format_timestamp(record.created_at),
        "updated_at": _format_timestamp(record.updated_at),
    }


class TemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    attack_type: str = Field(..., min_length=1, max_length=50)
    category: str = Field(default="", max_length=50)
    content: str = Field(..., min_length=1)
    description: str = Field(default="")


class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    attack_type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    category: Optional[str] = Field(default=None, max_length=50)
    content: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = Field(default=None)


@router.get("")
async def list_user_templates(
    limit: int = 100,
    favorites_only: bool = False,
    current_user: User = Depends(require_template_access),
) -> Dict[str, List[Dict[str, Any]]]:
    db = get_extended_database()
    records = await db.get_templates(
        limit=min(limit, 200),
        is_favorite=True if favorites_only else None,
    )
    return {"templates": [_template_to_dict(record) for record in records]}


@router.post("")
async def create_user_template(
    request: TemplateCreateRequest,
    current_user: User = Depends(require_template_access),
) -> Dict[str, Any]:
    db = get_extended_database()
    template_id = await db.save_template(
        {
            "name": request.name.strip(),
            "attack_type": request.attack_type.strip(),
            "category": request.category.strip() or None,
            "content": request.content,
            "description": request.description.strip() or None,
            "created_by": current_user.username,
        }
    )
    record = await db.get_template(template_id)
    if not record:
        raise HTTPException(status_code=500, detail="Failed to create template")
    return {"template": _template_to_dict(record)}


@router.put("/{template_id}")
async def update_user_template(
    template_id: int,
    request: TemplateUpdateRequest,
    current_user: User = Depends(require_template_access),
) -> Dict[str, Any]:
    db = get_extended_database()
    existing = await db.get_template(template_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

    payload = request.model_dump(exclude_unset=True)
    if not payload:
        return {"template": _template_to_dict(existing)}

    record = await db.update_template(template_id, payload)
    if not record:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")
    return {"template": _template_to_dict(record)}


@router.delete("/{template_id}")
async def delete_user_template(
    template_id: int,
    current_user: User = Depends(require_template_access),
) -> Dict[str, Any]:
    db = get_extended_database()
    existing = await db.get_template(template_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

    deleted = await db.delete_template(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

    try:
        from mox.core.audit import get_audit_logger

        await get_audit_logger().log(
            action="template_delete",
            resource=f"template:{template_id}",
            context=get_audit_logger().create_context(
                user_id=current_user.username,
                username=current_user.username,
                endpoint=f"/api/v1/user-templates/{template_id}",
                method="DELETE",
            ),
            request_body={"template_id": template_id, "name": existing.name},
            response_status=200,
        )
    except Exception:
        pass

    return {"deleted": True, "id": template_id}


@router.post("/{template_id}/favorite")
async def toggle_user_template_favorite(
    template_id: int,
    current_user: User = Depends(require_template_access),
) -> Dict[str, Any]:
    db = get_extended_database()
    existing = await db.get_template(template_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

    is_favorite = await db.toggle_template_favorite(template_id)
    record = await db.get_template(template_id)
    return {
        "id": template_id,
        "is_favorite": is_favorite,
        "template": _template_to_dict(record) if record else None,
    }
