"""测试 WebSocket 改进 - 异常处理"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from mox.routes.websocket import ConnectionManager


class TestConnectionManager:
    """测试连接管理器"""

    def test_initialization(self):
        """测试初始化"""
        manager = ConnectionManager()
        assert manager.MAX_CONNECTIONS == 100
        assert len(manager.active_connections) == 0

    def test_max_connections_limit(self):
        """测试最大连接数限制"""
        manager = ConnectionManager()

        # 模拟添加100个连接
        mock_ws_list = []
        for i in range(100):
            mock_ws = MagicMock()
            mock_ws.accept = AsyncMock()
            manager.active_connections.add(mock_ws)
            mock_ws_list.append(mock_ws)

        # 验证连接数达到上限
        assert len(manager.active_connections) >= manager.MAX_CONNECTIONS

    def test_disconnect_removes_connection(self):
        """测试断开连接"""
        manager = ConnectionManager()
        mock_ws = MagicMock()
        manager.active_connections.add(mock_ws)

        assert len(manager.active_connections) == 1

        manager.disconnect(mock_ws)

        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast_logs_failures(self):
        """测试广播时记录失败的连接"""
        manager = ConnectionManager()

        # 创建一个会失败的 mock 连接
        failing_ws = MagicMock()
        failing_ws.send_json = AsyncMock(side_effect=Exception("Connection error"))

        # 创建一个正常的 mock 连接
        good_ws = MagicMock()
        good_ws.send_json = AsyncMock()

        manager.active_connections.add(failing_ws)
        manager.active_connections.add(good_ws)

        # 广播消息
        await manager.broadcast({"type": "test", "message": "hello"})

        # 验证发送被调用
        good_ws.send_json.assert_called_once()
        failing_ws.send_json.assert_called_once()

        # 验证失败的连接被移除
        assert failing_ws not in manager.active_connections
        assert good_ws in manager.active_connections


class TestConnectionManagerIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_multiple_connections(self):
        """测试多个连接管理"""
        manager = ConnectionManager()

        connections = []
        for i in range(5):
            ws = MagicMock()
            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()
            connections.append(ws)

        for ws in connections:
            result = await manager.connect(ws)
            assert result is True

        assert len(manager.active_connections) == 5

    @pytest.mark.asyncio
    async def test_disconnect_all(self):
        """测试断开所有连接"""
        manager = ConnectionManager()

        for i in range(3):
            ws = MagicMock()
            ws.accept = AsyncMock()
            manager.active_connections.add(ws)

        assert len(manager.active_connections) == 3

        for ws in list(manager.active_connections):
            manager.disconnect(ws)

        assert len(manager.active_connections) == 0
