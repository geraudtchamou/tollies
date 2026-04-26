from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from ..db.session import get_db
from ..models import User, Event, Vote, Badge, UserBadge, EventStatus
from ..schemas import AnalyticsResponse, LeaderboardResponse, LeaderboardEntry
from .auth import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])


def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to check if user is admin."""
    if current_user.role not in ['admin', 'official']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get platform analytics dashboard data."""
    
    # Total events by status
    total_events = db.query(Event).count()
    validated_events = db.query(Event).filter(Event.status == EventStatus.VALIDATED).count()
    pending_events = db.query(Event).filter(Event.status == EventStatus.PENDING).count()
    invalidated_events = db.query(Event).filter(Event.status == EventStatus.INVALIDATED).count()
    
    # User stats
    total_users = db.query(User).count()
    
    # Top categories
    category_stats = db.query(
        Event.category,
        db.func.count(Event.id).label('count')
    ).group_by(Event.category).all()
    
    top_categories = [
        {"category": cat.value, "count": count}
        for cat, count in sorted(category_stats, key=lambda x: x[1, 'count'], reverse=True)[:5]
    ]
    
    # Hot spots (locations with most events) - simplified
    hot_spots = db.query(
        Event.latitude,
        Event.longitude,
        db.func.count(Event.id).label('count')
    ).group_by(Event.latitude, Event.longitude).order_by(
        db.func.count(Event.id).desc()
    ).limit(10).all()
    
    hot_spots_data = [
        {"latitude": lat, "longitude": lon, "event_count": count}
        for lat, lon, count in hot_spots
    ]
    
    # Verification accuracy (validated / total verified)
    total_verified = validated_events + invalidated_events
    verification_accuracy = (validated_events / total_verified * 100) if total_verified > 0 else 0
    
    return {
        "total_events": total_events,
        "validated_events": validated_events,
        "pending_events": pending_events,
        "invalidated_events": invalidated_events,
        "total_users": total_users,
        "active_users_today": 0,  # Would need activity tracking
        "top_categories": top_categories,
        "hot_spots": hot_spots_data,
        "verification_accuracy": round(verification_accuracy, 2)
    }


@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    limit: int = 10,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get gamification leaderboard."""
    
    # Get users with highest reputation and their badge counts
    users = db.query(User).order_by(User.reputation_points.desc()).limit(limit).all()
    
    entries = []
    for rank, user in enumerate(users, 1):
        badges_count = db.query(UserBadge).filter(UserBadge.user_id == user.id).count()
        verifications_count = db.query(Vote).filter(Vote.user_id == user.id).count()
        
        entries.append(LeaderboardEntry(
            user_id=user.id,
            username=user.email or user.phone or f"User_{str(user.id)[:8]}",
            reputation_points=user.reputation_points,
            badges_count=badges_count,
            verifications_count=verifications_count,
            rank=rank
        ))
    
    return {"entries": entries}


@router.post("/broadcast")
def create_official_broadcast(
    title: str,
    description: str,
    latitude: float,
    longitude: float,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Create an official broadcast event (auto-validated)."""
    
    from geoalchemy2.shape import from_shape
    from shapely.geometry import Point
    
    location = from_shape(Point(longitude, latitude), srid=4326)
    
    event = Event(
        title=title,
        description=description,
        category="other",
        latitude=latitude,
        longitude=longitude,
        location=location,
        reporter_id=admin.id,
        is_official_broadcast=True,
        status=EventStatus.VALIDATED,  # Auto-validated
        yes_votes=999,  # Show strong support
        verification_threshold=1
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    # TODO: Broadcast to all users via FCM
    
    return {
        "message": "Official broadcast created",
        "event_id": str(event.id)
    }


@router.get("/users")
def list_users(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """List all users (admin only)."""
    
    offset = (page - 1) * page_size
    users = db.query(User).offset(offset).limit(page_size).all()
    total = db.query(User).count()
    
    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "phone": u.phone,
                "role": u.role.value,
                "reputation_points": u.reputation_points,
                "is_verified": u.is_verified,
                "created_at": u.created_at.isoformat()
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: uuid.UUID,
    new_role: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Update a user's role (admin only)."""
    
    from ..models import UserRole
    
    valid_roles = ["user", "moderator", "admin", "official"]
    if new_role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {valid_roles}"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.role = getattr(UserRole, new_role.upper())
    db.commit()
    
    return {"message": f"User role updated to {new_role}"}
