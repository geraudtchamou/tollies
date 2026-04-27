import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { triggerSOS } from '../../store/slices/eventsSlice';
import { useNavigate } from 'react-router-dom';

const SOSPage = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [location, setLocation] = useState(null);
  const [message, setMessage] = useState('Emergency! Need immediate assistance.');
  const [isSending, setIsSending] = useState(false);
  const [sent, setSent] = useState(false);

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          });
        },
        (error) => {
          alert('Unable to get location. Please enable location services.');
          console.error(error);
        }
      );
    } else {
      alert('Geolocation is not supported by this browser.');
    }
  };

  const handleSendSOS = async () => {
    if (!location) {
      alert('Please get your location first!');
      return;
    }

    setIsSending(true);
    try {
      await dispatch(triggerSOS({
        latitude: location.latitude,
        longitude: location.longitude,
        message,
        share_video: true,
      })).unwrap();
      setSent(true);
    } catch (error) {
      console.error('Failed to send SOS:', error);
      alert('Failed to send SOS. Please try again.');
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>🚨 Emergency SOS</h1>
        <p style={styles.subtitle}>Send emergency alert to nearby users</p>

        {sent ? (
          <div style={styles.successCard}>
            <div style={styles.successIcon}>✅</div>
            <h2>SOS Alert Sent!</h2>
            <p>Nearby users and authorities have been notified.</p>
            <p style={styles.successSubtext}>Stay safe. Help is on the way.</p>
            <button onClick={() => navigate('/')} style={styles.backButton}>
              Return to Map
            </button>
          </div>
        ) : (
          <>
            <div style={styles.warningBox}>
              ⚠️ Only use SOS for genuine emergencies. False alarms may result in account suspension.
            </div>

            <button onClick={getCurrentLocation} style={styles.locationButton}>
              📍 {location ? 'Location Updated' : 'Get Current Location'}
            </button>

            {location && (
              <div style={styles.locationInfo}>
                <p><strong>Latitude:</strong> {location.latitude.toFixed(6)}</p>
                <p><strong>Longitude:</strong> {location.longitude.toFixed(6)}</p>
              </div>
            )}

            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Describe your emergency..."
              rows="4"
              style={styles.textarea}
            />

            <button
              onClick={handleSendSOS}
              disabled={!location || isSending}
              style={{
                ...styles.sosButton,
                opacity: !location || isSending ? 0.5 : 1,
              }}
            >
              {isSending ? 'Sending...' : '🚨 SEND SOS ALERT'}
            </button>

            <div style={styles.infoBox}>
              <h3>What happens when you send SOS?</h3>
              <ul style={styles.infoList}>
                <li>🔔 Nearby users receive instant push notifications</li>
                <li>📍 Your location is shared on the community map</li>
                <li>🚨 Event is auto-validated and highlighted</li>
                <li>👥 Community members can respond quickly</li>
              </ul>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

const styles = {
  container: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '20px',
  },
  card: {
    background: 'white',
    borderRadius: '16px',
    padding: '40px',
    width: '100%',
    maxWidth: '500px',
    boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
  },
  title: {
    fontSize: '32px',
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: '8px',
    color: '#dc3545',
  },
  subtitle: {
    textAlign: 'center',
    color: '#666',
    marginBottom: '24px',
  },
  warningBox: {
    background: '#fff3cd',
    border: '2px solid #ffc107',
    color: '#856404',
    padding: '16px',
    borderRadius: '8px',
    marginBottom: '24px',
    textAlign: 'center',
    fontWeight: '500',
  },
  locationButton: {
    width: '100%',
    padding: '16px',
    background: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
    marginBottom: '16px',
  },
  locationInfo: {
    background: '#f8f9fa',
    padding: '16px',
    borderRadius: '8px',
    marginBottom: '16px',
  },
  textarea: {
    width: '100%',
    padding: '14px',
    border: '2px solid #ddd',
    borderRadius: '8px',
    fontSize: '16px',
    resize: 'vertical',
    marginBottom: '16px',
    boxSizing: 'border-box',
  },
  sosButton: {
    width: '100%',
    padding: '20px',
    background: 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '24px',
    fontWeight: 'bold',
    cursor: 'pointer',
    marginBottom: '24px',
    animation: 'pulse 1s infinite',
  },
  infoBox: {
    background: '#f8f9fa',
    padding: '20px',
    borderRadius: '8px',
  },
  infoList: {
    margin: '12px 0 0 0',
    paddingLeft: '20px',
    color: '#555',
  },
  successCard: {
    textAlign: 'center',
    padding: '20px',
  },
  successIcon: {
    fontSize: '64px',
    marginBottom: '16px',
  },
  successSubtext: {
    color: '#28a745',
    fontWeight: 'bold',
    marginTop: '16px',
  },
  backButton: {
    marginTop: '24px',
    padding: '14px 32px',
    background: '#667eea',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '16px',
    cursor: 'pointer',
  },
};

export default SOSPage;
