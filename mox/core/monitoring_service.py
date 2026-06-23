"""监控统计服务 - 从数据库聚合真实指标"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import case, func, select

from mox.core.database import AttackRecord, DefenseRecord, get_database
from mox.core.logging import get_logger

logger = get_logger("monitoring")

_ATTACK_TYPE_LABELS = {
    "prompt_injection": "提示注入",
    "jailbreak": "越狱探测",
    "gcg": "GCG 对抗",
    "tap": "TAP 多轮",
    "rag": "RAG 攻击",
    "agent": "Agent 滥用",
    "multimodal": "多模态绕过",
    "novel": "新型攻击",
}

_DEFAULT_DEFENSE_NODES = [
    ("def_waf", "WAF", "defense"),
    ("def_prompt", "Prompt Filter", "defense"),
    ("def_jailbreak", "Jailbreak Detector", "defense"),
    ("def_rate", "Rate Limiter", "defense"),
    ("def_dlp", "DLP", "defense"),
]


async def get_security_stats() -> Dict[str, Any]:
    """获取安全总览统计（供前端 Dashboard 使用）"""
    db = get_database()
    total_attacks = await db.count_attack_records()
    total_defenses = await db.count_defense_records()

    successful_attacks = 0
    blocked_requests = 0

    try:
        async with db.get_session() as session:
            success_stmt = select(func.count(AttackRecord.id)).where(
                AttackRecord.result == "success"
            )
            success_result = await session.execute(success_stmt)
            successful_attacks = success_result.scalar() or 0

            blocked_stmt = select(func.count(DefenseRecord.id)).where(
                DefenseRecord.is_malicious.is_(True)
            )
            blocked_result = await session.execute(blocked_stmt)
            blocked_requests = blocked_result.scalar() or 0
    except Exception as exc:
        logger.warning(f"Failed to aggregate security stats: {exc}")

    total_requests = total_attacks + total_defenses
    attack_success_rate = successful_attacks / total_attacks if total_attacks else 0.0
    defense_success_rate = blocked_requests / total_defenses if total_defenses else 0.0

    return {
        "totalRequests": total_requests,
        "blockedRequests": blocked_requests,
        "attackSuccessRate": round(attack_success_rate, 4),
        "defenseSuccessRate": round(defense_success_rate, 4),
        "total_attacks": total_attacks,
        "total_defenses": total_defenses,
        "successful_attacks": successful_attacks,
    }


async def get_recent_attacks(limit: int = 10) -> List[Dict[str, Any]]:
    """获取最近攻击记录"""
    db = get_database()
    records = await db.get_attack_records(limit=limit)
    return [
        {
            "id": record.id,
            "type": record.attack_type,
            "prompt": (record.original_prompt or "")[:200],
            "success": record.result == "success" or record.success_score >= 0.6,
            "success_score": record.success_score,
            "model": record.model_name,
            "timestamp": record.created_at.isoformat() if record.created_at else None,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
        for record in records
    ]


def _hour_bucket(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)


def _format_hour_label(hours_ago: int) -> str:
    if hours_ago <= 0:
        return "现在"
    return f"-{hours_ago}h"


async def get_hourly_trends(hours: int = 24) -> Dict[str, Any]:
    """按小时聚合攻击与拦截趋势"""
    db = get_database()
    now = datetime.now()
    start = now - timedelta(hours=hours)
    bucket_keys: List[datetime] = []
    for offset in range(hours, -1, -1):
        bucket_keys.append(_hour_bucket(now - timedelta(hours=offset)))

    counts = {key: {"attack": 0, "blocked": 0} for key in bucket_keys}

    try:
        async with db.get_session() as session:
            attack_stmt = select(AttackRecord).where(AttackRecord.created_at >= start)
            attack_result = await session.execute(attack_stmt)
            for record in attack_result.scalars().all():
                if not record.created_at:
                    continue
                bucket = _hour_bucket(record.created_at)
                if bucket in counts:
                    counts[bucket]["attack"] += 1

            defense_stmt = select(DefenseRecord).where(
                DefenseRecord.created_at >= start,
                DefenseRecord.is_malicious.is_(True),
            )
            defense_result = await session.execute(defense_stmt)
            for record in defense_result.scalars().all():
                if not record.created_at:
                    continue
                bucket = _hour_bucket(record.created_at)
                if bucket in counts:
                    counts[bucket]["blocked"] += 1
    except Exception as exc:
        logger.warning(f"Failed to aggregate hourly trends: {exc}")

    series = []
    for index, bucket in enumerate(bucket_keys):
        hours_ago = len(bucket_keys) - 1 - index
        entry = counts[bucket]
        series.append(
            {
                "time": _format_hour_label(hours_ago),
                "attack": entry["attack"],
                "blocked": entry["blocked"],
            }
        )

    return {"series": series}


async def get_attack_exposure_radar() -> Dict[str, Any]:
    """按攻击类型聚合暴露面（雷达图）"""
    db = get_database()
    items: List[Dict[str, Any]] = []

    try:
        async with db.get_session() as session:
            stmt = (
                select(
                    AttackRecord.attack_type,
                    func.count(AttackRecord.id),
                    func.avg(AttackRecord.success_score),
                    func.sum(
                        case(
                            (AttackRecord.result == "success", 1),
                            else_=0,
                        )
                    ),
                )
                .group_by(AttackRecord.attack_type)
                .order_by(func.count(AttackRecord.id).desc())
            )
            result = await session.execute(stmt)
            for attack_type, count, avg_score, success_count in result.all():
                count = int(count or 0)
                if count == 0:
                    continue
                avg_score = float(avg_score or 0.0)
                success_count = int(success_count or 0)
                success_rate = success_count / count
                risk_value = round(min(100.0, max(0.0, success_rate * 70 + avg_score * 30)), 1)
                label = _ATTACK_TYPE_LABELS.get(attack_type, attack_type.replace("_", " ").title())
                items.append(
                    {
                        "subject": label,
                        "value": risk_value,
                        "count": count,
                        "attack_type": attack_type,
                    }
                )
    except Exception as exc:
        logger.warning(f"Failed to aggregate attack exposure radar: {exc}")

    return {"items": items}


async def get_threat_topology(limit: int = 40) -> Dict[str, Any]:
    """基于最近攻击记录生成威胁拓扑图数据"""
    recent = await get_recent_attacks(limit=limit)
    nodes: List[Dict[str, Any]] = [
        {"id": "core", "group": "core", "val": 30, "name": "Core LLM Engine"},
    ]
    links: List[Dict[str, Any]] = []

    for node_id, name, group in _DEFAULT_DEFENSE_NODES:
        nodes.append({"id": node_id, "group": group, "val": 15, "name": name})
        links.append({"source": node_id, "target": "core", "blocked": False})

    defense_ids = [node_id for node_id, _, _ in _DEFAULT_DEFENSE_NODES]

    for index, attack in enumerate(recent):
        node_id = f"att_{attack.get('id', index)}"
        success = bool(attack.get("success"))
        attack_type = attack.get("type") or "unknown"
        label = _ATTACK_TYPE_LABELS.get(attack_type, attack_type)
        nodes.append(
            {
                "id": node_id,
                "group": "attack_blocked" if not success else "attack_active",
                "val": max(3, int((attack.get("success_score") or 0.3) * 10)),
                "name": f"{label}",
            }
        )
        if success:
            target = "core"
            blocked = False
        else:
            target = defense_ids[index % len(defense_ids)]
            blocked = True
        links.append({"source": node_id, "target": target, "blocked": blocked})

    return {"nodes": nodes, "links": links}


async def get_monitoring_visualization(hours: int = 24) -> Dict[str, Any]:
    """Dashboard 可视化一次性数据包"""
    stats = await get_security_stats()
    trends = await get_hourly_trends(hours=hours)
    radar = await get_attack_exposure_radar()
    topology = await get_threat_topology()
    return {
        "stats": stats,
        "trends": trends,
        "radar": radar,
        "topology": topology,
        "timestamp": datetime.now().isoformat(),
    }


async def get_stats_overview() -> Dict[str, Any]:
    """获取完整统计概览（含最近攻击列表）"""
    stats = await get_security_stats()
    recent = await get_recent_attacks(limit=10)
    return {
        "total_attacks": stats["total_attacks"],
        "successful_attacks": stats["successful_attacks"],
        "total_defenses": stats["total_defenses"],
        "blocked_attacks": stats["blockedRequests"],
        "recent_attacks": recent,
    }
