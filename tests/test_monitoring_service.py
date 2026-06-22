"""监控统计服务测试"""

import pytest

from mox.core.monitoring_service import (
    get_attack_exposure_radar,
    get_hourly_trends,
    get_monitoring_visualization,
    get_recent_attacks,
    get_security_stats,
    get_threat_topology,
)


@pytest.mark.asyncio
async def test_get_security_stats_structure():
    stats = await get_security_stats()
    assert "totalRequests" in stats
    assert "blockedRequests" in stats
    assert "attackSuccessRate" in stats
    assert "defenseSuccessRate" in stats
    assert isinstance(stats["totalRequests"], int)


@pytest.mark.asyncio
async def test_get_recent_attacks_returns_list():
    attacks = await get_recent_attacks(limit=5)
    assert isinstance(attacks, list)


@pytest.mark.asyncio
async def test_get_hourly_trends_structure():
    trends = await get_hourly_trends(hours=24)
    assert "series" in trends
    assert isinstance(trends["series"], list)
    assert len(trends["series"]) == 25
    if trends["series"]:
        point = trends["series"][0]
        assert "time" in point
        assert "attack" in point
        assert "blocked" in point


@pytest.mark.asyncio
async def test_get_attack_exposure_radar_structure():
    radar = await get_attack_exposure_radar()
    assert "items" in radar
    assert isinstance(radar["items"], list)


@pytest.mark.asyncio
async def test_get_threat_topology_structure():
    topology = await get_threat_topology(limit=5)
    assert "nodes" in topology
    assert "links" in topology
    assert any(node["id"] == "core" for node in topology["nodes"])


@pytest.mark.asyncio
async def test_get_monitoring_visualization_bundle():
    payload = await get_monitoring_visualization()
    assert "stats" in payload
    assert "trends" in payload
    assert "radar" in payload
    assert "topology" in payload
    assert "timestamp" in payload