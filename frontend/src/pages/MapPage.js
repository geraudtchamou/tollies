import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { useDispatch, useSelector } from 'react-redux';
import { fetchEvents, createEvent, voteOnEvent, setSelectedEvent, setFilters } from '../../store/slices/eventsSlice';
import websocketService from '../../services/websocket';
import 'leaflet/dist/leaflet.css';

// Fix for default marker icon in React-Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const MapPage = () => {
  const dispatch = useDispatch();
  const { events, selectedEvent, filters } = useSelector((state) => state.events);
  const { user, isAuthenticated } = useSelector((state) => state.auth);
  
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportLocation, setReportLocation] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [viewMode, setViewMode] = useState('all'); // 'all', 'sos', 'validated', 'pending'
  const [selectedCategory, setSelectedCategory] = useState(null);

  // Event categories with icons and colors
  const categoryConfig = {
    assault: { color: '#dc3545', icon: '🚨', label: 'Assault' },
    theft: { color: '#fd7e14', icon: '👤', label: 'Theft' },
    arson: { color: '#dc3545', icon: '🔥', label: 'Arson' },
    missing_person: { color: '#ffc107', icon: '❓', label: 'Missing Person' },
    power_outage: { color: '#6c757d', icon: '💡', label: 'Power Outage' },
    water_outage: { color: '#17a2b8', icon: '💧', label: 'Water Outage' },
    road_issue: { color: '#6c757d', icon: '🚧', label: 'Road Issue' },
    transport_need: { color: '#007bff', icon: '🚌', label: 'Transport Need' },
    weather: { color: '#17a2b8', icon: '🌦️', label: 'Weather' },
    checkpoint: { color: '#28a745', icon: '✅', label: 'Checkpoint' },
    lost_item: { color: '#6f42c1', icon: '🎒', label: 'Lost Item' },
    lost_pet: { color: '#e83e8c', icon: '🐕', label: 'Lost Pet' },
    other: { color: '#6c757d', icon: '📍', label: 'Other' },
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'validated': return '#28a745'; // Green
      case 'invalidated': return '#dc3545'; // Red
      case 'pending': return '#ffc107'; // Yellow
      default: return '#6c757d';
    }
  };

  // Location tracker component
  function LocationTracker() {
    useMapEvents({
      locationfound(e) {
        setUserLocation(e.latlng);
        if (user && user.id) {
          websocketService.updateLocation(user.id, e.latlng.lat, e.latlng.lng);
        }
      },
    });
    return null;
  }

  useEffect(() => {
    // Connect to WebSocket
    if (user && user.id) {
      websocketService.connect(user.id);
      
      // Listen for real-time updates
      const unsubscribe = websocketService.addListener((message) => {
        console.log('WS Message:', message);
        if (message.type === 'live_feed' || message.type === 'event_update') {
          dispatch(fetchEvents(filters));
        }
      });

      return () => {
        unsubscribe();
        websocketService.disconnect();
      };
    }
  }, [user]);

  useEffect(() => {
    // Fetch initial events
    dispatch(fetchEvents(filters));
  }, []);

  const handleMapClick = (e) => {
    if (isAuthenticated) {
      setReportLocation(e.latlng);
      setShowReportModal(true);
    }
  };

  const handleCreateEvent = async (eventData) => {
    try {
      await dispatch(createEvent({
        ...eventData,
        latitude: reportLocation.lat,
        longitude: reportLocation.lng,
      })).unwrap();
      setShowReportModal(false);
      setReportLocation(null);
      dispatch(fetchEvents(filters));
    } catch (error) {
      console.error('Failed to create event:', error);
    }
  };

  const handleVote = async (eventId, voteType) => {
    try {
      await dispatch(voteOnEvent({ eventId, voteType })).unwrap();
      dispatch(fetchEvents(filters));
    } catch (error) {
      console.error('Failed to vote:', error);
    }
  };

  const filteredEvents = events.filter(event => {
    if (viewMode === 'sos' && !event.is_sos) return false;
    if (viewMode === 'validated' && event.status !== 'validated') return false;
    if (viewMode === 'pending' && event.status !== 'pending') return false;
    if (selectedCategory && event.category !== selectedCategory) return false;
    return true;
  });

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <h1 style={styles.logo}>🛡️ Community Safety</h1>
        <div style={styles.headerActions}>
          <button onClick={() => window.location.href='/sos'} style={styles.sosButton}>
            🚨 SOS
          </button>
          <button onClick={() => window.location.href='/leaderboard'} style={styles.actionButton}>
            🏆 Leaderboard
          </button>
          {user && (
            <span style={styles.userInfo}>
              👤 {user.email?.split('@')[0] || user.phone?.slice(-4) || 'User'} 
              ({user.reputation_points} pts)
            </span>
          )}
        </div>
      </header>

      {/* Filters */}
      <div style={styles.filters}>
        <div style={styles.filterGroup}>
          <button
            style={{ ...styles.filterBtn, ...(viewMode === 'all' ? styles.activeFilter : {}) }}
            onClick={() => setViewMode('all')}
          >
            All Events
          </button>
          <button
            style={{ ...styles.filterBtn, ...(viewMode === 'sos' ? styles.activeFilter : {}) }}
            onClick={() => setViewMode('sos')}
          >
            🚨 SOS Only
          </button>
          <button
            style={{ ...styles.filterBtn, ...(viewMode === 'validated' ? styles.activeFilter : {}) }}
            onClick={() => setViewMode('validated')}
          >
            ✅ Validated
          </button>
          <button
            style={{ ...styles.filterBtn, ...(viewMode === 'pending' ? styles.activeFilter : {}) }}
            onClick={() => setViewMode('pending')}
          >
            ⏳ Pending
          </button>
        </div>
        
        <select
          value={selectedCategory || ''}
          onChange={(e) => setSelectedCategory(e.target.value || null)}
          style={styles.categorySelect}
        >
          <option value="">All Categories</option>
          {Object.entries(categoryConfig).map(([key, config]) => (
            <option key={key} value={key}>{config.icon} {config.label}</option>
          ))}
        </select>
      </div>

      {/* Map */}
      <div style={styles.mapContainer}>
        <MapContainer
          center={[40.7128, -74.0060]}
          zoom={13}
          style={styles.map}
          onClick={handleMapClick}
        >
          <LocationTracker />
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
          />
          
          {/* User location marker */}
          {userLocation && (
            <Marker position={userLocation}>
              <Popup>You are here</Popup>
            </Marker>
          )}
          
          {/* Event markers */}
          {filteredEvents.map(event => {
            const category = categoryConfig[event.category] || categoryConfig.other;
            const statusColor = getStatusColor(event.status);
            
            return (
              <Marker
                key={event.id}
                position={[event.latitude, event.longitude]}
                icon={L.divIcon({
                  className: 'custom-marker',
                  html: `
                    <div style="
                      background-color: ${statusColor};
                      border: 3px solid white;
                      border-radius: 50%;
                      width: 30px;
                      height: 30px;
                      display: flex;
                      align-items: center;
                      justify-content: center;
                      font-size: 16px;
                      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                    ">
                      ${category.icon}
                    </div>
                  `,
                  iconSize: [30, 30],
                  iconAnchor: [15, 15],
                })}
              >
                <Popup>
                  <div style={styles.popupContent}>
                    <h3 style={styles.popupTitle}>{event.title}</h3>
                    <p style={styles.popupCategory}>
                      {category.icon} {category.label}
                    </p>
                    <p style={styles.popupDescription}>{event.description}</p>
                    <div style={styles.popupStats}>
                      <span style={{ color: '#28a745' }}>👍 {event.yes_votes}</span>
                      <span style={{ color: '#dc3545' }}>👎 {event.no_votes}</span>
                    </div>
                    <div style={styles.popupStatus}>
                      Status: <strong style={{ color: statusColor }}>{event.status}</strong>
                    </div>
                    {isAuthenticated && selectedEvent?.id !== event.id && (
                      <div style={styles.popupActions}>
                        <button
                          onClick={() => handleVote(event.id, 'yes')}
                          style={styles.voteBtnYes}
                        >
                          Yes
                        </button>
                        <button
                          onClick={() => handleVote(event.id, 'no')}
                          style={styles.voteBtnNo}
                        >
                          No
                        </button>
                      </div>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>

      {/* Report Modal */}
      {showReportModal && (
        <ReportModal
          location={reportLocation}
          onClose={() => { setShowReportModal(false); setReportLocation(null); }}
          onSubmit={handleCreateEvent}
          categoryConfig={categoryConfig}
        />
      )}

      {/* Legend */}
      <div style={styles.legend}>
        <h4>Legend</h4>
        <div style={styles.legendItem}>
          <span style={{ ...styles.legendDot, backgroundColor: '#28a745' }}></span>
          Validated
        </div>
        <div style={styles.legendItem}>
          <span style={{ ...styles.legendDot, backgroundColor: '#ffc107' }}></span>
          Pending
        </div>
        <div style={styles.legendItem}>
          <span style={{ ...styles.legendDot, backgroundColor: '#dc3545' }}></span>
          Invalidated
        </div>
      </div>
    </div>
  );
};

// Report Modal Component
const ReportModal = ({ location, onClose, onSubmit, categoryConfig }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'other',
    media_urls: [],
    is_sos: false,
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div style={styles.modalOverlay}>
      <div style={styles.modal}>
        <h2>Report Event</h2>
        <p style={styles.modalLocation}>
          Location: {location.lat.toFixed(4)}, {location.lng.toFixed(4)}
        </p>
        
        <form onSubmit={handleSubmit} style={styles.modalForm}>
          <input
            type="text"
            placeholder="Event Title"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            required
            style={styles.modalInput}
          />
          
          <textarea
            placeholder="Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            rows="4"
            style={styles.modalTextarea}
          />
          
          <select
            value={formData.category}
            onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            style={styles.modalSelect}
          >
            {Object.entries(categoryConfig).map(([key, config]) => (
              <option key={key} value={key}>{config.icon} {config.label}</option>
            ))}
          </select>
          
          <label style={styles.modalCheckbox}>
            <input
              type="checkbox"
              checked={formData.is_sos}
              onChange={(e) => setFormData({ ...formData, is_sos: e.target.checked })}
            />
            Emergency SOS (requires immediate attention)
          </label>
          
          <div style={styles.modalButtons}>
            <button type="button" onClick={onClose} style={styles.cancelBtn}>
              Cancel
            </button>
            <button type="submit" style={styles.submitBtn}>
              Submit Report
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    padding: '16px 24px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
  },
  logo: {
    fontSize: '24px',
    fontWeight: 'bold',
    margin: 0,
  },
  headerActions: {
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
  },
  sosButton: {
    background: '#dc3545',
    color: 'white',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '8px',
    fontWeight: 'bold',
    cursor: 'pointer',
    animation: 'pulse 2s infinite',
  },
  actionButton: {
    background: 'rgba(255,255,255,0.2)',
    color: 'white',
    border: 'none',
    padding: '10px 16px',
    borderRadius: '8px',
    cursor: 'pointer',
  },
  userInfo: {
    background: 'rgba(255,255,255,0.2)',
    padding: '8px 12px',
    borderRadius: '8px',
    fontSize: '14px',
  },
  filters: {
    background: 'white',
    padding: '16px',
    display: 'flex',
    gap: '16px',
    flexWrap: 'wrap',
    borderBottom: '1px solid #eee',
  },
  filterGroup: {
    display: 'flex',
    gap: '8px',
  },
  filterBtn: {
    padding: '8px 16px',
    border: '2px solid #667eea',
    background: 'white',
    color: '#667eea',
    borderRadius: '20px',
    cursor: 'pointer',
    transition: 'all 0.3s',
  },
  activeFilter: {
    background: '#667eea',
    color: 'white',
  },
  categorySelect: {
    padding: '8px 12px',
    border: '2px solid #ddd',
    borderRadius: '8px',
    fontSize: '14px',
  },
  mapContainer: {
    flex: 1,
    position: 'relative',
  },
  map: {
    height: 'calc(100vh - 200px)',
    width: '100%',
  },
  popupContent: {
    minWidth: '250px',
  },
  popupTitle: {
    margin: '0 0 8px 0',
    fontSize: '16px',
  },
  popupCategory: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '8px',
  },
  popupDescription: {
    fontSize: '14px',
    marginBottom: '12px',
  },
  popupStats: {
    display: 'flex',
    gap: '16px',
    marginBottom: '8px',
  },
  popupStatus: {
    fontSize: '13px',
    marginBottom: '12px',
  },
  popupActions: {
    display: 'flex',
    gap: '8px',
  },
  voteBtnYes: {
    flex: 1,
    padding: '8px',
    background: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  voteBtnNo: {
    flex: 1,
    padding: '8px',
    background: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modal: {
    background: 'white',
    padding: '32px',
    borderRadius: '16px',
    width: '90%',
    maxWidth: '500px',
    maxHeight: '90vh',
    overflow: 'auto',
  },
  modalLocation: {
    color: '#666',
    fontSize: '14px',
    marginBottom: '20px',
  },
  modalForm: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  modalInput: {
    padding: '12px',
    border: '2px solid #ddd',
    borderRadius: '8px',
    fontSize: '16px',
  },
  modalTextarea: {
    padding: '12px',
    border: '2px solid #ddd',
    borderRadius: '8px',
    fontSize: '14px',
    resize: 'vertical',
  },
  modalSelect: {
    padding: '12px',
    border: '2px solid #ddd',
    borderRadius: '8px',
    fontSize: '16px',
  },
  modalCheckbox: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
  },
  modalButtons: {
    display: 'flex',
    gap: '12px',
    marginTop: '8px',
  },
  cancelBtn: {
    flex: 1,
    padding: '12px',
    background: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
  },
  submitBtn: {
    flex: 1,
    padding: '12px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
  },
  legend: {
    position: 'absolute',
    bottom: '20px',
    right: '20px',
    background: 'white',
    padding: '16px',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
    marginBottom: '8px',
  },
  legendDot: {
    width: '16px',
    height: '16px',
    borderRadius: '50%',
  },
};

export default MapPage;
