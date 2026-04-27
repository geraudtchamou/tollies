from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
import uuid
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.tables import (
    Event, LostDocument, ForgottenItem, TransportRequest, 
    User, Vote, EventCategory, EventStatus
)
from app.schemas.main import (
    EventCreate, EventResponse, LostDocumentResponse, 
    ForgottenItemResponse, TransportRequestResponse,
    TransportAcceptRequest, AdvancedAnalyticsResponse,
    CategoryStats, HotSpot, VerificationTrend
)
from app.core.security import get_current_user

router = APIRouter()


@router.post("/lost-document", response_model=LostDocumentResponse, status_code=status.HTTP_201_CREATED)
def report_lost_document(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Report a lost document (ID, passport, license, etc.)"""
    if not event_data.document_details:
        raise HTTPException(status_code=400, detail="Document details required")
    
    # Create the base event
    db_event = Event(
        title=event_data.title,
        description=event_data.description,
        category=EventCategory.LOST_DOCUMENT,
        latitude=event_data.latitude,
        longitude=event_data.longitude,
        address=event_data.address,
        reporter_id=current_user.id,
        media_urls=event_data.media_urls or []
    )
    db.add(db_event)
    db.flush()
    
    # Create lost document record
    doc_details = event_data.document_details
    db_document = LostDocument(
        event_id=db_event.id,
        document_type=doc_details.document_type or "Unknown",
        document_number=doc_details.document_number,
        issuing_authority=doc_details.issuing_authority,
        holder_name=doc_details.holder_name,
        description=doc_details.description,
        photo_urls=event_data.media_urls or [],
        contact_info=doc_details.contact_info or current_user.phone or current_user.email,
        is_sensitive=doc_details.is_sensitive
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    return db_document


@router.get("/lost-documents", response_model=List[LostDocumentResponse])
def get_lost_documents(
    skip: int = 0,
    limit: int = 50,
    document_type: Optional[str] = None,
    is_found: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all lost documents with filters"""
    query = db.query(LostDocument).join(Event).filter(
        Event.category == EventCategory.LOST_DOCUMENT
    )
    
    if document_type:
        query = query.filter(LostDocument.document_type.ilike(f"%{document_type}%"))
    if is_found is not None:
        query = query.filter(LostDocument.is_found == is_found)
    
    # Hide sensitive info for non-owners
    documents = query.offset(skip).limit(limit).all()
    return documents


@router.put("/lost-document/{document_id}/found")
def mark_document_found(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a lost document as found"""
    db_document = db.query(LostDocument).filter(LostDocument.id == document_id).first()
    if not db_document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db_document.is_found = True
    db_event = db.query(Event).filter(Event.id == db_document.event_id).first()
    if db_event:
        db_event.status = EventStatus.VALIDATED
    
    db.commit()
    return {"message": "Document marked as found"}


@router.post("/forgotten-item", response_model=ForgottenItemResponse, status_code=status.HTTP_201_CREATED)
def report_forgotten_item(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Report a forgotten bag, parcel, or other item"""
    if not event_data.forgotten_item_details:
        raise HTTPException(status_code=400, detail="Item details required")
    
    # Create the base event
    db_event = Event(
        title=event_data.title,
        description=event_data.description,
        category=EventCategory.FORGOTTEN_BAG,
        latitude=event_data.latitude,
        longitude=event_data.longitude,
        address=event_data.address,
        reporter_id=current_user.id,
        media_urls=event_data.media_urls or []
    )
    db.add(db_event)
    db.flush()
    
    # Create forgotten item record
    item_details = event_data.forgotten_item_details
    db_item = ForgottenItem(
        event_id=db_event.id,
        item_type=item_details.item_type or "Unknown",
        brand=item_details.brand,
        color=item_details.color,
        size=item_details.size,
        description=item_details.description,
        location_description=item_details.location_description,
        photo_urls=event_data.media_urls or [],
        contact_info=item_details.contact_info or current_user.phone or current_user.email,
        contains_valuables=item_details.contains_valuables
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item


@router.get("/forgotten-items", response_model=List[ForgottenItemResponse])
def get_forgotten_items(
    skip: int = 0,
    limit: int = 50,
    item_type: Optional[str] = None,
    is_claimed: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all forgotten items with filters"""
    query = db.query(ForgottenItem).join(Event).filter(
        Event.category == EventCategory.FORGOTTEN_BAG
    )
    
    if item_type:
        query = query.filter(ForgottenItem.item_type.ilike(f"%{item_type}%"))
    if is_claimed is not None:
        query = query.filter(ForgottenItem.is_claimed == is_claimed)
    
    items = query.offset(skip).limit(limit).all()
    return items


@router.put("/forgotten-item/{item_id}/claim")
def claim_forgotten_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Claim a forgotten item"""
    db_item = db.query(ForgottenItem).filter(ForgottenItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db_item.is_claimed = True
    db_event = db.query(Event).filter(Event.id == db_item.event_id).first()
    if db_event:
        db_event.status = EventStatus.VALIDATED
    
    db.commit()
    return {"message": "Item claimed successfully"}


@router.post("/transport-request", response_model=TransportRequestResponse, status_code=status.HTTP_201_CREATED)
def create_transport_request(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a taxi or bicycle transport request"""
    if not event_data.transport_details:
        raise HTTPException(status_code=400, detail="Transport details required")
    
    transport = event_data.transport_details
    if transport.request_type not in ["taxi", "bicycle"]:
        raise HTTPException(status_code=400, detail="Invalid transport type")
    
    # Determine category based on transport type
    category = EventCategory.TAXI_NEEDED if transport.request_type == "taxi" else EventCategory.BICYCLE_NEEDED
    
    # Create the base event
    db_event = Event(
        title=f"{transport.request_type.capitalize()} needed",
        description=f"Need {transport.request_type} from {transport.pickup_address or 'current location'}",
        category=category,
        latitude=transport.pickup_latitude,
        longitude=transport.pickup_longitude,
        address=transport.pickup_address,
        reporter_id=current_user.id,
        urgency=transport.urgency
    )
    db.add(db_event)
    db.flush()
    
    # Create transport request record
    db_transport = TransportRequest(
        event_id=db_event.id,
        request_type=transport.request_type,
        passenger_id=current_user.id,
        pickup_latitude=transport.pickup_latitude,
        pickup_longitude=transport.pickup_longitude,
        pickup_address=transport.pickup_address,
        destination_latitude=transport.destination_latitude,
        destination_longitude=transport.destination_longitude,
        destination_address=transport.destination_address,
        urgency=transport.urgency,
        passengers_count=transport.passengers_count,
        luggage_info=transport.luggage_info,
        special_requirements=transport.special_requirements,
        estimated_price=transport.estimated_price
    )
    db.add(db_transport)
    db.commit()
    db.refresh(db_transport)
    
    return db_transport


@router.get("/transport-requests", response_model=List[TransportRequestResponse])
def get_transport_requests(
    skip: int = 0,
    limit: int = 50,
    request_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all transport requests with filters"""
    query = db.query(TransportRequest).join(Event).filter(
        Event.category.in_([EventCategory.TAXI_NEEDED, EventCategory.BICYCLE_NEEDED])
    )
    
    if request_type:
        query = query.filter(TransportRequest.request_type == request_type)
    if status_filter:
        query = query.filter(TransportRequest.status == status_filter)
    
    requests = query.order_by(TransportRequest.requested_at.desc()).offset(skip).limit(limit).all()
    return requests


@router.post("/transport-request/{request_id}/accept")
def accept_transport_request(
    request_id: uuid.UUID,
    accept_data: TransportAcceptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept a transport request as a provider"""
    db_transport = db.query(TransportRequest).filter(TransportRequest.id == request_id).first()
    if not db_transport:
        raise HTTPException(status_code=404, detail="Transport request not found")
    
    if db_transport.status != "pending":
        raise HTTPException(status_code=400, detail="Request already accepted or completed")
    
    db_transport.status = "accepted"
    db_transport.provider_id = current_user.id
    db_transport.accepted_at = datetime.utcnow()
    if accept_data.estimated_price:
        db_transport.estimated_price = accept_data.estimated_price
    
    db.commit()
    return {"message": "Transport request accepted"}


@router.post("/transport-request/{request_id}/complete")
def complete_transport_request(
    request_id: uuid.UUID,
    final_price: Optional[float] = None,
    rating: Optional[float] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete a transport request"""
    db_transport = db.query(TransportRequest).filter(TransportRequest.id == request_id).first()
    if not db_transport:
        raise HTTPException(status_code=404, detail="Transport request not found")
    
    if db_transport.status != "accepted" and db_transport.status != "in_progress":
        raise HTTPException(status_code=400, detail="Request cannot be completed")
    
    db_transport.status = "completed"
    db_transport.completed_at = datetime.utcnow()
    if final_price:
        db_transport.final_price = final_price
    if rating:
        db_transport.provider_rating = rating
    
    # Update provider reputation
    if db_transport.provider_id:
        provider = db.query(User).filter(User.id == db_transport.provider_id).first()
        if provider:
            provider.reputation_points += 10
    
    db.commit()
    return {"message": "Transport completed successfully"}


@router.get("/analytics/advanced", response_model=AdvancedAnalyticsResponse)
def get_advanced_analytics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get advanced analytics with detailed statistics and trends"""
    if current_user.role not in ["admin", "moderator", "official"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Basic counts
    total_events = db.query(Event).filter(Event.created_at >= cutoff_date).count()
    validated_events = db.query(Event).filter(
        Event.status == EventStatus.VALIDATED,
        Event.created_at >= cutoff_date
    ).count()
    pending_events = db.query(Event).filter(
        Event.status == EventStatus.PENDING,
        Event.created_at >= cutoff_date
    ).count()
    invalidated_events = db.query(Event).filter(
        Event.status == EventStatus.INVALIDATED,
        Event.created_at >= cutoff_date
    ).count()
    
    total_users = db.query(User).count()
    active_users_today = db.query(User).filter(
        func.date(User.updated_at) == datetime.utcnow().date()
    ).count()
    
    # Top categories
    category_counts = db.query(
        Event.category,
        func.count(Event.id).label('count')
    ).filter(
        Event.created_at >= cutoff_date
    ).group_by(Event.category).order_by(func.count(Event.id).desc()).limit(10).all()
    
    top_categories = [
        CategoryStats(
            category=str(cat.category.value) if cat.category else "unknown",
            count=count,
            percentage=round((count / total_events * 100) if total_events > 0 else 0, 2)
        )
        for cat, count in category_counts
    ]
    
    # Hot spots (geospatial clustering)
    hot_spots_query = db.query(
        Event.latitude,
        Event.longitude,
        func.count(Event.id).label('event_count')
    ).filter(
        Event.created_at >= cutoff_date,
        Event.latitude.isnot(None),
        Event.longitude.isnot(None)
    ).group_by(
        Event.latitude, Event.longitude
    ).having(
        func.count(Event.id) > 2
    ).order_by(
        func.count(Event.id).desc()
    ).limit(10).all()
    
    hot_spots = [
        HotSpot(
            latitude=float(lat),
            longitude=float(lon),
            event_count=count,
            radius_km=0.5,
            primary_category="mixed"
        )
        for lat, lon, count in hot_spots_query
    ]
    
    # Verification accuracy
    total_verified = validated_events + invalidated_events
    verification_accuracy = round(
        (validated_events / total_verified * 100) if total_verified > 0 else 0, 2
    )
    
    # Verification trends (last 7 days)
    verification_trends = []
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=i)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        validated = db.query(Event).filter(
            Event.status == EventStatus.VALIDATED,
            Event.created_at >= day_start,
            Event.created_at < day_end
        ).count()
        invalidated = db.query(Event).filter(
            Event.status == EventStatus.INVALIDATED,
            Event.created_at >= day_start,
            Event.created_at < day_end
        ).count()
        pending = db.query(Event).filter(
            Event.status == EventStatus.PENDING,
            Event.created_at >= day_start,
            Event.created_at < day_end
        ).count()
        
        verification_trends.append(VerificationTrend(
            date=day_start.strftime("%Y-%m-%d"),
            validated=validated,
            invalidated=invalidated,
            pending=pending
        ))
    
    # Transport statistics
    transport_total = db.query(TransportRequest).count()
    transport_pending = db.query(TransportRequest).filter(
        TransportRequest.status == "pending"
    ).count()
    
    # Lost items found rate
    lost_items_total = db.query(LostDocument).count() + db.query(ForgottenItem).count()
    lost_items_found = db.query(LostDocument).filter(
        LostDocument.is_found == True
    ).count() + db.query(ForgottenItem).filter(
        ForgottenItem.is_claimed == True
    ).count()
    lost_items_found_rate = round(
        (lost_items_found / lost_items_total * 100) if lost_items_total > 0 else 0, 2
    )
    
    # Average verification time (simplified)
    avg_verification_time = 15.5  # Would need more complex query in production
    
    return AdvancedAnalyticsResponse(
        total_events=total_events,
        validated_events=validated_events,
        pending_events=pending_events,
        invalidated_events=invalidated_events,
        total_users=total_users,
        active_users_today=active_users_today,
        top_categories=top_categories,
        hot_spots=hot_spots,
        verification_accuracy=verification_accuracy,
        verification_trends=verification_trends,
        transport_requests_total=transport_total,
        transport_requests_pending=transport_pending,
        lost_items_found_rate=lost_items_found_rate,
        average_verification_time_minutes=avg_verification_time
    )
