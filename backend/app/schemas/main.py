"""
Pydantic Schemas for Request/Response Validation
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

# Enums matching the database
class UserRole(str, Enum):
    user = "user"
    moderator = "moderator"
    admin = "admin"
    official = "official"

class EventStatus(str, Enum):
    pending = "pending"
    validated = "validated"
    invalidated = "invalidated"
    resolved = "resolved"

class EventType(str, Enum):
    security = "security"
    normal = "normal"
    lost_found = "lost_found"
    transport = "transport"
    infrastructure = "infrastructure"

class TransportType(str, Enum):
    taxi = "taxi"
    bicycle = "bicycle"

class LostItemType(str, Enum):
    document = "document"
    bag_parcel = "bag_parcel"
    person = "person"
    pet = "pet"
    other = "other"

# Auth Schemas
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    
class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.user

class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    otp: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID

class MessageResponse(BaseModel):
    message: str
    count: Optional[int] = None
    request_id: Optional[str] = None

# Event Schemas
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: EventType
    sub_category: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    media_urls: Optional[List[str]] = []

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    id: UUID
    status: EventStatus
    reporter_id: UUID
    view_count: int
    like_count: int
    comment_count: int
    vote_yes: int
    vote_no: int
    created_at: datetime
    updated_at: datetime
    extra_data: Optional[Dict[str, Any]] = {}
    
    class Config:
        from_attributes = True

class VoteCreate(BaseModel):
    vote_type: str  # "yes" or "no"

# Comment Schemas
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[UUID] = None

class CommentResponse(BaseModel):
    id: UUID
    event_id: UUID
    user_id: UUID
    content: str
    parent_id: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Preference Schemas
class PreferenceUpdate(BaseModel):
    preferred_categories: Optional[List[str]] = None
    preferred_locations: Optional[List[Dict[str, Any]]] = None
    notification_enabled: Optional[bool] = None

# Transport Request Schemas
class TransportRequestCreate(BaseModel):
    type: TransportType
    pickup_lat: float = Field(..., ge=-90, le=90)
    pickup_lng: float = Field(..., ge=-180, le=180)
    dest_lat: Optional[float] = Field(None, ge=-90, le=90)
    dest_lng: Optional[float] = Field(None, ge=-180, le=180)
    destination_address: Optional[str] = None
    passengers: int = Field(default=1, ge=1, le=8)
    notes: Optional[str] = None

class TransportRequestResponse(BaseModel):
    id: UUID
    requester_id: UUID
    type: TransportType
    status: str
    pickup_lat: float
    pickup_lng: float
    dest_lat: Optional[float]
    dest_lng: Optional[float]
    destination_address: Optional[str]
    passengers: int
    provider_id: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Lost Item Schemas
class LostItemCreate(BaseModel):
    item_type: LostItemType
    is_lost: bool = True
    description: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    brand: Optional[str] = None
    color: Optional[str] = None
    date_lost: Optional[datetime] = None
    reward_amount: float = Field(default=0.0, ge=0)
    person_name: Optional[str] = None
    age_estimate: Optional[int] = Field(None, ge=0, le=120)
    last_seen_location: Optional[str] = None

class LostItemResponse(BaseModel):
    id: UUID
    event_id: UUID
    item_type: LostItemType
    is_lost: bool
    status: str
    description: Optional[str]
    brand: Optional[str]
    color: Optional[str]
    reward_amount: float
    person_name: Optional[str]
    age_estimate: Optional[int]
    last_seen_location: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Analytics Schemas
class DashboardOverview(BaseModel):
    total_events: int
    new_users: int
    total_users: int
    engagement: Dict[str, int]
    status_breakdown: Dict[str, int]
    category_breakdown: Dict[str, int]
    verification_accuracy: float

class TimeSeriesData(BaseModel):
    date: str
    count: int

class HeatmapCell(BaseModel):
    lat: float
    lng: float
    total: int
    security: int
    validated: int
    invalidated: int
    safety_score: int

class Contributor(BaseModel):
    user_id: str
    identifier: str
    reputation: int
    votes: int
    comments: int
    events_reported: int
