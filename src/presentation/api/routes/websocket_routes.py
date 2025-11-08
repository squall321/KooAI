"""
WebSocket API Routes

Real-time updates for file uploads, processing status, and notifications.
"""

import json
import asyncio
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

router = APIRouter()


class ConnectionManager:
    """
    WebSocket connection manager.

    Manages multiple WebSocket connections and broadcasts messages.
    """

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        """
        Accept new WebSocket connection.

        Args:
            client_id: Unique client identifier
            websocket: WebSocket instance
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        """
        Remove WebSocket connection.

        Args:
            client_id: Client identifier
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, client_id: str):
        """
        Send message to specific client.

        Args:
            message: Message dict
            client_id: Target client ID
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """
        Broadcast message to all connected clients.

        Args:
            message: Message dict
        """
        for connection in self.active_connections.values():
            await connection.send_json(message)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    ## WebSocket Endpoint

    Real-time bidirectional communication channel.

    ### Use Cases
    - File upload progress
    - Processing status updates
    - Real-time notifications
    - Task completion alerts

    ### Connection
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/client123');

    ws.onopen = () => {
        console.log('Connected');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received:', data);
    };

    ws.send(JSON.stringify({
        type: 'subscribe',
        topics: ['uploads', 'processing']
    }));
    ```

    ### Message Types
    - **upload_progress**: File upload progress
    - **processing_status**: Processing status update
    - **notification**: General notification
    - **error**: Error message

    ### Example Messages

    Upload Progress:
    ```json
    {
        "type": "upload_progress",
        "data": {
            "filename": "simulation.vtk",
            "progress": 45.5,
            "uploaded_bytes": 1048576,
            "total_bytes": 2304512
        }
    }
    ```

    Processing Status:
    ```json
    {
        "type": "processing_status",
        "data": {
            "task_id": "task_123",
            "status": "processing",
            "progress": 75.0,
            "message": "Analyzing field: temperature"
        }
    }
    ```
    """
    await manager.connect(client_id, websocket)

    try:
        # Send welcome message
        await manager.send_personal_message(
            {
                "type": "connection",
                "message": f"Connected as {client_id}",
                "timestamp": datetime.utcnow().isoformat(),
            },
            client_id,
        )

        # Listen for messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            if message.get("type") == "subscribe":
                topics = message.get("topics", [])
                await manager.send_personal_message(
                    {
                        "type": "subscribed",
                        "topics": topics,
                        "message": f"Subscribed to {len(topics)} topics",
                    },
                    client_id,
                )

            elif message.get("type") == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()}, client_id
                )

            else:
                # Echo back unknown messages
                await manager.send_personal_message(
                    {"type": "echo", "received": message}, client_id
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id)


# Helper functions for sending updates
async def send_upload_progress(client_id: str, filename: str, progress: float, uploaded: int, total: int):
    """
    Send upload progress update.

    Args:
        client_id: Client ID
        filename: File name
        progress: Progress percentage
        uploaded: Bytes uploaded
        total: Total bytes
    """
    await manager.send_personal_message(
        {
            "type": "upload_progress",
            "data": {
                "filename": filename,
                "progress": progress,
                "uploaded_bytes": uploaded,
                "total_bytes": total,
            },
            "timestamp": datetime.utcnow().isoformat(),
        },
        client_id,
    )


async def send_processing_status(client_id: str, task_id: str, status: str, progress: float, message: str):
    """
    Send processing status update.

    Args:
        client_id: Client ID
        task_id: Task ID
        status: Status (queued, processing, completed, failed)
        progress: Progress percentage
        message: Status message
    """
    await manager.send_personal_message(
        {
            "type": "processing_status",
            "data": {
                "task_id": task_id,
                "status": status,
                "progress": progress,
                "message": message,
            },
            "timestamp": datetime.utcnow().isoformat(),
        },
        client_id,
    )


async def send_notification(client_id: str, level: str, message: str, title: str = None):
    """
    Send notification.

    Args:
        client_id: Client ID
        level: Notification level (info, warning, error, success)
        message: Notification message
        title: Optional notification title
    """
    await manager.send_personal_message(
        {
            "type": "notification",
            "data": {
                "level": level,
                "title": title,
                "message": message,
            },
            "timestamp": datetime.utcnow().isoformat(),
        },
        client_id,
    )


async def broadcast_system_message(message: str):
    """
    Broadcast system message to all connected clients.

    Args:
        message: System message
    """
    await manager.broadcast(
        {
            "type": "system",
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
