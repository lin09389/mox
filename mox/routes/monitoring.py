"""监控相关路由"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends

from mox.infrastructure.auth import get_current_active_user, User
from mox.infrastructure.database import get_database
from mox.infrastructure.logging import get_logger

logger = get_logger("monitoring")

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


# ============ 路由端点 ============


@router.get("/dashboard")
async def get_monitoring_dashboard(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """获取监控面板数据"""
    try:
        from mox.infrastructure.monitoring import MonitoringDashboard

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
        from mox.infrastructure.monitoring import AnomalyDetector

        detector = AnomalyDetector()
        return detector.get_anomalies(limit=20)
    except Exception as e:
        logger.error(f"Failed to get anomalies: {e}")
        return []


@router.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """获取安全统计 — backed by real database counts."""
    try:
        db = get_database()
        total_attacks = await db.count_attack_records()
        total_defenses = await db.count_defense_records()

        # Pull a snapshot of recent records to compute success/block rates.
        recent_attacks = await db.get_attack_records(limit=500)
        recent_defenses = await db.get_defense_records(limit=500)

        if recent_attacks:
            attack_success_rate = sum(
                1 for r in recent_attacks if r.result == "success"
            ) / len(recent_attacks)
        else:
            attack_success_rate = 0.0

        if recent_defenses:
            defense_success_rate = sum(
                1 for r in recent_defenses if r.is_malicious
            ) / len(recent_defenses)
        else:
            defense_success_rate = 0.0

        return {
            "totalRequests": total_attacks,
            "blockedRequests": sum(
                1 for r in recent_defenses if r.is_malicious
            ),
            "attackSuccessRate": round(attack_success_rate, 4),
            "defenseSuccessRate": round(defense_success_rate, 4),
            "total_attacks": total_attacks,
            "total_defenses": total_defenses,
        }
    except Exception as e:
        logger.error(f"Failed to compute monitoring stats: {e}")
        # Fail-soft with explicit zero values — never return hardcoded
        # fake numbers (that was the previous broken behavior).
        return {
            "totalRequests": 0,
            "blockedRequests": 0,
            "attackSuccessRate": 0,
            "defenseSuccessRate": 0,
            "total_attacks": 0,
            "total_defenses": 0,
            "error": str(e),
        }


@router.get("/attacks/recent")
async def get_recent_attacks(
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """获取最近攻击 — backed by real database records."""
    try:
        db = get_database()
        records = await db.get_attack_records(limit=limit)
        return [
            {
                "id": r.id,
                "type": r.attack_type,
                "prompt": r.original_prompt,
                "adversarial_prompt": r.adversarial_prompt,
                "success": r.result == "success",
                "result": r.result,
                "success_score": r.success_score,
                "iterations": r.iterations,
                "model_name": r.model_name,
                "timestamp": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]
    except Exception as e:
        logger.error(f"Failed to get recent attacks: {e}")
        return []
