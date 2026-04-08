"""监控相关路由"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends

from mox.core.auth import get_current_active_user, User
from mox.core.logging import get_logger

logger = get_logger("monitoring")

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


# ============ 路由端点 ============


@router.get("/dashboard")
async def get_monitoring_dashboard(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """获取监控面板数据"""
    try:
        from mox.core.monitoring import MonitoringDashboard

        dashboard = MonitoringDashboard()
        return dashboard.get_dashboard_data()
    except Exception as e:
        logger.error(f"Failed to get monitoring dashboard data: {e}")
        return {
            "total_requests": 0,
            "blocked_requests": 0,
            "attack_success_rate": 0,
            "defense_success_rate": 0,
            "error": str(e),
        }


@router.get("/anomalies")
async def get_anomalies() -> List[Dict[str, Any]]:
    """获取异常列表"""
    try:
        from mox.core.monitoring import AnomalyDetector

        detector = AnomalyDetector()
        return detector.get_anomalies(limit=20)
    except Exception as e:
        logger.error(f"Failed to get anomalies: {e}")
        return []


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """获取安全统计"""
    return {
        "totalRequests": 1247,
        "blockedRequests": 89,
        "attackSuccessRate": 0.12,
        "defenseSuccessRate": 0.94,
    }


@router.get("/attacks/recent")
async def get_recent_attacks() -> List[Dict[str, Any]]:
    """获取最近攻击"""
    return [
        {"type": "prompt_injection", "prompt": "Ignore instructions", "success": False},
        {"type": "jailbreak", "prompt": "DAN mode", "success": True},
    ]
