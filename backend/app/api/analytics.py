"""
Analytics Dashboard APIs with Advanced Queries, Charts, and Graphs
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case, cast, Date
from sqlalchemy.dialects.postgresql import JSONB
from typing import List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from ..models.tables import (
    Event, User, Vote, Comment, Like, TransportRequest, LostItem,
    EventType, EventStatus, UserRole
)
from ..core.database import get_db
from ..core.security import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard/overview")
async def get_dashboard_overview(
    days: int = Query(30, description="Last N days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall dashboard metrics"""
    if current_user.role not in [UserRole.admin, UserRole.moderator]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Total events
    total_events = db.query(Event).filter(Event.created_at >= cutoff_date).count()
    
    # Events by status
    status_counts = db.query(
        Event.status, func.count(Event.id)
    ).filter(Event.created_at >= cutoff_date).group_by(Event.status).all()
    
    # Events by category
    category_counts = db.query(
        Event.category, func.count(Event.id)
    ).filter(Event.created_at >= cutoff_date).group_by(Event.category).all()
    
    # Total users
    total_users = db.query(User).count()
    new_users = db.query(User).filter(User.created_at >= cutoff_date).count()
    
    # Engagement metrics
    total_votes = db.query(Vote).filter(Vote.created_at >= cutoff_date).count()
    total_comments = db.query(Comment).filter(Comment.created_at >= cutoff_date).count()
    total_likes = db.query(Like).filter(Like.created_at >= cutoff_date).count()
    
    # Verification accuracy (validated vs invalidated)
    validated = db.query(Event).filter(
        Event.status == EventStatus.validated,
        Event.created_at >= cutoff_date
    ).count()
    invalidated = db.query(Event).filter(
        Event.status == EventStatus.invalidated,
        Event.created_at >= cutoff_date
    ).count()
    accuracy = validated / (validated + invalidated) * 100 if (validated + invalidated) > 0 else 0
    
    return {
        "total_events": total_events,
        "new_users": new_users,
        "total_users": total_users,
        "engagement": {
            "votes": total_votes,
            "comments": total_comments,
            "likes": total_likes
        },
        "status_breakdown": {str(s.value): c for s, c in status_counts},
        "category_breakdown": {str(c.value): cnt for c, cnt in category_counts},
        "verification_accuracy": round(accuracy, 2)
    }

@router.get("/dashboard/events/timeseries")
async def get_events_timeseries(
    days: int = Query(30),
    interval: str = Query("day", description="day, week, month"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get event counts over time for line charts"""
    if current_user.role not in [UserRole.admin, UserRole.moderator]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    if interval == "day":
        date_trunc = cast(func.date_trunc('day', Event.created_at), Date)
    elif interval == "week":
        date_trunc = cast(func.date_trunc('week', Event.created_at), Date)
    elif interval == "month":
        date_trunc = cast(func.date_trunc('month', Event.created_at), Date)
    else:
        date_trunc = cast(func.date_trunc('day', Event.created_at), Date)
    
    results = db.query(
        date_trunc.label('date'),
        func.count(Event.id).label('count')
    ).filter(
        Event.created_at >= cutoff_date
    ).group_by(date_trunc).order_by(date_trunc).all()
    
    return [{"date": str(r.date), "count": r.count} for r in results]

@router.get("/dashboard/heatmap")
async def get_safety_heatmap(
    grid_size: float = Query(0.01, description="Grid size in degrees (~1km)"),
    days: int = Query(30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate safety heatmap data (aggregated by grid cells)"""
    if current_user.role not in [UserRole.admin, UserRole.moderator]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Snap to grid using ST_SnapToGrid equivalent
    # This is a simplified version; production should use PostGIS directly
    events = db.query(
        Event.latitude, Event.longitude, Event.category, Event.status
    ).filter(Event.created_at >= cutoff_date).all()
    
    grid_data = {}
    for event in events:
        lat_grid = round(event.latitude / grid_size) * grid_size
        lng_grid = round(event.longitude / grid_size) * grid_size
        key = f"{lat_grid},{lng_grid}"
        
        if key not in grid_data:
            grid_data[key] = {
                "lat": lat_grid,
                "lng": lng_grid,
                "total": 0,
                "security": 0,
                "validated": 0,
                "invalidated": 0
            }
        
        grid_data[key]["total"] += 1
        if event.category == EventType.security:
            grid_data[key]["security"] += 1
        if event.status == EventStatus.validated:
            grid_data[key]["validated"] += 1
        elif event.status == EventStatus.invalidated:
            grid_data[key]["invalidated"] += 1
    
    # Calculate safety score (0-100)
    for cell in grid_data.values():
        # Higher security events = lower safety
        # Higher invalidated = lower reliability
        base_score = 100
        base_score -= min(cell["security"] * 5, 50)  # Max -50 for security
        base_score -= min(cell["invalidated"] * 2, 20)  # Max -20 for invalid
        cell["safety_score"] = max(0, min(100, base_score))
    
    return list(grid_data.values())

@router.get("/dashboard/top-contributors")
async def get_top_contributors(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get top contributors by reputation and activity"""
    if current_user.role not in [UserRole.admin, UserRole.moderator]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Subquery for vote counts
    vote_counts = db.query(
        Vote.user_id, func.count(Vote.id).label('vote_count')
    ).group_by(Vote.user_id).subquery()
    
    # Subquery for comment counts
    comment_counts = db.query(
        Comment.user_id, func.count(Comment.id).label('comment_count')
    ).group_by(Comment.user_id).subquery()
    
    # Subquery for event reports
    event_counts = db.query(
        Event.reporter_id, func.count(Event.id).label('event_count')
    ).group_by(Event.reporter_id).subquery()
    
    users = db.query(
        User.id, User.email, User.phone, User.reputation_points,
        func.coalesce(vote_counts.c.vote_count, 0).label('votes'),
        func.coalesce(comment_counts.c.comment_count, 0).label('comments'),
        func.coalesce(event_counts.c.event_count, 0).label('events')
    ).outerjoin(vote_counts, User.id == vote_counts.c.user_id
    ).outerjoin(comment_counts, User.id == comment_counts.c.user_id
    ).outerjoin(event_counts, User.id == event_counts.c.reporter_id
    ).order_by(User.reputation_points.desc()
    ).limit(limit).all()
    
    return [{
        "user_id": str(u.id),
        "identifier": u.email or u.phone,
        "reputation": u.reputation_points,
        "votes": u.votes,
        "comments": u.comments,
        "events_reported": u.events
    } for u in users]

@router.get("/dashboard/category-trends")
async def get_category_trends(
    days: int = Query(90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get category trends over time for stacked area charts"""
    if current_user.role not in [UserRole.admin, UserRole.moderator]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    results = db.query(
        cast(func.date_trunc('week', Event.created_at), Date).label('week'),
        Event.category,
        func.count(Event.id).label('count')
    ).filter(
        Event.created_at >= cutoff_date
    ).group_by(
        cast(func.date_trunc('week', Event.created_at), Date),
        Event.category
    ).order_by('week').all()
    
    # Reformat for chart.js
    weeks = sorted(set(str(r.week) for r in results))
    categories = sorted(set(str(r.category) for r in results))
    
    datasets = {}
    for cat in categories:
        datasets[cat] = [0] * len(weeks)
    
    for r in results:
        week_idx = weeks.index(str(r.week))
        cat_key = str(r.category)
        datasets[cat_key][week_idx] = r.count
    
    return {
        "labels": weeks,
        "datasets": datasets
    }

@router.get("/dashboard/transport-stats")
async def get_transport_statistics(
    days: int = Query(30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get taxi/bicycle request statistics"""
    if current_user.role not in [UserRole.admin, UserRole.moderator]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    total_requests = db.query(TransportRequest).filter(
        TransportRequest.created_at >= cutoff_date
    ).count()
    
    by_type = db.query(
        TransportRequest.type, func.count(TransportRequest.id)
    ).filter(
        TransportRequest.created_at >= cutoff_date
    ).group_by(TransportRequest.type).all()
    
    by_status = db.query(
        TransportRequest.status, func.count(TransportRequest.id)
    ).filter(
        TransportRequest.created_at >= cutoff_date
    ).group_by(TransportRequest.status).all()
    
    # Average response time (accepted - created)
    avg_response = db.query(
        func.avg(TransportRequest.updated_at - TransportRequest.created_at)
    ).filter(
        TransportRequest.created_at >= cutoff_date,
        TransportRequest.status.in_(['accepted', 'completed'])
    ).scalar()
    
    return {
        "total_requests": total_requests,
        "by_type": {str(t.value): c for t, c in by_type},
        "by_status": {s: c for s, c in by_status},
        "avg_response_time_minutes": float(avg_response.total_seconds() / 60) if avg_response else 0
    }

@router.get("/dashboard/lost-items-stats")
async def get_lost_items_statistics(
    days: int = Query(30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get lost/found items statistics"""
    if current_user.role not in [UserRole.admin, UserRole.moderator]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    total_items = db.query(LostItem).join(Event).filter(
        Event.created_at >= cutoff_date
    ).count()
    
    by_type = db.query(
        LostItem.item_type, func.count(LostItem.id)
    ).join(Event).filter(
        Event.created_at >= cutoff_date
    ).group_by(LostItem.item_type).all()
    
    lost_vs_found = db.query(
        LostItem.is_lost, func.count(LostItem.id)
    ).join(Event).filter(
        Event.created_at >= cutoff_date
    ).group_by(LostItem.is_lost).all()
    
    returned = db.query(LostItem).join(Event).filter(
        Event.created_at >= cutoff_date,
        LostItem.status == 'returned'
    ).count()
    
    return_rate = returned / total_items * 100 if total_items > 0 else 0
    
    return {
        "total_items": total_items,
        "by_type": {str(t.value): c for t, c in by_type},
        "lost_count": sum(c for l, c in lost_vs_found if l),
        "found_count": sum(c for l, c in lost_vs_found if not l),
        "returned_count": returned,
        "return_rate_percent": round(return_rate, 2)
    }
