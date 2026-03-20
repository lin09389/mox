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

    async def connect(self, websocket: WebSocket):
        if len(self.active_connections) >= self.MAX_CONNECTIONS:
            await websocket.close(code=1013, reason="Too many connections")
            return False
        await websocket.accept()
        self.active_connections.add(websocket)
        return True

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


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
                    await manager.send_personal_message(
                        {"type": "subscribed", "channel": channel}, websocket
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
    await manager.connect(websocket)
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

    await manager.broadcast({
        "type": message.type,
        "channel": message.channel,
        "data": message.data,
    })
    return {"success": True, "clients": len(manager.active_connections)}


@router.get("/api/ws/stats")
async def get_ws_stats():
    """获取WebSocket连接统计"""
    return {
        "active_connections": len(manager.active_connections),
    }