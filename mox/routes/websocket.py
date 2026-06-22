"""WebSocket 相关路由"""

import json
from typing import Dict, Any, Optional, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel

from mox.core.auth import User, get_current_active_user

router = APIRouter(tags=["WebSocket"])


# ============ 连接管理器 ============


class ConnectionManager:
    """WebSocket连接管理器"""

    MAX_CONNECTIONS: int = 100  # Maximum concurrent connections to prevent DoS

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.channel_subscriptions: Dict[str, Set[WebSocket]] = {}
        self.task_listeners: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        if len(self.active_connections) >= self.MAX_CONNECTIONS:
            await websocket.close(code=1013, reason="Too many connections")
            return False
        await websocket.accept()
        self.active_connections.add(websocket)
        return True

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        for channel in self.channel_subscriptions:
            self.channel_subscriptions[channel].discard(websocket)
        for task_id in self.task_listeners:
            self.task_listeners[task_id].discard(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """广播消息到所有活跃连接"""
        from mox.core.logging import get_logger

        logger = get_logger("websocket")

        failed_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket connection: {e}")
                failed_connections.append(connection)

        for conn in failed_connections:
            self.active_connections.discard(conn)

    async def broadcast_to_channel(self, channel: str, message: dict):
        """广播到指定频道"""
        if channel not in self.channel_subscriptions:
            return
        for websocket in list(self.channel_subscriptions[channel]):
            try:
                await websocket.send_json(message)
            except Exception:
                self.channel_subscriptions[channel].discard(websocket)

    async def notify_task_update(self, task_id: str, data: dict):
        """通知任务更新"""
        if task_id in self.task_listeners:
            for websocket in list(self.task_listeners[task_id]):
                try:
                    await websocket.send_json({"type": "task_update", "task_id": task_id, **data})
                except Exception:
                    self.task_listeners[task_id].discard(websocket)


manager = ConnectionManager()


# ============ 请求模型 ============


class WebSocketMessage(BaseModel):
    type: str
    channel: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# ============ 路由端点 ============


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时通信端点"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "ping":
                    await manager.send_personal_message({"type": "pong"}, websocket)
                elif msg_type == "subscribe":
                    channel = message.get("channel")
                    if channel not in manager.channel_subscriptions:
                        manager.channel_subscriptions[channel] = set()
                    manager.channel_subscriptions[channel].add(websocket)
                    await manager.send_personal_message(
                        {"type": "subscribed", "channel": channel}, websocket
                    )
                elif msg_type == "unsubscribe":
                    channel = message.get("channel")
                    if channel in manager.channel_subscriptions:
                        manager.channel_subscriptions[channel].discard(websocket)
                    await manager.send_personal_message(
                        {"type": "unsubscribed", "channel": channel}, websocket
                    )
                elif msg_type == "listen_task":
                    task_id = message.get("task_id")
                    if task_id not in manager.task_listeners:
                        manager.task_listeners[task_id] = set()
                    manager.task_listeners[task_id].add(websocket)
                    await manager.send_personal_message(
                        {"type": "listening", "task_id": task_id}, websocket
                    )
                else:
                    await manager.send_personal_message(
                        {"type": "echo", "data": message}, websocket
                    )
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON"}, websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/attack/{task_id}")
async def websocket_attack(websocket: WebSocket, task_id: str):
    """WebSocket攻击任务跟踪"""
    connected = await manager.connect(websocket)
    if not connected:
        return

    if task_id not in manager.task_listeners:
        manager.task_listeners[task_id] = set()
    manager.task_listeners[task_id].add(websocket)

    try:
        await manager.send_personal_message(
            {"type": "connected", "task_id": task_id, "status": "listening"}, websocket
        )

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "status_check":
                await manager.send_personal_message(
                    {"type": "status", "task_id": task_id, "status": "processing"}, websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.post("/api/ws/broadcast")
async def broadcast_message(
    message: WebSocketMessage,
    current_user: User = Depends(get_current_active_user),
):
    """广播消息到所有WebSocket客户端"""
    if "admin" not in (current_user.scopes or []):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Admin scope required")

    await manager.broadcast(
        {
            "type": message.type,
            "channel": message.channel,
            "data": message.data,
        }
    )
    return {"success": True, "clients": len(manager.active_connections)}


@router.get("/api/ws/stats")
async def get_ws_stats():
    """获取WebSocket连接统计"""
    return {
        "active_connections": len(manager.active_connections),
    }
