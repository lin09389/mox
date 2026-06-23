"""监控相关路由"""

from typing import Dict, Any, List

from fastapi import APIRouter, Depends

from mox.core.auth import get_current_active_user, User
from mox.core.monitoring_service import (
    get_monitoring_visualization,
    get_recent_attacks,
    get_security_stats,
)

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/dashboard")
async def get_monitoring_dashboard(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """获取监控面板数据"""
    try:
        from mox.core.monitoring import MonitoringDashboard

        dashboard = MonitoringDashboard()
        data = dashboard.get_dashboard_data()
        stats = await get_security_stats()
        data.update(stats)
        return data
    except Exception:
        return await get_security_stats()


@router.get("/anomalies")
async def get_anomalies() -> List[Dict[str, Any]]:
    """获取异常列表"""
    try:
        from mox.core.monitoring import AnomalyDetector

        detector = AnomalyDetector()
        return detector.get_anomalies(limit=20)
    except Exception:
        return []


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """获取安全统计（从数据库聚合）"""
    return await get_security_stats()


@router.get("/visualization")
async def get_visualization() -> Dict[str, Any]:
    """获取 Dashboard 可视化数据（时序、雷达、拓扑）"""
    return await get_monitoring_visualization()


@router.get("/attacks/recent")
async def get_recent_attacks_endpoint() -> List[Dict[str, Any]]:
    """获取最近攻击记录"""
    return await get_recent_attacks(limit=10)
