import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { NeuButton, NeuCard, NeuInput, GlassPanel, Badge, Skeleton } from './UIComponents';

const TransportPage = () => {
  const dispatch = useDispatch();
  const { token, user } = useSelector((state) => state.auth);
  const [activeTab, setActiveTab] = useState('request'); // request, available
  const [transportType, setTransportType] = useState('taxi'); // taxi, bicycle
  const [loading, setLoading] = useState(false);
  const [requests, setRequests] = useState([]);
  const [showRequestModal, setShowRequestModal] = useState(false);
  
  const [formData, setFormData] = useState({
    pickupAddress: '',
    destinationAddress: '',
    pickupLatitude: null,
    pickupLongitude: null,
    destinationLatitude: null,
    destinationLongitude: null,
    urgency: 'normal',
    passengersCount: 1,
    luggageInfo: '',
    specialRequirements: '',
  });

  useEffect(() => {
    if (activeTab === 'available') {
      fetchRequests();
    }
  }, [activeTab]);

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setFormData(prev => ({
            ...prev,
            pickupLatitude: position.coords.latitude,
            pickupLongitude: position.coords.longitude
          }));
        },
        (error) => {
          console.error('Error getting location:', error);
          alert('Unable to get your location. Please enable GPS.');
        }
      );
    }
  };

  const handleGetLocation = () => {
    getCurrentLocation();
  };

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/features/transport-requests?status_filter=pending', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setRequests(data);
      }
    } catch (error) {
      console.error('Error fetching requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitRequest = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        title: `${transportType.charAt(0).toUpperCase() + transportType.slice(1)} needed`,
        description: `Need ${transportType} from ${formData.pickupAddress}`,
        category: transportType === 'taxi' ? 'taxi_needed' : 'bicycle_needed',
        latitude: formData.pickupLatitude,
        longitude: formData.pickupLongitude,
        address: formData.pickupAddress,
        transport_details: {
          request_type: transportType,
          pickup_latitude: formData.pickupLatitude,
          pickup_longitude: formData.pickupLongitude,
          pickup_address: formData.pickupAddress,
          destination_latitude: formData.destinationLatitude,
          destination_longitude: formData.destinationLongitude,
          destination_address: formData.destinationAddress,
          urgency: formData.urgency,
          passengers_count: formData.passengersCount,
          luggage_info: formData.luggageInfo,
          special_requirements: formData.specialRequirements,
        }
      };

      const response = await fetch('/api/v1/features/transport-request', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        alert('Transport request created successfully! Drivers nearby will be notified.');
        setShowRequestModal(false);
        resetForm();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to create request');
      }
    } catch (error) {
      console.error('Error creating request:', error);
      alert('Failed to create request');
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptRequest = async (requestId) => {
    try {
      const response = await fetch(`/api/v1/features/transport-request/${requestId}/accept`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          provider_latitude: formData.pickupLatitude || 0,
          provider_longitude: formData.pickupLongitude || 0,
        })
      });

      if (response.ok) {
        alert('Request accepted! Contact the passenger for details.');
        fetchRequests();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to accept request');
      }
    } catch (error) {
      console.error('Error accepting request:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      pickupAddress: '',
      destinationAddress: '',
      pickupLatitude: null,
      pickupLongitude: null,
      destinationLatitude: null,
      destinationLongitude: null,
      urgency: 'normal',
      passengersCount: 1,
      luggageInfo: '',
      specialRequirements: '',
    });
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <GlassPanel style={styles.header}>
        <h1 style={styles.title}>🚗 Transport Hub</h1>
        <p style={styles.subtitle}>Request or provide taxi/bicycle services in your community</p>
      </GlassPanel>

      {/* Type Selector */}
      <div style={styles.typeSelector}>
        <button
          onClick={() => setTransportType('taxi')}
          style={{
            ...styles.typeBtn,
            ...(transportType === 'taxi' ? styles.typeBtnActive : {})
          }}
        >
          🚕 Taxi
        </button>
        <button
          onClick={() => setTransportType('bicycle')}
          style={{
            ...styles.typeBtn,
            ...(transportType === 'bicycle' ? styles.typeBtnActive : {})
          }}
        >
          🚲 Bicycle
        </button>
      </div>

      {/* Tabs */}
      <div style={styles.tabs}>
        <button
          onClick={() => {
            setActiveTab('request');
            getCurrentLocation();
          }}
          style={{
            ...styles.tab,
            ...(activeTab === 'request' ? styles.activeTab : {})
          }}
        >
          📍 Request Ride
        </button>
        <button
          onClick={() => setActiveTab('available')}
          style={{
            ...styles.tab,
            ...(activeTab === 'available' ? styles.activeTab : {})
          }}
        >
          💼 Available Requests
        </button>
      </div>

      {/* Request Tab */}
      {activeTab === 'request' && (
        <NeuCard style={styles.requestForm}>
          <h2 style={styles.formTitle}>Request {transportType === 'taxi' ? 'Taxi' : 'Bicycle'}</h2>
          
          <form onSubmit={handleSubmitRequest}>
            <NeuButton
              type="button"
              variant="secondary"
              icon="📍"
              onClick={handleGetLocation}
              style={{ marginBottom: '15px' }}
            >
              Get Current Location
            </NeuButton>

            <NeuInput
              label="Pickup Address"
              value={formData.pickupAddress}
              onChange={(e) => setFormData({...formData, pickupAddress: e.target.value})}
              placeholder="Where should we pick you up?"
              required
            />

            <NeuInput
              label="Destination Address"
              value={formData.destinationAddress}
              onChange={(e) => setFormData({...formData, destinationAddress: e.target.value})}
              placeholder="Where are you going?"
            />

            <NeuInput
              label="Urgency"
              value={formData.urgency}
              onChange={(e) => setFormData({...formData, urgency: e.target.value})}
              as="select"
              options={[
                { value: 'normal', label: 'Normal' },
                { value: 'urgent', label: 'Urgent' },
                { value: 'emergency', label: 'Emergency' }
              ]}
            />

            <NeuInput
              label="Passengers"
              type="number"
              value={formData.passengersCount}
              onChange={(e) => setFormData({...formData, passengersCount: parseInt(e.target.value)})}
              min="1"
              max="10"
            />

            <NeuInput
              label="Luggage Info"
              value={formData.luggageInfo}
              onChange={(e) => setFormData({...formData, luggageInfo: e.target.value})}
              placeholder="e.g., 2 suitcases, 1 backpack"
            />

            <NeuInput
              label="Special Requirements"
              value={formData.specialRequirements}
              onChange={(e) => setFormData({...formData, specialRequirements: e.target.value})}
              placeholder="e.g., Child seat, wheelchair accessible"
              multiline
              rows={2}
            />

            <NeuButton type="submit" variant="primary" loading={loading} style={{ marginTop: '20px' }}>
              Request {transportType === 'taxi' ? 'Taxi' : 'Bicycle'}
            </NeuButton>
          </form>
        </NeuCard>
      )}

      {/* Available Requests Tab */}
      {activeTab === 'available' && (
        <div style={styles.requestsList}>
          {loading ? (
            Array(5).fill(0).map((_, i) => <Skeleton key={i} height={150} />)
          ) : requests.length === 0 ? (
            <GlassPanel style={styles.emptyState}>
              <p>No pending requests at the moment</p>
              <p style={{ fontSize: '0.9rem', color: '#666' }}>Check back later or refresh the page</p>
            </GlassPanel>
          ) : (
            requests.map((request) => (
              <NeuCard key={request.id} style={styles.requestCard}>
                <div style={styles.cardHeader}>
                  <Badge variant={request.urgency === 'emergency' ? 'danger' : request.urgency === 'urgent' ? 'warning' : 'info'}>
                    {request.urgency === 'emergency' ? '🚨 Emergency' : request.urgency === 'urgent' ? '⚡ Urgent' : '📋 Normal'}
                  </Badge>
                  <Badge variant="primary">{request.request_type === 'taxi' ? '🚕 Taxi' : '🚲 Bicycle'}</Badge>
                </div>

                <h3 style={styles.cardTitle}>{request.request_type === 'taxi' ? 'Taxi' : 'Bicycle'} Needed</h3>
                
                <div style={styles.routeInfo}>
                  <p style={styles.routeItem}>
                    <strong>📍 Pickup:</strong> {request.pickup_address || 'Current location'}
                  </p>
                  {request.destination_address && (
                    <p style={styles.routeItem}>
                      <strong>🏁 Destination:</strong> {request.destination_address}
                    </p>
                  )}
                </div>

                <div style={styles.details}>
                  <span>👥 {request.passengers_count} passenger(s)</span>
                  {request.luggage_info && <span>🧳 {request.luggage_info}</span>}
                  {request.special_requirements && (
                    <span>♿ {request.special_requirements}</span>
                  )}
                </div>

                <div style={styles.cardFooter}>
                  <span style={styles.timestamp}>
                    {new Date(request.requested_at).toLocaleString()}
                  </span>
                  <NeuButton
                    variant="success"
                    size="small"
                    onClick={() => handleAcceptRequest(request.id)}
                  >
                    Accept & Earn Points
                  </NeuButton>
                </div>
              </NeuCard>
            ))
          )}
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    minHeight: '100vh',
    padding: '20px',
    background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  },
  header: {
    textAlign: 'center',
    marginBottom: '30px',
    padding: '30px',
  },
  title: {
    fontSize: '2.5rem',
    fontWeight: '700',
    color: '#fff',
    margin: '0 0 10px 0',
    textShadow: '0 2px 4px rgba(0,0,0,0.2)',
  },
  subtitle: {
    fontSize: '1.1rem',
    color: 'rgba(255,255,255,0.9)',
    margin: 0,
  },
  typeSelector: {
    display: 'flex',
    gap: '15px',
    justifyContent: 'center',
    marginBottom: '20px',
  },
  typeBtn: {
    padding: '15px 40px',
    border: 'none',
    borderRadius: '30px',
    background: 'rgba(255,255,255,0.2)',
    color: '#fff',
    fontSize: '1.2rem',
    cursor: 'pointer',
    backdropFilter: 'blur(10px)',
    transition: 'all 0.3s ease',
  },
  typeBtnActive: {
    background: '#fff',
    color: '#f5576c',
    boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
    transform: 'scale(1.05)',
  },
  tabs: {
    display: 'flex',
    gap: '10px',
    marginBottom: '20px',
    justifyContent: 'center',
  },
  tab: {
    padding: '12px 24px',
    border: 'none',
    borderRadius: '25px',
    background: 'rgba(255,255,255,0.2)',
    color: '#fff',
    fontSize: '1rem',
    cursor: 'pointer',
    backdropFilter: 'blur(10px)',
    transition: 'all 0.3s ease',
  },
  activeTab: {
    background: '#fff',
    color: '#f5576c',
    boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
  },
  requestForm: {
    maxWidth: '600px',
    margin: '0 auto',
    padding: '30px',
    background: 'rgba(255,255,255,0.95)',
  },
  formTitle: {
    fontSize: '1.8rem',
    fontWeight: '600',
    color: '#333',
    marginBottom: '20px',
    textAlign: 'center',
  },
  requestsList: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
    gap: '20px',
  },
  requestCard: {
    padding: '20px',
    background: 'rgba(255,255,255,0.95)',
  },
  cardHeader: {
    display: 'flex',
    gap: '8px',
    marginBottom: '12px',
    flexWrap: 'wrap',
  },
  cardTitle: {
    fontSize: '1.3rem',
    fontWeight: '600',
    color: '#333',
    margin: '0 0 15px 0',
  },
  routeInfo: {
    marginBottom: '15px',
  },
  routeItem: {
    fontSize: '0.95rem',
    color: '#555',
    marginBottom: '8px',
  },
  details: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '15px',
    fontSize: '0.9rem',
    color: '#666',
    marginBottom: '15px',
  },
  cardFooter: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: '15px',
    borderTop: '1px solid #eee',
  },
  timestamp: {
    fontSize: '0.85rem',
    color: '#999',
  },
  emptyState: {
    gridColumn: '1 / -1',
    textAlign: 'center',
    padding: '60px 20px',
  },
};

export default TransportPage;
