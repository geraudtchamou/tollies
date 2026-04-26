"""
Advanced Features API - Event Merging, Analytics, Transport, Lost & Found
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint, ST_Within
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import json

from app.db.session import get_db
from app.models.tables import (
    Event, EventCategory, EventStatus, Vote, User, LostDocument, ForgottenItem,
    TransportRequest, RewardEscrow, RewardEscrowStatus, GeofenceSubscription,
    SafetyScore, PredictiveHotspot, InfrastructureIssue, MunicipalStatus,
    EmergencyResource, PersonalSafetyTimer
)
from app.schemas.main import (
    LostDocumentCreate, LostDocumentResponse, ForgottenItemCreate,
    ForgottenItemResponse, TransportRequestCreate, TransportRequestResponse,
    EventResponse, EventCreate
)
from app.core.security import get_current_user

router = APIRouter()


# ============================================================================
# AUTOMATED EVENT MERGING & DUPLICATE DETECTION
# ============================================================================

@router.post("/events/{event_id}/check-duplicates")
async def check_duplicate_events(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if an event has potential duplicates within 50m and 5 minutes
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Find events within 50 meters and 5 minutes with same category
    time_window = datetime.utcnow() - timedelta(minutes=5)
    
    duplicates = db.query(Event).filter(
        Event.id != event_id,
        Event.category == event.category,
        Event.created_at >= time_window,
        Event.status != EventStatus.MERGED,
        ST_DWithin(
            Event.location,
            f"SRID=4326;POINT({event.longitude} {event.latitude})",
            50  # 50 meters
        )
    ).all()
    
    return {
        "event_id": event_id,
        "potential_duplicates": [
            {
                "id": str(dup.id),
                "title": dup.title,
                "distance_meters": float(db.query(ST_Distance(
                    Event.location,
                    f"SRID=4326;POINT({event.longitude} {event.latitude})"
                )).filter(Event.id == dup.id).scalar()),
                "time_diff_seconds": (event.created_at - dup.created_at).total_seconds(),
                "reporter_id": str(dup.reporter_id)
            }
            for dup in duplicates
        ],
        "merge_recommended": len(duplicates) > 0
    }


@router.post("/events/merge")
async def merge_events(
    source_event_ids: List[str],
    target_event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Merge multiple source events into a single target event.
    Consolidates votes and notifies reporters.
    """
    if current_user.role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Only moderators can merge events")
    
    target_event = db.query(Event).filter(Event.id == target_event_id).first()
    if not target_event:
        raise HTTPException(status_code=404, detail="Target event not found")
    
    duplicate_group_id = uuid.uuid4()
    merged_count = 0
    
    for source_id in source_event_ids:
        source_event = db.query(Event).filter(Event.id == source_id).first()
        if not source_event:
            continue
        
        # Merge votes
        for vote in source_event.votes:
            # Check if user already voted on target
            existing_vote = db.query(Vote).filter(
                Vote.event_id == target_event_id,
                Vote.user_id == vote.user_id
            ).first()
            
            if not existing_vote:
                # Transfer vote to target
                vote.event_id = target_event_id
                merged_count += 1
        
        # Update event status
        source_event.status = EventStatus.MERGED
        source_event.merged_into_id = target_event_id
        source_event.duplicate_group_id = duplicate_group_id
    
    # Recalculate target event votes
    yes_votes = db.query(func.sum(Vote.weight)).filter(
        Vote.event_id == target_event_id,
        Vote.vote_type == "yes"
    ).scalar() or 0
    
    no_votes = db.query(func.sum(Vote.weight)).filter(
        Vote.event_id == target_event_id,
        Vote.vote_type == "no"
    ).scalar() or 0
    
    target_event.yes_votes = int(yes_votes)
    target_event.no_votes = int(no_votes)
    target_event.weighted_score = yes_votes - no_votes
    target_event.duplicate_group_id = duplicate_group_id
    
    db.commit()
    
    # TODO: Send notifications to all reporters about merge
    
    return {
        "message": f"Successfully merged {len(source_event_ids)} events",
        "target_event_id": str(target_event_id),
        "duplicate_group_id": str(duplicate_group_id),
        "votes_consolidated": merged_count
    }


# ============================================================================
# LOST DOCUMENTS
# ============================================================================

@router.post("/lost-documents", response_model=LostDocumentResponse)
async def create_lost_document(
    document: LostDocumentCreate,
    event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report a lost document"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if event.category != EventCategory.LOST_DOCUMENT:
        raise HTTPException(status_code=400, detail="Event must be LOST_DOCUMENT category")
    
    lost_doc = LostDocument(
        event_id=event_id,
        document_type=document.document_type,
        document_number=document.document_number,
        issuing_authority=document.issuing_authority,
        holder_name=document.holder_name,
        description=document.description,
        contact_info=document.contact_info,
        is_sensitive=document.is_sensitive
    )
    
    db.add(lost_doc)
    db.commit()
    db.refresh(lost_doc)
    
    return lost_doc


@router.get("/lost-documents", response_model=List[LostDocumentResponse])
async def search_lost_documents(
    document_type: Optional[str] = None,
    is_found: Optional[bool] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search lost documents with filters"""
    query = db.query(LostDocument).join(Event)
    
    if document_type:
        query = query.filter(LostDocument.document_type.ilike(f"%{document_type}%"))
    
    if is_found is not None:
        query = query.filter(LostDocument.is_found == is_found)
    
    # Only show non-sensitive info if not owner
    results = query.limit(limit).all()
    
    return results


@router.put("/lost-documents/{doc_id}/found")
async def mark_document_found(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a lost document as found"""
    lost_doc = db.query(LostDocument).filter(LostDocument.id == doc_id).first()
    if not lost_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    lost_doc.is_found = True
    lost_doc.event.status = EventStatus.RESOLVED
    
    db.commit()
    
    return {"message": "Document marked as found", "reward_eligible": True}


# ============================================================================
# FORGOTTEN ITEMS (BAGS, PARCELS)
# ============================================================================

@router.post("/forgotten-items", response_model=ForgottenItemResponse)
async def create_forgotten_item(
    item: ForgottenItemCreate,
    event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report a forgotten bag or parcel"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if event.category not in [EventCategory.FORGOTTEN_BAG, EventCategory.FORGOTTEN_PARCEL]:
        raise HTTPException(status_code=400, detail="Invalid event category")
    
    forgotten_item = ForgottenItem(
        event_id=event_id,
        item_type=item.item_type,
        brand=item.brand,
        color=item.color,
        size=item.size,
        description=item.description,
        location_description=item.location_description,
        contact_info=item.contact_info,
        contains_valuables=item.contains_valuables
    )
    
    db.add(forgotten_item)
    db.commit()
    db.refresh(forgotten_item)
    
    return forgotten_item


@router.get("/forgotten-items", response_model=List[ForgottenItemResponse])
async def search_forgotten_items(
    item_type: Optional[str] = None,
    is_claimed: Optional[bool] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search forgotten items"""
    query = db.query(ForgottenItem).join(Event)
    
    if item_type:
        query = query.filter(ForgottenItem.item_type.ilike(f"%{item_type}%"))
    
    if is_claimed is not None:
        query = query.filter(ForgottenItem.is_claimed == is_claimed)
    
    results = query.limit(limit).all()
    return results


@router.post("/forgotten-items/{item_id}/claim")
async def claim_forgotten_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Claim a forgotten item"""
    forgotten_item = db.query(ForgottenItem).filter(ForgottenItem.id == item_id).first()
    if not forgotten_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if forgotten_item.is_claimed:
        raise HTTPException(status_code=400, detail="Item already claimed")
    
    forgotten_item.is_claimed = True
    forgotten_item.event.status = EventStatus.RESOLVED
    
    db.commit()
    
    return {"message": "Item claimed successfully"}


# ============================================================================
# TRANSPORT REQUESTS (TAXI & BICYCLE)
# ============================================================================

@router.post("/transport-requests", response_model=TransportRequestResponse)
async def create_transport_request(
    request: TransportRequestCreate,
    event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a taxi or bicycle request"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    transport_request = TransportRequest(
        event_id=event_id,
        request_type=request.request_type,  # 'taxi' or 'bicycle'
        passenger_id=current_user.id,
        pickup_latitude=request.pickup_latitude,
        pickup_longitude=request.pickup_longitude,
        pickup_address=request.pickup_address,
        destination_latitude=request.destination_latitude,
        destination_longitude=request.destination_longitude,
        destination_address=request.destination_address,
        urgency=request.urgency,
        passengers_count=request.passengers_count,
        luggage_info=request.luggage_info,
        special_requirements=request.special_requirements
    )
    
    db.add(transport_request)
    db.commit()
    db.refresh(transport_request)
    
    # TODO: Notify nearby drivers/providers via WebSocket/push
    
    return transport_request


@router.get("/transport-requests/open", response_model=List[TransportRequestResponse])
async def get_open_transport_requests(
    request_type: Optional[str] = None,
    latitude: float = None,
    longitude: float = None,
    radius_km: float = 10.0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get open transport requests near a location"""
    query = db.query(TransportRequest).join(Event).filter(
        TransportRequest.status == "pending"
    )
    
    if request_type:
        query = query.filter(TransportRequest.request_type == request_type)
    
    if latitude and longitude:
        # Filter by distance using PostGIS
        point = f"SRID=4326;POINT({longitude} {latitude})"
        query = query.filter(
            ST_DWithin(
                Event.location,
                point,
                radius_km * 1000  # Convert to meters
            )
        )
    
    results = query.order_by(TransportRequest.requested_at.desc()).limit(limit).all()
    return results


@router.post("/transport-requests/{request_id}/accept")
async def accept_transport_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Driver/provider accepts a transport request"""
    transport_request = db.query(TransportRequest).filter(
        TransportRequest.id == request_id
    ).first()
    
    if not transport_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if transport_request.status != "pending":
        raise HTTPException(status_code=400, detail="Request not available")
    
    transport_request.status = "accepted"
    transport_request.provider_id = current_user.id
    transport_request.accepted_at = datetime.utcnow()
    
    db.commit()
    
    # TODO: Notify passenger
    
    return {"message": "Request accepted", "provider_id": str(current_user.id)}


@router.post("/transport-requests/{request_id}/complete")
async def complete_transport_request(
    request_id: str,
    final_price: Optional[float] = None,
    rating: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Complete a transport request"""
    transport_request = db.query(TransportRequest).filter(
        TransportRequest.id == request_id
    ).first()
    
    if not transport_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if transport_request.status != "in_progress":
        raise HTTPException(status_code=400, detail="Request not in progress")
    
    transport_request.status = "completed"
    transport_request.completed_at = datetime.utcnow()
    
    if final_price:
        transport_request.final_price = final_price
    
    if rating:
        transport_request.provider_rating = rating
    
    db.commit()
    
    return {"message": "Trip completed successfully"}


# ============================================================================
# REWARD ESCROW (STRIPE INTEGRATION PLACEHOLDER)
# ============================================================================

@router.post("/rewards/escrow/create")
async def create_reward_escrow(
    event_id: str,
    amount: float,
    currency: str = "USD",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a reward escrow for lost item recovery"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # In production: Create Stripe Payment Intent with escrow
    # stripe_payment_intent = stripe.PaymentIntent.create(...)
    
    escrow = RewardEscrow(
        event_id=event_id,
        requester_id=current_user.id,
        amount=amount,
        currency=currency,
        stripe_payment_intent_id=f"pi_mock_{uuid.uuid4()}",  # Placeholder
        status=RewardEscrowStatus.HELD
    )
    
    db.add(escrow)
    db.commit()
    db.refresh(escrow)
    
    return {
        "escrow_id": str(escrow.id),
        "amount": amount,
        "currency": currency,
        "status": "held",
        "message": "Reward held in escrow. Will be released upon item return."
    }


@router.post("/rewards/escrow/{escrow_id}/release")
async def release_reward_escrow(
    escrow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Release escrow reward after mutual confirmation"""
    escrow = db.query(RewardEscrow).filter(RewardEscrow.id == escrow_id).first()
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow not found")
    
    if escrow.status != RewardEscrowStatus.HELD:
        raise HTTPException(status_code=400, detail="Escrow not in held state")
    
    # In production: Release Stripe escrow
    # stripe.Transfer.create(...)
    
    escrow.status = RewardEscrowStatus.RELEASED
    escrow.released_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Reward released successfully", "amount": float(escrow.amount)}


# ============================================================================
# GEOFENCED ALERT SUBSCRIPTIONS
# ============================================================================

@router.post("/geofences")
async def create_geofence_subscription(
    name: str,
    polygon_coords: List[List[float]],  # [[lng, lat], [lng, lat], ...]
    notification_types: List[str] = ["security", "missing_person"],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a custom geofence for alerts"""
    # Convert coords to WKT POLYGON
    coords_str = ", ".join([f"{lng} {lat}" for lng, lat in polygon_coords])
    wkt_polygon = f"POLYGON(({coords_str}))"
    
    geofence = GeofenceSubscription(
        user_id=current_user.id,
        name=name,
        polygon=f"SRID=4326;{wkt_polygon}",
        notification_types=notification_types
    )
    
    db.add(geofence)
    db.commit()
    db.refresh(geofence)
    
    return {"message": "Geofence created", "geofence_id": str(geofence.id)}


@router.get("/geofences", response_model=List[Dict])
async def get_user_geofences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's geofence subscriptions"""
    geofences = db.query(GeofenceSubscription).filter(
        GeofenceSubscription.user_id == current_user.id,
        GeofenceSubscription.is_active == True
    ).all()
    
    return [
        {
            "id": str(g.id),
            "name": g.name,
            "notification_types": g.notification_types,
            "created_at": g.created_at
        }
        for g in geofences
    ]


# ============================================================================
# INFRASTRUCTURE ISSUES TRACKING
# ============================================================================

@router.post("/infrastructure/{event_id}")
async def create_infrastructure_issue(
    event_id: str,
    issue_type: str,  # pothole, traffic_light, street_light
    priority: str = "medium",
    assigned_department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create infrastructure repair tracking"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    issue = InfrastructureIssue(
        event_id=event_id,
        issue_type=issue_type,
        priority=priority,
        assigned_department=assigned_department
    )
    
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    return {"message": "Infrastructure issue tracked", "issue_id": str(issue.id)}


@router.put("/infrastructure/{issue_id}/status")
async def update_infrastructure_status(
    issue_id: str,
    municipal_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update infrastructure repair status (officials only)"""
    if current_user.role not in ["admin", "official"]:
        raise HTTPException(status_code=403, detail="Officials only")
    
    issue = db.query(InfrastructureIssue).filter(
        InfrastructureIssue.id == issue_id
    ).first()
    
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    issue.municipal_status = MunicipalStatus(municipal_status)
    
    if municipal_status == "fixed":
        issue.fixed_at = datetime.utcnow()
        issue.event.status = EventStatus.RESOLVED
    
    db.commit()
    
    return {"message": "Status updated", "status": municipal_status}


# ============================================================================
# EMERGENCY RESOURCES (HOSPITAL/SHELTER CAPACITY)
# ============================================================================

@router.get("/emergency-resources")
async def get_emergency_resources(
    resource_type: Optional[str] = None,
    latitude: float = None,
    longitude: float = None,
    radius_km: float = 10.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get nearby emergency resources with capacity info"""
    query = db.query(EmergencyResource).filter(
        EmergencyResource.is_operational == True
    )
    
    if resource_type:
        query = query.filter(EmergencyResource.resource_type == resource_type)
    
    if latitude and longitude:
        point = f"SRID=4326;POINT({longitude} {latitude})"
        query = query.filter(
            ST_DWithin(
                EmergencyResource.location,
                point,
                radius_km * 1000
            )
        )
    
    resources = query.all()
    
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "type": r.resource_type,
            "address": r.address,
            "contact": r.contact_phone,
            "occupancy_rate": r.occupancy_rate,
            "availability": r.current_availability,
            "services": r.services,
            "distance_km": None  # Calculate if lat/lng provided
        }
        for r in resources
    ]


@router.put("/emergency-resources/{resource_id}/capacity")
async def update_resource_capacity(
    resource_id: str,
    current_availability: int,
    total_capacity: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update emergency resource capacity (officials only)"""
    if current_user.role not in ["admin", "official"]:
        raise HTTPException(status_code=403, detail="Officials only")
    
    resource = db.query(EmergencyResource).filter(
        EmergencyResource.id == resource_id
    ).first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    resource.current_availability = current_availability
    
    if total_capacity:
        resource.total_capacity = total_capacity
        resource.occupancy_rate = 1.0 - (current_availability / total_capacity)
    
    resource.last_updated = datetime.utcnow()
    resource.updated_by = current_user.id
    
    db.commit()
    
    return {"message": "Capacity updated", "occupancy_rate": resource.occupancy_rate}


# ============================================================================
# PERSONAL SAFETY TIMER
# ============================================================================

@router.post("/safety-timer/start")
async def start_safety_timer(
    expected_duration_minutes: int,
    emergency_contact_ids: Optional[List[str]] = None,
    start_lat: float = None,
    start_lng: float = None,
    end_lat: float = None,
    end_lng: float = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a personal safety timer for solo walks"""
    timer = PersonalSafetyTimer(
        user_id=current_user.id,
        expected_duration_minutes=expected_duration_minutes,
        emergency_contact_ids=[uuid.UUID(cid) for cid in emergency_contact_ids] if emergency_contact_ids else [],
        start_location=f"SRID=4326;POINT({start_lng} {start_lat})" if start_lat and start_lng else None,
        end_location=f"SRID=4326;POINT({end_lng} {end_lat})" if end_lat and end_lng else None,
        expected_end_at=datetime.utcnow() + timedelta(minutes=expected_duration_minutes)
    )
    
    db.add(timer)
    db.commit()
    db.refresh(timer)
    
    # TODO: Schedule background job to check timer expiry
    
    return {
        "timer_id": str(timer.id),
        "expected_end_at": timer.expected_end_at,
        "message": f"Safety timer started. Auto-alert in {expected_duration_minutes} minutes if not checked in."
    }


@router.post("/safety-timer/{timer_id}/check-in")
async def check_in_safety_timer(
    timer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manual check-in to cancel safety timer"""
    timer = db.query(PersonalSafetyTimer).filter(
        PersonalSafetyTimer.id == timer_id,
        PersonalSafetyTimer.user_id == current_user.id
    ).first()
    
    if not timer:
        raise HTTPException(status_code=404, detail="Timer not found")
    
    timer.checked_in_at = datetime.utcnow()
    timer.is_active = False
    
    db.commit()
    
    return {"message": "Check-in successful. Timer cancelled."}


@router.get("/safety-timer/active")
async def get_active_safety_timers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's active safety timers"""
    timers = db.query(PersonalSafetyTimer).filter(
        PersonalSafetyTimer.user_id == current_user.id,
        PersonalSafetyTimer.is_active == True,
        PersonalSafetyTimer.checked_in_at == None
    ).all()
    
    return [
        {
            "id": str(t.id),
            "started_at": t.started_at,
            "expected_end_at": t.expected_end_at,
            "remaining_minutes": max(0, (t.expected_end_at - datetime.utcnow()).total_seconds() / 60)
        }
        for t in timers
    ]
