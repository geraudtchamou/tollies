from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from typing import List, Optional
import uuid

from ..db.session import get_db
from ..models import Event, Vote, EventCategory, EventStatus, User
from ..schemas import (
    EventCreate, EventUpdate, EventResponse, EventListResponse, VoteRequest
)
from .auth import get_current_user

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new event."""
    
    # Create geometry for PostGIS
    location = from_shape(Point(event_data.longitude, event_data.latitude), srid=4326)
    
    # Determine verification threshold based on category
    verification_threshold = 3 if event_data.is_sos else 5
    
    event = Event(
        title=event_data.title,
        description=event_data.description,
        category=event_data.category,
        latitude=event_data.latitude,
        longitude=event_data.longitude,
        location=location,
        address=event_data.address,
        reporter_id=current_user.id,
        media_urls=event_data.media_urls or [],
        is_sos=event_data.is_sos,
        verification_threshold=verification_threshold,
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    # Award reputation points for reporting
    current_user.reputation_points += 1
    
    # TODO: Send push notifications to nearby users via FCM
    
    return event


@router.get("/", response_model=EventListResponse)
def get_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[EventCategory] = None,
    status_filter: Optional[EventStatus] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = None,
    is_sos: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get events with filters and geospatial search."""
    
    query = db.query(Event)
    
    # Apply filters
    if category:
        query = query.filter(Event.category == category)
    if status_filter:
        query = query.filter(Event.status == status_filter)
    if is_sos is not None:
        query = query.filter(Event.is_sos == is_sos)
    
    # Geospatial filter
    if latitude and longitude and radius_km:
        # Using ST_DWithin for geospatial query
        point = from_shape(Point(longitude, latitude), srid=4326)
        # Convert km to degrees (approximate)
        radius_degrees = radius_km / 111.0
        query = query.filter(
            func.ST_DWithin(
                Event.location,
                point,
                radius_degrees
            )
        )
    
    # Get total count
    total = query.count()
    
    # Pagination
    offset = (page - 1) * page_size
    events = query.order_by(Event.created_at.desc()).offset(offset).limit(page_size).all()
    
    return {
        "events": events,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific event by ID."""
    
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Increment views
    event.views += 1
    db.commit()
    
    return event


@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: uuid.UUID,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an event (reporter, moderator, or admin only)."""
    
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check permissions
    if event.reporter_id != current_user.id and current_user.role not in ['moderator', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this event"
        )
    
    # Update fields
    if event_data.title:
        event.title = event_data.title
    if event_data.description is not None:
        event.description = event_data.description
    if event_data.status:
        event.status = event_data.status
    if event_data.media_urls:
        event.media_urls = event_data.media_urls
    
    db.commit()
    db.refresh(event)
    
    return event


@router.delete("/{event_id}")
def delete_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an event (reporter, moderator, or admin only)."""
    
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check permissions
    if event.reporter_id != current_user.id and current_user.role not in ['moderator', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this event"
        )
    
    db.delete(event)
    db.commit()
    
    return {"message": "Event deleted successfully"}


@router.post("/{event_id}/vote")
def vote_on_event(
    event_id: uuid.UUID,
    vote_data: VoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vote on event verification."""
    
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check if user already voted
    existing_vote = db.query(Vote).filter(
        and_(Vote.event_id == event_id, Vote.user_id == current_user.id)
    ).first()
    
    if existing_vote:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already voted on this event"
        )
    
    # Create vote
    vote = Vote(
        event_id=event_id,
        user_id=current_user.id,
        vote_type=vote_data.vote_type
    )
    db.add(vote)
    
    # Update event vote counts
    if vote_data.vote_type == "yes":
        event.yes_votes += 1
    else:
        event.no_votes += 1
    
    # Auto-validate/invalidated based on threshold
    if event.yes_votes >= event.verification_threshold and event.status == EventStatus.PENDING:
        event.status = EventStatus.VALIDATED
        # Award reputation to reporter
        reporter = db.query(User).filter(User.id == event.reporter_id).first()
        if reporter:
            reporter.reputation_points += 5
    
    if event.no_votes >= event.verification_threshold and event.status == EventStatus.PENDING:
        event.status = EventStatus.INVALIDATED
    
    # Award reputation for voting
    current_user.reputation_points += 1
    
    db.commit()
    db.refresh(event)
    
    # TODO: Broadcast vote update via WebSocket
    
    return {
        "message": "Vote recorded",
        "yes_votes": event.yes_votes,
        "no_votes": event.no_votes,
        "status": event.status.value
    }


@router.get("/category/{category}", response_model=EventListResponse)
def get_events_by_category(
    category: EventCategory,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get events by category."""
    
    offset = (page - 1) * page_size
    query = db.query(Event).filter(Event.category == category)
    total = query.count()
    events = query.order_by(Event.created_at.desc()).offset(offset).limit(page_size).all()
    
    return {
        "events": events,
        "total": total,
        "page": page,
        "page_size": page_size
    }
