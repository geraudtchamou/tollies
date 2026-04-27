from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Float, Text, JSON, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid
import enum
from app.db.session import Base


class UserRole(enum.Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    OFFICIAL = "official"


class EventCategory(enum.Enum):
    # Security events
    ASSAULT = "assault"
    THEFT = "theft"
    ARSON = "arson"
    MISSING_PERSON = "missing_person"
    # Normal events
    POWER_OUTAGE = "power_outage"
    WATER_OUTAGE = "water_outage"
    ROAD_ISSUE = "road_issue"
    TRANSPORT_NEED = "transport_need"
    WEATHER = "weather"
    CHECKPOINT = "checkpoint"
    LOST_ITEM = "lost_item"
    LOST_PET = "lost_pet"
    # New categories for lost/found
    LOST_DOCUMENT = "lost_document"
    FORGOTTEN_BAG = "forgotten_bag"
    FORGOTTEN_PARCEL = "forgotten_parcel"
    # Transport requests
    TAXI_NEEDED = "taxi_needed"
    BICYCLE_NEEDED = "bicycle_needed"
    # Infrastructure
    POTHOLE = "pothole"
    TRAFFIC_LIGHT_ISSUE = "traffic_light_issue"
    STREET_LIGHT_ISSUE = "street_light_issue"
    OTHER = "other"


class EventStatus(enum.Enum):
    PENDING = "pending"  # Yellow
    VALIDATED = "validated"  # Green
    INVALIDATED = "invalidated"  # Red
    MERGED = "merged"  # Merged into another event
    RESOLVED = "resolved"  # Issue fixed


class RewardEscrowStatus(enum.Enum):
    PENDING = "pending"
    HELD = "held"
    RELEASED = "released"
    REFUNDED = "refunded"


class TransportRequestStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MunicipalStatus(enum.Enum):
    REPORTED = "reported"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=True)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)
    otp_code = Column(String(6))
    otp_expires_at = Column(DateTime(timezone=True))
    otp_attempts = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    reputation_points = Column(Integer, default=0)
    avatar_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Privacy settings
    is_anonymous = Column(Boolean, default=False)
    location_sharing_enabled = Column(Boolean, default=True)


class Event(Base):
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(Enum(EventCategory), nullable=False)
    status = Column(Enum(EventStatus), default=EventStatus.PENDING)
    
    # Location - using PostGIS
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry('POINT', srid=4326))
    address = Column(String(500))
    
    # User references
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Verification with reputation weighting
    yes_votes = Column(Integer, default=0)
    no_votes = Column(Integer, default=0)
    verification_threshold = Column(Integer, default=5)
    weighted_score = Column(Float, default=0.0)  # Reputation-weighted score
    
    # Duplicate detection & merging
    duplicate_group_id = Column(UUID(as_uuid=True), nullable=True)  # Groups similar events
    merged_into_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=True)
    
    # Multimedia
    media_urls = Column(JSON, default=list)  # Array of image/video URLs
    has_live_stream = Column(Boolean, default=False)
    ai_summary = Column(Text, nullable=True)  # AI-generated summary of video/content
    
    # Official broadcast
    is_official_broadcast = Column(Boolean, default=False)
    
    # SOS emergency
    is_sos = Column(Boolean, default=False)
    
    # Metadata
    views = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))  # Auto-expire old events


class Vote(Base):
    __tablename__ = "votes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    vote_type = Column(String(3))  # 'yes' or 'no'
    weight = Column(Float, default=1.0)  # Reputation-based weight
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        # Prevent duplicate votes per user per event
        UniqueConstraint('event_id', 'user_id', name='unique_user_event_vote'),
    )


class LiveStream(Base):
    __tablename__ = "live_streams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    stream_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    viewer_count = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))


class SafeWalk(Base):
    __tablename__ = "safe_walks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    companion_ids = Column(JSON, default=list)  # Array of user IDs
    start_location = Column(Geometry('POINT', srid=4326))
    end_location = Column(Geometry('POINT', srid=4326))
    route = Column(JSON, default=list)  # Array of coordinates
    is_active = Column(Boolean, default=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    alert_triggered = Column(Boolean, default=False)


class Badge(Base):
    __tablename__ = "badges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    icon_url = Column(String(500))
    criteria = Column(JSON)  # Requirements to earn badge


class UserBadge(Base):
    __tablename__ = "user_badges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())


class LostPet(Base):
    __tablename__ = "lost_pets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    pet_name = Column(String(100))
    pet_type = Column(String(50))  # dog, cat, etc.
    breed = Column(String(100))
    color = Column(String(50))
    last_seen_location = Column(Geometry('POINT', srid=4326))
    photo_urls = Column(JSON, default=list)
    contact_info = Column(String(255))
    is_found = Column(Boolean, default=False)


class LostDocument(Base):
    __tablename__ = "lost_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    document_type = Column(String(100))  # ID, passport, license, certificate, etc.
    document_number = Column(String(100))  # Optional, can be partial
    issuing_authority = Column(String(200))
    issue_date = Column(DateTime(timezone=True))
    expiry_date = Column(DateTime(timezone=True))
    holder_name = Column(String(200))
    description = Column(Text)
    photo_urls = Column(JSON, default=list)
    contact_info = Column(String(255))
    is_found = Column(Boolean, default=False)
    is_sensitive = Column(Boolean, default=True)  # For privacy handling


class ForgottenItem(Base):
    __tablename__ = "forgotten_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    item_type = Column(String(100))  # bag, parcel, phone, wallet, etc.
    brand = Column(String(100))
    color = Column(String(50))
    size = Column(String(50))
    description = Column(Text)
    location_description = Column(String(500))  # Where it was left
    photo_urls = Column(JSON, default=list)
    contact_info = Column(String(255))
    is_claimed = Column(Boolean, default=False)
    contains_valuables = Column(Boolean, default=False)


class TransportRequest(Base):
    __tablename__ = "transport_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    request_type = Column(String(20))  # 'taxi' or 'bicycle'
    passenger_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Route information
    pickup_latitude = Column(Float, nullable=False)
    pickup_longitude = Column(Float, nullable=False)
    pickup_address = Column(String(500))
    destination_latitude = Column(Float)
    destination_longitude = Column(Float)
    destination_address = Column(String(500))
    route = Column(JSON, default=list)  # Array of coordinates
    
    # Request details
    urgency = Column(String(20), default="normal")  # normal, urgent, emergency
    passengers_count = Column(Integer, default=1)
    luggage_info = Column(String(200))
    special_requirements = Column(Text)  # wheelchair, child seat, etc.
    
    # Status
    status = Column(String(20), default="pending")  # pending, accepted, in_progress, completed, cancelled
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Driver/provider
    provider_rating = Column(Float)  # Rating given to provider
    
    # Timing
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True))
    picked_up_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Pricing (optional)
    estimated_price = Column(Float)
    final_price = Column(Float)


class RewardEscrow(Base):
    """Stripe escrow for lost item rewards"""
    __tablename__ = "reward_escrows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    requester_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    stripe_payment_intent_id = Column(String(255), unique=True)
    status = Column(Enum(RewardEscrowStatus), default=RewardEscrowStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    released_at = Column(DateTime(timezone=True))
    refunded_at = Column(DateTime(timezone=True))


class GeofenceSubscription(Base):
    """Custom geofenced alert subscriptions"""
    __tablename__ = "geofence_subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)  # e.g., "School Zone"
    polygon = Column(Geometry('POLYGON', srid=4326), nullable=False)
    notification_types = Column(ARRAY(String), default=["security", "missing_person"])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SafetyScore(Base):
    """Community safety scores for grid cells"""
    __tablename__ = "safety_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grid_cell_id = Column(String(100), nullable=False, unique=True)  # H3 index or custom grid
    center_lat = Column(Float)
    center_lng = Column(Float)
    score = Column(Float, default=50.0)  # 0-100
    incident_count_24h = Column(Integer, default=0)
    validation_rate = Column(Float, default=0.0)
    response_time_avg = Column(Float)  # Average verification time
    last_updated = Column(DateTime(timezone=True), server_default=func.now())


class PredictiveHotspot(Base):
    """AI-predicted risk hotspots"""
    __tablename__ = "predictive_hotspots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    radius_meters = Column(Integer, default=500)
    risk_level = Column(Float, nullable=False)  # 0.0 to 1.0
    predicted_event_type = Column(String(100))
    confidence_score = Column(Float)
    prediction_time = Column(DateTime(timezone=True), nullable=False)
    factors = Column(JSON)  # Contributing factors (time, weather, historical)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InfrastructureIssue(Base):
    """Track infrastructure repair status"""
    __tablename__ = "infrastructure_issues"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    issue_type = Column(String(100), nullable=False)  # pothole, traffic_light, street_light
    municipal_status = Column(Enum(MunicipalStatus), default=MunicipalStatus.REPORTED)
    assigned_department = Column(String(200))
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    estimated_fix_date = Column(DateTime(timezone=True))
    fixed_at = Column(DateTime(timezone=True))
    fix_photo_urls = Column(JSON, default=list)  # Photos after repair
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EmergencyResource(Base):
    """Hospital/shelter capacity tracking"""
    __tablename__ = "emergency_resources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    resource_type = Column(String(50), nullable=False)  # hospital, shelter, fire_station, police
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    address = Column(String(500))
    contact_phone = Column(String(20))
    
    # Capacity tracking
    total_capacity = Column(Integer)
    current_availability = Column(Integer)
    occupancy_rate = Column(Float)  # 0.0 to 1.0
    
    # Services offered
    services = Column(ARRAY(String))  # e.g., ["emergency", "trauma", "pediatric"]
    
    is_operational = Column(Boolean, default=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Official who updated


class PersonalSafetyTimer(Base):
    """Check-in timer for solo walks"""
    __tablename__ = "personal_safety_timers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expected_duration_minutes = Column(Integer, nullable=False)
    emergency_contact_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)
    start_location = Column(Geometry('POINT', srid=4326))
    end_location = Column(Geometry('POINT', srid=4326))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    expected_end_at = Column(DateTime(timezone=True), nullable=False)
    checked_in_at = Column(DateTime(timezone=True))  # User manually checked in
    auto_alert_triggered = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
