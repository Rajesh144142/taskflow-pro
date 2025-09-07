from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.websocket_service import websocket_service
from app.utils.security import verify_token
import json

router = APIRouter()


@router.websocket("/ws/tasks/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time task updates"""
    await websocket_service.connect(websocket, user_id)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message.get("type") == "subscribe":
                await websocket_service.send_status_update(
                    user_id, 
                    f"Subscribed to updates for user {user_id}"
                )
            elif message.get("type") == "unsubscribe":
                await websocket_service.send_status_update(
                    user_id, 
                    f"Unsubscribed from updates for user {user_id}"
                )
            else:
                await websocket_service.send_status_update(
                    user_id, 
                    f"Received message: {message.get('type', 'unknown')}"
                )
                
    except WebSocketDisconnect:
        websocket_service.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_service.disconnect(websocket, user_id)
