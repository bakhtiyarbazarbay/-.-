"""
WebSocket endpoint для real-time доставки сообщений.
"""
import json
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Менеджер WebSocket-подключений по чатам."""

    def __init__(self):
        # chat_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_id: int):
        """Подключить пользователя к чату."""
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = set()
        self.active_connections[chat_id].add(websocket)

    def disconnect(self, websocket: WebSocket, chat_id: int):
        """Отключить пользователя от чата."""
        if chat_id in self.active_connections:
            self.active_connections[chat_id].discard(websocket)
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]

    async def broadcast(self, chat_id: int, message: dict):
        """Отправить сообщение всем участникам чата."""
        if chat_id in self.active_connections:
            data = json.dumps(message, default=str, ensure_ascii=False)
            dead = []
            for connection in self.active_connections[chat_id]:
                try:
                    await connection.send_text(data)
                except Exception:
                    dead.append(connection)
            for conn in dead:
                self.active_connections[chat_id].discard(conn)


manager = ConnectionManager()


@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int):
    """
    WebSocket для real-time сообщений в чате.
    
    Клиент подключается к /ws/{chat_id} и получает
    все новые сообщения в JSON-формате.
    """
    await manager.connect(websocket, chat_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            # Рассылаем всем участникам чата
            await manager.broadcast(chat_id, {
                "type": "message",
                "chat_id": chat_id,
                "content": message.get("content", ""),
                "sender_id": message.get("sender_id"),
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket, chat_id)
    except Exception:
        manager.disconnect(websocket, chat_id)
