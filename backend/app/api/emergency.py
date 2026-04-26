from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from ..db.session import get_db
from ..models import User, Event, EventStatus, LiveStream
from ..schemas import SOSRequest, SafeWalkCreate, SafeWalkResponse
from .auth import get_current_user
from .websocket import manager, notify_nearby_users

router = APIRouter(tags=["Emergency & Safety"])


@router.post("/sos")
def trigger_sos(
    sos_data: SOSRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger emergency SOS alert."""
    
    from geoalchemy2.shape import from_shape
    from shapely.geometry import Point
    
    # Create SOS event
    location = from_shape(Point(sos_data.longitude, sos_data.latitude), srid=4326)
    
    event = Event(
        title="🚨 SOS EMERGENCY ALERT",
        description=sos_data.message,
        category="other",
        latitude=sos_data.latitude,
        longitude=sos_data.longitude,
        location=location,
        reporter_id=current_user.id,
        is_sos=True,
        status=EventStatus.VALIDATED,  # Auto-validated for SOS
        verification_threshold=1
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    # Notify nearby users immediately
    notify_nearby_users(
        sos_data.latitude,
        sos_data.longitude,
        {
            "type": "SOS",
            "message": sos_data.message,
            "latitude": sos_data.latitude,
            "longitude": sos_data.longitude
        }
    )
    
    # Broadcast via WebSocket
    import asyncio
    asyncio.create_task(manager.broadcast_to_all({
        "type": "emergency_sos",
        "event_id": str(event.id),
        "location": {
            "latitude": sos_data.latitude,
            "longitude": sos_data.longitude
        },
        "message": "EMERGENCY ALERT - Immediate assistance needed!"
    }))
    
    # TODO: Integrate with local emergency services API
    # TODO: Send SMS to emergency contacts
    
    return {
        "message": "SOS alert triggered successfully",
        "event_id": str(event.id),
        "emergency_services_notified": False  # Would be True with integration
    }


@router.post("/safe-walk", response_model=SafeWalkResponse)
def start_safe_walk(
    walk_data: SafeWalkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a safe walk tracking session."""
    
    from geoalchemy2.shape import from_shape
    from shapely.geometry import Point, LineString
    
    start_location = from_shape(
        Point(walk_data.start_longitude, walk_data.start_latitude),
        srid=4326
    )
    end_location = from_shape(
        Point(walk_data.end_longitude, walk_data.end_latitude),
        srid=4326
    )
    
    # Create route (simplified - in production would use routing API)
    route = [
        [walk_data.start_latitude, walk_data.start_longitude],
        [walk_data.end_latitude, walk_data.end_longitude]
    ]
    
    from ..models import SafeWalk
    safe_walk = SafeWalk(
        user_id=current_user.id,
        companion_ids=walk_data.companion_ids or [],
        start_location=start_location,
        end_location=end_location,
        route=route
    )
    
    db.add(safe_walk)
    db.commit()
    db.refresh(safe_walk)
    
    # Notify companions
    # TODO: Send push notifications to companions
    
    return safe_walk


@router.get("/safe-walk/{walk_id}")
def get_safe_walk(
    walk_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get safe walk status."""
    
    from ..models import SafeWalk
    safe_walk = db.query(SafeWalk).filter(SafeWalk.id == walk_id).first()
    
    if not safe_walk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Safe walk not found"
        )
    
    # Check if user is involved
    if safe_walk.user_id != current_user.id and current_user.id not in safe_walk.companion_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this safe walk"
        )
    
    return {
        "id": str(safe_walk.id),
        "user_id": str(safe_walk.user_id),
        "is_active": safe_walk.is_active,
        "started_at": safe_walk.started_at.isoformat(),
        "alert_triggered": safe_walk.alert_triggered
    }


@router.put("/safe-walk/{walk_id}/complete")
def complete_safe_walk(
    walk_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark safe walk as completed."""
    
    from ..models import SafeWalk
    from datetime import datetime
    
    safe_walk = db.query(SafeWalk).filter(SafeWalk.id == walk_id).first()
    
    if not safe_walk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Safe walk not found"
        )
    
    if safe_walk.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    safe_walk.is_active = False
    safe_walk.completed_at = datetime.utcnow()
    db.commit()
    
    # Award reputation points for completing safely
    current_user.reputation_points += 2
    
    # Notify companions
    # TODO: Send completion notifications
    
    return {"message": "Safe walk completed successfully"}


@router.post("/live-stream")
def start_live_stream(
    event_id: uuid.UUID,
    stream_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a live video stream for an event."""
    
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Create live stream record
    live_stream = LiveStream(
        event_id=event_id,
        user_id=current_user.id,
        stream_url=stream_url
    )
    
    db.add(live_stream)
    
    # Update event
    event.has_live_stream = True
    db.commit()
    
    # Notify subscribers
    import asyncio
    asyncio.create_task(manager.broadcast_to_event(str(event_id), {
        "type": "live_stream_started",
        "stream_url": stream_url,
        "streamer": str(current_user.id)
    }))
    
    return {
        "message": "Live stream started",
        "stream_id": str(live_stream.id),
        "stream_url": stream_url
    }


@router.post("/live-stream/{stream_id}/end")
def end_live_stream(
    stream_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """End a live stream."""
    
    live_stream = db.query(LiveStream).filter(LiveStream.id == stream_id).first()
    if not live_stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live stream not found"
        )
    
    if live_stream.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to end this stream"
        )
    
    from datetime import datetime
    live_stream.is_active = False
    live_stream.ended_at = datetime.utcnow()
    
    # Update event
    event = db.query(Event).filter(Event.id == live_stream.event_id).first()
    if event:
        event.has_live_stream = False
    
    db.commit()
    
    # Notify subscribers
    import asyncio
    asyncio.create_task(manager.broadcast_to_event(str(live_stream.event_id), {
        "type": "live_stream_ended",
        "stream_id": str(stream_id)
    }))
    
    return {"message": "Live stream ended"}
