from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import List, Dict
import json
from datetime import datetime

from ..db.session import get_db
from ..models import Event, EventStatus
from ..schemas import EventResponse

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        # Store active connections
        self.active_connections: List[WebSocket] = []
        # Map event IDs to subscribed connections
        self.event_subscriptions: Dict[str, List[WebSocket]] = {}
        # Map user locations for proximity notifications
        self.user_locations: Dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept and store a new connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from all subscriptions
        for event_id in list(self.event_subscriptions.keys()):
            if websocket in self.event_subscriptions[event_id]:
                self.event_subscriptions[event_id].remove(websocket)
    
    async def subscribe_to_event(self, websocket: WebSocket, event_id: str):
        """Subscribe a connection to an event's updates."""
        if event_id not in self.event_subscriptions:
            self.event_subscriptions[event_id] = []
        if websocket not in self.event_subscriptions[event_id]:
            self.event_subscriptions[event_id].append(websocket)
    
    async def unsubscribe_from_event(self, websocket: WebSocket, event_id: str):
        """Unsubscribe a connection from an event's updates."""
        if event_id in self.event_subscriptions:
            if websocket in self.event_subscriptions[event_id]:
                self.event_subscriptions[event_id].remove(websocket)
    
    async def broadcast_to_event(self, event_id: str, message: dict):
        """Broadcast a message to all subscribers of an event."""
        if event_id in self.event_subscriptions:
            disconnected = []
            for connection in self.event_subscriptions[event_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.disconnect(conn)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    def update_user_location(self, user_id: str, latitude: float, longitude: float):
        """Update a user's location for proximity notifications."""
        self.user_locations[user_id] = {
            "latitude": latitude,
            "longitude": longitude,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    def get_nearby_users(self, latitude: float, longitude: float, radius_km: float = 5.0) -> List[str]:
        """Get users within a radius of a location."""
        nearby = []
        radius_degrees = radius_km / 111.0
        
        for user_id, loc in self.user_locations.items():
            lat_diff = abs(loc["latitude"] - latitude)
            lon_diff = abs(loc["longitude"] - longitude)
            
            if lat_diff <= radius_degrees and lon_diff <= radius_degrees:
                nearby.append(user_id)
        
        return nearby


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time event updates."""
    
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            action = message.get("action")
            
            if action == "subscribe":
                event_id = message.get("event_id")
                if event_id:
                    await manager.subscribe_to_event(websocket, event_id)
                    await websocket.send_json({
                        "type": "subscribed",
                        "event_id": event_id
                    })
            
            elif action == "unsubscribe":
                event_id = message.get("event_id")
                if event_id:
                    await manager.unsubscribe_from_event(websocket, event_id)
            
            elif action == "update_location":
                user_id = message.get("user_id")
                latitude = message.get("latitude")
                longitude = message.get("longitude")
                if user_id and latitude and longitude:
                    manager.update_user_location(user_id, latitude, longitude)
            
            elif action == "get_live_feed":
                # Send recent events as initial feed
                recent_events = db.query(Event).filter(
                    Event.status == EventStatus.PENDING
                ).order_by(Event.created_at.desc()).limit(20).all()
                
                await websocket.send_json({
                    "type": "live_feed",
                    "events": [
                        {
                            "id": str(event.id),
                            "title": event.title,
                            "category": event.category.value,
                            "status": event.status.value,
                            "yes_votes": event.yes_votes,
                            "no_votes": event.no_votes,
                            "latitude": event.latitude,
                            "longitude": event.longitude,
                            "created_at": event.created_at.isoformat()
                        }
                        for event in recent_events
                    ]
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # Notify others that user left (optional)


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    """WebSocket endpoint for push notifications."""
    
    await manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def broadcast_event_update(event: Event, update_type: str):
    """Broadcast an event update to all subscribers."""
    event_id = str(event.id)
    
    message = {
        "type": update_type,
        "event_id": event_id,
        "data": {
            "id": event_id,
            "title": event.title,
            "status": event.status.value,
            "yes_votes": event.yes_votes,
            "no_votes": event.no_votes,
            "updated_at": datetime.utcnow().isoformat()
        }
    }
    
    await manager.broadcast_to_event(event_id, message)


async def notify_nearby_users(latitude: float, longitude: float, event_data: dict):
    """Notify nearby users about a new event."""
    nearby_users = manager.get_nearby_users(latitude, longitude, radius_km=5.0)
    
    notification = {
        "type": "nearby_event",
        "event": event_data,
        "message": f"New event reported near your location!"
    }
    
    # In production, also send FCM push notifications
    # For now, just log
    print(f"Notifying {len(nearby_users)} nearby users about event")
