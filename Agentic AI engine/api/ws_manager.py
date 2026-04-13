import json
import logging
from typing import Dict, List, Set, Union

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages real-time WebSocket connections for MedAgent."""

    def __init__(self):
        # Maps user_id -> set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Global admin/doctor connections for site-wide broadcasting (audit/analytics)
        self.staff_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, user_id: str, role: str = "patient"):
        """Accept a new connection and categorize by role and user_id."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)

        if role in ["admin", "doctor"]:
            self.staff_connections.add(websocket)

        logger.info(f"WS Connected: User {user_id} ({role})")

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Clean up disconnected sockets."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        self.staff_connections.discard(websocket)
        logger.info(f"WS Disconnected: User {user_id}")

    async def send_personal_message(self, message: Union[str, Dict], user_id: str):
        """Send message to all open tabs for a specific user (e.g. Chat/Reminders)."""
        if user_id not in self.active_connections:
            return

        payload = message if isinstance(message, str) else json.dumps(message)
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.error(f"WS send fail to user {user_id}: {e}")

    async def broadcast_staff(self, message: Union[str, Dict]):
        """Broadcast message to all active staff members (e.g. Audit Logs/Analytics)."""
        payload = message if isinstance(message, str) else json.dumps(message)
        for connection in list(self.staff_connections):
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.error(f"WS broadcast staff fail: {e}")
                self.staff_connections.discard(connection)

    async def broadcast_all(self, message: Union[str, Dict]):
        """Broadcast to every single connected client."""
        payload = message if isinstance(message, str) else json.dumps(message)
        for user_sockets in self.active_connections.values():
            for connection in list(user_sockets):
                try:
                    await connection.send_text(payload)
                except Exception as e:
                    logger.error(f"WS broadcast all fail: {e}")


# Singleton instance
manager = ConnectionManager()
