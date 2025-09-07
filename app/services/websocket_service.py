from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class WebSocketService:
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection and add to active connections"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection from active connections"""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    # Remove broken connections
                    self.active_connections[user_id].remove(connection)
    
    async def broadcast_to_user(self, user_id: str, event_type: str, data: dict):
        """Broadcast specific event to user"""
        message = {
            "type": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.send_personal_message(message, user_id)
    
    async def send_task_update(self, user_id: str, task_data: dict, event_type: str):
        """Send task update to user"""
        await self.broadcast_to_user(user_id, f"task_{event_type}", task_data)
    
    async def send_status_update(self, user_id: str, message: str):
        """Send status update to user"""
        await self.broadcast_to_user(user_id, "status_update", {"message": message})


# Global WebSocket service instance
websocket_service = WebSocketService()
