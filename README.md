# Community Event Verification App (v2)

A production-ready, community-driven event verification platform with real-time capabilities, dual authentication (email/phone-OTP), and advanced safety features.

## Features

### Core Features
- **Event Reporting**: Report security incidents (assaults, theft, arson, missing persons) and normal events (outages, road issues, weather)
- **Real-Time Location Mapping**: Interactive map with live status updates (Green=validated, Red=invalidated, Yellow=pending)
- **Real-Time Verification**: Push notifications for nearby events, live voting with instant sync
- **Official Broadcasts**: Verified admin announcements with badges
- **Dual Authentication**: Email/password OR phone/OTP via Twilio/Firebase
- **Multimedia Support**: Photos, comments, live video streaming (WebRTC)

### MVP+ Features
- **Emergency SOS**: One-tap alerts with live location/video sharing
- **Live Video Verification**: Real-time streaming from event scenes
- **AI-Powered Aids**: Auto-categorization of events/images
- **Lost Pet Finder**: Dedicated module with photo matching
- **Gamification**: Leaderboards, badges, daily streaks
- **Analytics Dashboard**: Verification accuracy, hot spots visualization
- **Safe Walk Tracking**: Share live location during walks
- **QR Check-Ins**: For official events and checkpoints
- **Privacy Controls**: Anonymized reporting, data expiration

## Tech Stack

### Backend
- **Framework**: FastAPI with WebSockets and SSE
- **Database**: PostgreSQL + PostGIS (geospatial), MongoDB (media/logs)
- **Cache/PubSub**: Redis
- **Auth**: JWT, Twilio OTP, Firebase Auth
- **Real-Time**: WebSockets, FCM/Web Push

### Frontend
- **Framework**: React SPA
- **Maps**: React-Leaflet / Mapbox
- **State**: Redux Toolkit + Dexie.js (offline-first)
- **Real-Time**: WebSocket client, FCM integration
- **Video**: WebRTC for live streaming

### DevOps
- Docker & Docker Compose
- CI/CD ready
- Rate limiting & security headers

## Project Structure

```
/workspace
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Config, security
│   │   ├── db/           # Database connections
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── utils/        # Helpers
│   ├── tests/
│   └── migrations/
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom hooks
│   │   ├── services/     # API clients
│   │   ├── store/        # Redux store
│   │   └── utils/        # Utilities
│   └── public/
├── docs/
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- Node.js 18+

### Environment Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and configure:
   - Database credentials
   - Twilio credentials (for OTP)
   - Firebase credentials (for push notifications)
   - JWT secrets

### Running with Docker

```bash
docker-compose up --build
```

Services will be available at:
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432
- MongoDB: localhost:27017
- Redis: localhost:6379

### Manual Setup

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register with email or phone
- `POST /api/v1/auth/login` - Login with email/password
- `POST /api/v1/auth/otp/request` - Request OTP for phone
- `POST /api/v1/auth/otp/verify` - Verify OTP

### Events
- `GET /api/v1/events` - List events with filters
- `POST /api/v1/events` - Create new event
- `PUT /api/v1/events/{id}` - Update event
- `DELETE /api/v1/events/{id}` - Delete event
- `POST /api/v1/events/{id}/vote` - Vote on event verification

### Real-Time
- `WS /ws/events` - WebSocket for live updates
- `POST /api/v1/sos` - Emergency SOS alert

### Admin
- `GET /api/v1/admin/analytics` - Analytics dashboard
- `GET /api/v1/admin/leaderboard` - Gamification leaderboard

## Safety & Security

- OTP expires in 5 minutes with brute-force protection
- Rate limiting on all endpoints
- GDPR-compliant data handling
- Anonymized reporting options
- PII encryption at rest and in transit

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## License

MIT License

## Contributing

See CONTRIBUTING.md for guidelines.
