# Community Event Verification App - Advanced Features Documentation

## Overview
This document describes the advanced features implemented in version 2.0 of the Community Event Verification App, including automated event merging, lost & found modules, transport requests, analytics dashboards, and safety features.

---

## 🎯 New Features Implemented

### 1. Automated Event Merging & Duplicate Detection

**Purpose**: Prevents split verification when multiple users report the same incident.

**How it Works**:
- Automatically detects events within 50 meters and 5 minutes with the same category
- Uses PostGIS `ST_DWithin` for geospatial queries
- Moderators can merge duplicate events, consolidating all votes
- Notifies all reporters when their events are merged

**API Endpoints**:
```
POST /api/v1/advanced/events/{event_id}/check-duplicates
POST /api/v1/advanced/events/merge
```

**Database Fields Added**:
- `Event.duplicate_group_id`: UUID grouping merged events
- `Event.merged_into_id`: Reference to parent event
- `EventStatus.MERGED`: New status for merged events

---

### 2. Lost Documents Module

**Purpose**: Track and recover lost official documents (IDs, passports, licenses).

**Features**:
- Detailed document metadata (type, number, issuing authority)
- Privacy controls for sensitive information
- Search by document type and found status
- Reward escrow integration

**API Endpoints**:
```
POST /api/v1/advanced/lost-documents
GET /api/v1/advanced/lost-documents
PUT /api/v1/advanced/lost-documents/{doc_id}/found
```

**Database Model**: `LostDocument`
- Document type, number, issuing authority
- Holder name (partially hidden for privacy)
- Sensitive flag for extra privacy

---

### 3. Forgotten Items (Bags & Parcels)

**Purpose**: Report and claim forgotten bags, parcels, and personal items.

**Features**:
- Item categorization (bag, parcel, phone, wallet, etc.)
- Brand, color, size tracking
- Location description where item was left
- Claim workflow with verification

**API Endpoints**:
```
POST /api/v1/advanced/forgotten-items
GET /api/v1/advanced/forgotten-items
POST /api/v1/advanced/forgotten-items/{item_id}/claim
```

**Database Model**: `ForgottenItem`
- Item type, brand, color, size
- Contains valuables flag
- Claimed status

---

### 4. Transport Requests (Taxi & Bicycle)

**Purpose**: One-tap request for taxi or bicycle assistance based on location.

**Features**:
- Simple button press to request transport
- Current location auto-detected
- Destination selection
- Urgency levels (normal, urgent, emergency)
- Provider/driver matching system
- Real-time status updates

**API Endpoints**:
```
POST /api/v1/advanced/transport-requests
GET /api/v1/advanced/transport-requests/open
POST /api/v1/advanced/transport-requests/{request_id}/accept
POST /api/v1/advanced/transport-requests/{request_id}/complete
```

**Request Flow**:
1. User presses "Need Taxi" or "Need Bicycle" button
2. App captures current GPS location
3. User optionally sets destination
4. Request broadcast to nearby providers
5. Provider accepts and picks up passenger
6. Trip completion with optional rating

**Database Model**: `TransportRequest`
- Request type (taxi/bicycle)
- Pickup and destination coordinates
- Passenger count, luggage info
- Special requirements (wheelchair, child seat)
- Status tracking (pending → accepted → in_progress → completed)

---

### 5. Trust & Safety Escrow for Rewards

**Purpose**: Secure reward payments for lost item recovery via Stripe Connect.

**Features**:
- Reward amount held in escrow
- Auto-release upon mutual confirmation
- Prevents scams and fraud
- Incentivizes honest returns

**API Endpoints**:
```
POST /api/v1/advanced/rewards/escrow/create
POST /api/v1/advanced/rewards/escrow/{escrow_id}/release
```

**Database Model**: `RewardEscrow`
- Amount and currency
- Stripe Payment Intent ID
- Status: PENDING → HELD → RELEASED/REFUNDED

**Production Integration**:
```python
# Create Stripe escrow
stripe_payment_intent = stripe.PaymentIntent.create(
    amount=amount_cents,
    currency=currency,
    payment_method_types=['card'],
    capture_method='manual'  # Hold funds
)

# Release after confirmation
stripe.Transfer.create(
    amount=amount_cents,
    destination=finder_stripe_account
)
```

---

### 6. Custom Geofenced Alert Subscriptions

**Purpose**: Users draw custom zones (e.g., school, home) and receive alerts for events inside.

**Features**:
- Polygon drawing on map
- Multiple notification types per zone
- Works regardless of user's current location
- Instant push notifications

**API Endpoints**:
```
POST /api/v1/advanced/geofences
GET /api/v1/advanced/geofences
```

**Database Model**: `GeofenceSubscription`
- PostGIS POLYGON geometry
- Notification type filters
- Active/inactive toggle

**Usage Example**:
```javascript
// Frontend: Draw polygon on map
const coords = [
  [-73.9857, 40.7484],  // Corner 1
  [-73.9847, 40.7484],  // Corner 2
  [-73.9847, 40.7494],  // Corner 3
  [-73.9857, 40.7494]   // Corner 4
];

// Send to backend
fetch('/api/v1/advanced/geofences', {
  method: 'POST',
  body: JSON.stringify({
    name: "Child's School Zone",
    polygon_coords: coords,
    notification_types: ["security", "missing_person"]
  })
});
```

---

### 7. Infrastructure Repair Tracker

**Purpose**: Track non-emergency infrastructure issues (potholes, traffic lights) through municipal repair.

**Features**:
- Separate from emergency events
- Municipal workflow: REPORTED → ACKNOWLEDGED → IN_PROGRESS → FIXED
- Department assignment
- Public accountability dashboard
- Before/after photos

**Categories**:
- Potholes
- Traffic light malfunctions
- Street light outages

**API Endpoints**:
```
POST /api/v1/advanced/infrastructure/{event_id}
PUT /api/v1/advanced/infrastructure/{issue_id}/status
GET /api/v1/analytics/infrastructure/status
```

**Database Model**: `InfrastructureIssue`
- Issue type and priority
- Municipal status enum
- Assigned department
- Estimated and actual fix dates

---

### 8. Emergency Resource Tracker

**Purpose**: Real-time hospital/shelter capacity during disasters.

**Features**:
- Live bed availability
- Occupancy rates
- Services offered (emergency, trauma, pediatric)
- Official-only updates
- Filter by resource type

**API Endpoints**:
```
GET /api/v1/advanced/emergency-resources
PUT /api/v1/advanced/emergency-resources/{resource_id}/capacity
```

**Database Model**: `EmergencyResource`
- Resource type (hospital, shelter, fire_station, police)
- Total capacity and current availability
- Occupancy rate calculation
- Services array

**Use Case**:
During earthquake, users can see:
- Nearest hospital with available beds
- Open emergency shelters
- Real-time occupancy to avoid overcrowding

---

### 9. Personal Safety Timer (Check-In)

**Purpose**: Automatic alert if user doesn't check in after solo walk.

**Features**:
- Set expected duration
- Emergency contacts notified on timeout
- Manual check-in cancels timer
- Silent SOS to nearby users if expired

**API Endpoints**:
```
POST /api/v1/advanced/safety-timer/start
POST /api/v1/advanced/safety-timer/{timer_id}/check-in
GET /api/v1/advanced/safety-timer/active
```

**Database Model**: `PersonalSafetyTimer`
- Expected duration
- Emergency contact list
- Start/end locations
- Check-in timestamp

**Workflow**:
1. User starts timer before walking home
2. Sets duration (e.g., 30 minutes)
3. Adds emergency contacts
4. If no check-in by deadline:
   - Auto-share location with contacts
   - Trigger silent SOS to nearby users

---

### 10. Reputation-Based Verification Weight

**Purpose**: Trusted users' votes count more to prevent spam/troll voting.

**Implementation**:
```python
# Vote weight calculation
effective_vote = 1 + floor(user.reputation_points / 500)

# Example:
# User with 0 rep → weight = 1.0
# User with 500 rep → weight = 2.0
# User with 1500 rep → weight = 4.0
```

**Database Changes**:
- `Vote.weight`: Float field for weighted votes
- `Event.weighted_score`: Sum of weighted votes

**Benefits**:
- Reduces impact of new/spam accounts
- Rewards consistent, accurate contributors
- More resilient to coordinated manipulation

---

## 📊 Analytics Dashboard Features

### Overview Metrics
```
GET /api/v1/analytics/overview?days=30
```
Returns:
- Total events by status and category
- Verification statistics
- Active user counts
- Top contributors leaderboard

### Geographical Heatmap
```
GET /api/v1/analytics/heatmap?days=7&grid_size_meters=500
```
- GeoJSON output for map visualization
- Event density by grid cell
- Configurable grid resolution

### Safety Scores
```
GET /api/v1/analytics/safety-scores
POST /api/v1/analytics/safety-scores/recalculate
```
- Dynamic 0-100 score per neighborhood grid
- Based on:
  - Recent incident count (last 24h)
  - Validation rate
  - Average response time
- Formula: `100 - incident_penalty + validation_bonus`

### Predictive Hotspots (AI)
```
GET /api/v1/analytics/predictive-hotspots
POST /api/v1/analytics/predictive-hotspots/generate
```
- ML-based risk prediction (Prophet/LSTM in production)
- Factors: historical patterns, time, day of week, weather
- Confidence scores
- Semi-transparent overlays on map

### Verification Accuracy
```
GET /api/v1/analytics/verification-accuracy?days=30
```
- Identifies disputed events (close votes)
- Flags suspicious users (>50% invalidation rate)
- Provides moderation recommendations

### Time-Series Analytics
```
GET /api/v1/analytics/time-series?metric=events&granularity=day&days=30
```
- Trend analysis for events, votes, users
- Configurable granularity (hour/day/week/month)
- Category filtering

---

## 🗄️ Database Schema Additions

### New Tables
1. **LostDocument** - Lost IDs, passports, certificates
2. **ForgottenItem** - Bags, parcels, phones, wallets
3. **TransportRequest** - Taxi/bicycle requests
4. **RewardEscrow** - Stripe escrow for rewards
5. **GeofenceSubscription** - Custom alert zones
6. **SafetyScore** - Neighborhood safety metrics
7. **PredictiveHotspot** - AI risk predictions
8. **InfrastructureIssue** - Municipal repair tracking
9. **EmergencyResource** - Hospital/shelter capacity
10. **PersonalSafetyTimer** - Check-in timers

### Enhanced Tables
- **Event**: Added `duplicate_group_id`, `merged_into_id`, `weighted_score`, `ai_summary`
- **Vote**: Added `weight` field for reputation-based scoring
- **User**: Added `geofences` relationship

---

## 🔧 Technical Implementation Details

### PostGIS Queries Used

**Duplicate Detection**:
```sql
SELECT * FROM events
WHERE ST_DWithin(
  location,
  ST_MakePoint(:lon, :lat),
  50  -- 50 meters
)
AND category = :category
AND created_at >= NOW() - INTERVAL '5 minutes'
```

**Heatmap Generation**:
```sql
SELECT 
  ST_SnapToGrid(location, 0.005, 0.005) as grid_cell,
  COUNT(*) as event_count
FROM events
GROUP BY grid_cell
```

**Geofence Matching**:
```sql
SELECT * FROM geofence_subscriptions
WHERE ST_Within(
  ST_MakePoint(:event_lon, :event_lat),
  polygon
)
```

### Background Tasks (Celery Beat)

**Scheduled Jobs**:
1. **Recalculate Safety Scores** - Every hour
2. **Generate Predictive Hotspots** - Daily at midnight
3. **Check Safety Timers** - Every 5 minutes
4. **Expire Old Events** - Daily
5. **Send Geofence Alerts** - On new event creation

### WebSocket Real-Time Updates

**Events**:
- Vote count changes
- Event status updates
- New events in user's area
- Transport request acceptances

**Example**:
```python
@websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Broadcast vote update
            await manager.broadcast({
                "type": "vote_update",
                "event_id": data["event_id"],
                "yes_votes": new_yes,
                "no_votes": new_no
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

---

## 🚀 Frontend Integration Guide

### Transport Request Button
```jsx
import { NeuButton } from './components/UIComponents';

function TransportRequestPanel({ location }) {
  const requestTransport = async (type) => {
    const response = await fetch('/api/v1/advanced/transport-requests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_id: currentEventId,
        request_type: type,
        pickup_latitude: location.lat,
        pickup_longitude: location.lng,
        urgency: 'normal'
      })
    });
    
    // Show success animation
    showToast(`🚕 ${type} requested! Driver will arrive soon.`);
  };
  
  return (
    <div className="neu-card animate-slide-up">
      <h3>Need a Ride?</h3>
      <NeuButton 
        variant="primary" 
        icon="🚕"
        onClick={() => requestTransport('taxi')}
      >
        Request Taxi
      </NeuButton>
      <NeuButton 
        variant="secondary" 
        icon="🚲"
        onClick={() => requestTransport('bicycle')}
      >
        Request Bicycle
      </NeuButton>
    </div>
  );
}
```

### Lost Item Report Form
```jsx
function LostDocumentForm({ eventId }) {
  const [formData, setFormData] = useState({
    document_type: '',
    holder_name: '',
    contact_info: '',
    is_sensitive: true
  });
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    await fetch('/api/v1/advanced/lost-documents', {
      method: 'POST',
      body: JSON.stringify({ ...formData, event_id: eventId })
    });
  };
  
  return (
    <form onSubmit={handleSubmit} className="glass-panel p-6">
      <select 
        value={formData.document_type}
        onChange={(e) => setFormData({...formData, document_type: e.target.value})}
        className="neu-input"
      >
        <option>ID Card</option>
        <option>Passport</option>
        <option>Driver's License</option>
        <option>Certificate</option>
      </select>
      
      <NeuInput
        placeholder="Holder's Name"
        value={formData.holder_name}
        onChange={(e) => setFormData({...formData, holder_name: e.target.value})}
      />
      
      <button type="submit" className="neu-btn neu-btn-primary">
        Report Lost Document
      </button>
    </form>
  );
}
```

### Safety Score Heatmap Layer
```jsx
import { MapContainer, GeoJSON } from 'react-leaflet';

function SafetyHeatmapLayer() {
  const [geoData, setGeoData] = useState(null);
  
  useEffect(() => {
    fetch('/api/v1/analytics/heatmap?days=7')
      .then(res => res.json())
      .then(data => setGeoData(data));
  }, []);
  
  return geoData ? (
    <GeoJSON
      data={geoData}
      style={(feature) => ({
        fillColor: getColor(feature.properties.intensity),
        weight: 0,
        fillOpacity: feature.properties.intensity * 0.6
      })}
    />
  ) : null;
}

function getColor(intensity) {
  return intensity > 0.8 ? '#ff0000' :
         intensity > 0.5 ? '#ffa500' :
         intensity > 0.2 ? '#ffff00' : '#00ff00';
}
```

---

## 🔐 Security Considerations

### Privacy Protections
- Lost document holder names partially masked
- Sensitive documents marked with `is_sensitive` flag
- Anonymous reporting option preserved
- GDPR-compliant data expiration

### Access Control
- Event merging: Admin/Moderator only
- Infrastructure status updates: Official/Admin only
- Emergency resource updates: Official/Admin only
- Predictive hotspot generation: Admin only

### Rate Limiting
- Transport requests: 5 per hour per user
- Safety timer starts: 3 concurrent max
- Escrow creation: Verified users only

---

## 📈 Performance Optimizations

### Database Indexes
```sql
CREATE INDEX idx_events_location ON events USING GIST (location);
CREATE INDEX idx_events_created_at ON events (created_at DESC);
CREATE INDEX idx_events_category_status ON events (category, status);
CREATE INDEX idx_transport_requests_status ON transport_requests (status);
CREATE INDEX idx_geofences_user ON geofence_subscriptions (user_id, is_active);
```

### Caching Strategy (Redis)
- Safety scores: Cache for 1 hour
- Heatmap data: Cache for 15 minutes
- Leaderboard: Cache for 30 minutes
- User reputation: Cache for 5 minutes

### Query Optimization
- Use materialized views for complex aggregations
- Pagination on all list endpoints
- Lazy loading for nested relationships

---

## 🧪 Testing Recommendations

### Unit Tests
```python
def test_duplicate_detection():
    # Create two events 30m apart, 2 minutes apart
    event1 = create_event(lat=40.7128, lng=-74.0060)
    event2 = create_event(lat=40.7130, lng=-74.0062)
    
    # Should detect as duplicates
    duplicates = check_duplicates(event2.id)
    assert len(duplicates['potential_duplicates']) == 1

def test_reputation_vote_weight():
    user = create_user(reputation_points=1000)
    vote = create_vote(user=user, vote_type='yes')
    assert vote.weight == 3.0  # 1 + floor(1000/500)
```

### Integration Tests
- Full transport request workflow
- Escrow creation and release
- Geofence alert triggering
- Safety timer expiry and alert

### Load Testing
- 1000 concurrent WebSocket connections
- 100 events/second ingestion
- Geospatial query performance under load

---

## 🎉 Future Enhancements

### Planned Features
1. **AR Event Overlay** - Camera view with floating pins
2. **Voice Reporting** - "Report theft at 5th and Main"
3. **Disaster Mode** - Bluetooth mesh networking offline
4. **Video AI Summaries** - Whisper + GPT-4V for live streams
5. **Crowd-Sourced Traffic** - Real-time traffic light sync

### ML Improvements
- Train LSTM model on 1 year of historical data
- Integrate weather API for predictions
- Anomaly detection for unusual event spikes

---

## 📞 Support & Documentation

- **API Docs**: `/docs` (Swagger UI)
- **Redoc**: `/redoc`
- **GitHub**: [Repository Link]
- **Discord**: [Community Server]

---

**Version**: 2.0.0  
**Last Updated**: 2024  
**License**: MIT
