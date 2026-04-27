"""
Engagement APIs: Search, View, Like, Comment, Share, Preferences
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import List, Optional
from uuid import UUID
import logging

from ..models.tables import (
    Event, User, Comment, Like, Vote, UserPreference, 
    EventType, EventStatus, TransportType, LostItemType, TransportRequest, LostItem
)
from ..core.database import get_db
from ..core.security import get_current_user
from ..schemas.main import (
    EventResponse, CommentCreate, CommentResponse, 
    PreferenceUpdate, TransportRequestCreate, LostItemCreate,
    MessageResponse
)

router = APIRouter(prefix="/engagement", tags=["Engagement"])
logger = logging.getLogger(__name__)

# --- Search & Browse ---

@router.get("/events/search", response_model=List[EventResponse])
async def search_events(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[EventType] = Query(None),
    status: Optional[EventStatus] = Query(None),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    radius_km: float = Query(5.0, ge=0.1, le=50),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search events with filters, geospatial search, and full-text search"""
    query = db.query(Event).filter(Event.status != EventStatus.invalidated)
    
    # Text search
    if q:
        search_filter = or_(
            Event.title.ilike(f"%{q}%"),
            Event.description.ilike(f"%{q}%"),
            Event.sub_category.ilike(f"%{q}%")
        )
        query = query.filter(search_filter)
    
    # Category filter
    if category:
        query = query.filter(Event.category == category)
    
    # Status filter
    if status:
        query = query.filter(Event.status == status)
    
    # Geospatial filter
    if lat and lng:
        # PostGIS ST_DWithin equivalent in SQLAlchemy Core
        from sqlalchemy import text
        point_wkt = f"POINT({lng} {lat})"
        query = query.filter(
            text(f"ST_DWithin(location_geom, ST_GeomFromText('{point_wkt}', 4326), :radius)")
        ).params(radius=radius_km * 1000)  # meters
    
    # Order by recency
    query = query.order_by(Event.created_at.desc()).limit(limit)
    
    events = query.all()
    return events

@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event_details(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get event details and increment view count"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Increment view count
    event.view_count += 1
    db.commit()
    db.refresh(event)
    
    return event

# --- Likes ---

@router.post("/events/{event_id}/like", response_model=MessageResponse)
async def like_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Like an event (toggle)"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    existing_like = db.query(Like).filter(
        Like.event_id == event_id,
        Like.user_id == current_user.id
    ).first()
    
    if existing_like:
        # Unlike
        db.delete(existing_like)
        event.like_count = max(0, event.like_count - 1)
        msg = "Event unliked"
    else:
        # Like
        new_like = Like(event_id=event_id, user_id=current_user.id)
        db.add(new_like)
        event.like_count += 1
        msg = "Event liked"
    
    db.commit()
    return {"message": msg, "count": event.like_count}

@router.get("/events/{event_id}/likes")
async def get_event_likes(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get users who liked this event"""
    likes = db.query(Like, User).join(User).filter(Like.event_id == event_id).all()
    return [{"user_id": l.User.id, "created_at": l.Like.created_at} for l in likes]

# --- Comments ---

@router.post("/events/{event_id}/comments", response_model=CommentResponse)
async def add_comment(
    event_id: UUID,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a comment to an event (supports nested replies via parent_id)"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Validate parent if replying
    if comment_data.parent_id:
        parent = db.query(Comment).filter(Comment.id == comment_data.parent_id).first()
        if not parent or parent.event_id != event_id:
            raise HTTPException(status_code=400, detail="Invalid parent comment")
    
    new_comment = Comment(
        event_id=event_id,
        user_id=current_user.id,
        content=comment_data.content,
        parent_id=comment_data.parent_id
    )
    db.add(new_comment)
    event.comment_count += 1
    db.commit()
    db.refresh(new_comment)
    
    return new_comment

@router.get("/events/{event_id}/comments", response_model=List[CommentResponse])
async def get_event_comments(
    event_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all comments for an event (flat list, frontend can nest)"""
    comments = db.query(Comment).filter(
        Comment.event_id == event_id
    ).order_by(Comment.created_at.asc()).all()
    return comments

# --- User Preferences ---

@router.get("/preferences", response_model=PreferenceUpdate)
async def get_user_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's preferences"""
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if not prefs:
        # Create default
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    return prefs

@router.put("/preferences", response_model=PreferenceUpdate)
async def update_user_preferences(
    prefs_data: PreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user preferences for categories and locations"""
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if not prefs:
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)
    
    if prefs_data.preferred_categories is not None:
        prefs.preferred_categories = prefs_data.preferred_categories
    if prefs_data.preferred_locations is not None:
        prefs.preferred_locations = prefs_data.preferred_locations
    if prefs_data.notification_enabled is not None:
        prefs.notification_enabled = prefs_data.notification_enabled
    
    db.commit()
    db.refresh(prefs)
    return prefs

# --- Transport Requests (Taxi/Bicycle) ---

@router.post("/transport/request", response_model=TransportRequest)
async def create_transport_request(
    request_data: TransportRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a taxi or bicycle request"""
    new_request = TransportRequest(
        requester_id=current_user.id,
        type=request_data.type,
        pickup_lat=request_data.pickup_lat,
        pickup_lng=request_data.pickup_lng,
        dest_lat=request_data.dest_lat,
        dest_lng=request_data.dest_lng,
        destination_address=request_data.destination_address,
        passengers=request_data.passengers,
        notes=request_data.notes
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    
    # TODO: Send push notification to nearby providers
    return new_request

@router.get("/transport/requests/nearby", response_model=List[TransportRequest])
async def get_nearby_transport_requests(
    lat: float,
    lng: float,
    radius_km: float = 2.0,
    type: Optional[TransportType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get nearby transport requests (for drivers/bikers)"""
    query = db.query(TransportRequest).filter(
        TransportRequest.status == "pending"
    )
    
    if type:
        query = query.filter(TransportRequest.type == type)
    
    # Simple distance filter (can optimize with PostGIS)
    requests = query.all()
    nearby = []
    for req in requests:
        # Haversine formula approximation
        from math import radians, cos, sin, asin, sqrt
        lon1, lat1, lon2, lat2 = map(radians, [req.pickup_lng, req.pickup_lat, lng, lat])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        if km <= radius_km:
            nearby.append(req)
    
    return nearby[:20]

@router.post("/transport/{request_id}/accept", response_model=MessageResponse)
async def accept_transport_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept a transport request (become the provider)"""
    request = db.query(TransportRequest).filter(TransportRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    if request.status != "pending":
        raise HTTPException(status_code=400, detail="Request no longer pending")
    
    request.provider_id = current_user.id
    request.status = "accepted"
    db.commit()
    
    return {"message": "Request accepted", "request_id": str(request_id)}

# --- Lost Items ---

@router.post("/lost-items", response_model=LostItem)
async def create_lost_item(
    item_data: LostItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report a lost item/person/pet"""
    # First create the base event
    from ..models.tables import Event as EventModel
    new_event = EventModel(
        title=f"{'Lost' if item_data.is_lost else 'Found'}: {item_data.item_type.value}",
        description=item_data.description,
        category=EventType.lost_found,
        sub_category=item_data.item_type.value,
        latitude=item_data.latitude,
        longitude=item_data.longitude,
        reporter_id=current_user.id,
        extra_data={"reward_amount": item_data.reward_amount}
    )
    db.add(new_event)
    db.flush()  # Get ID
    
    new_item = LostItem(
        event_id=new_event.id,
        item_type=item_data.item_type,
        is_lost=item_data.is_lost,
        description=item_data.description,
        brand=item_data.brand,
        color=item_data.color,
        date_lost=item_data.date_lost,
        reward_amount=item_data.reward_amount,
        person_name=item_data.person_name,
        age_estimate=item_data.age_estimate,
        last_seen_location=item_data.last_seen_location
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return new_item

@router.get("/lost-items", response_model=List[LostItem])
async def search_lost_items(
    item_type: Optional[LostItemType] = Query(None),
    is_lost: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search lost/found items"""
    query = db.query(LostItem)
    if item_type:
        query = query.filter(LostItem.item_type == item_type)
    if is_lost is not None:
        query = query.filter(LostItem.is_lost == is_lost)
    if status:
        query = query.filter(LostItem.status == status)
    
    return query.order_by(LostItem.created_at.desc()).limit(50).all()
