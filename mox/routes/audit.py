"""审计日志 API 路由"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from mox.core.audit import get_audit_logger
from mox.core.auth import User, get_current_active_user

router = APIRouter(prefix="/audit", tags=["Audit"])

_ACTION_LABELS = {
    "attack_run": "攻击测试",
    "defense_detect": "防御检测",
    "benchmark_run": "基准评测",
    "model_list": "模型查询",
    "login": "用户登录",
    "logout": "用户登出",
    "register": "用户注册",
    "report_query": "报告查询",
    "report_download": "报告下载",
    "report_delete": "报告删除",
    "report_create": "报告创建",
    "dataset_query": "数据集查询",
    "dataset_upload": "数据集上传",
    "dataset_delete": "数据集删除",
    "template_query": "模板查询",
    "template_create": "模板创建",
    "template_update": "模板更新",
    "template_delete": "模板删除",
    "audit_query": "审计查询",
}


@router.get("/logs")
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    action: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, List[Dict[str, Any]]]:
    """获取审计日志列表"""
    audit_logger = get_audit_logger()
    logs = await audit_logger.get_logs(limit=limit, action=action)

    enriched = []
    for log in logs:
        entry = dict(log)
        entry["action_label"] = _ACTION_LABELS.get(log.get("action", ""), log.get("action", ""))
        entry["resource"] = log.get("endpoint") or log.get("resource", "")
        enriched.append(entry)

    return {"logs": enriched}
