import React, { useState, useEffect } from 'react';
import api from '../../services/api';

const LeaderboardPage = () => {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    try {
      const response = await api.get('/admin/leaderboard?limit=20');
      setLeaderboard(response.data.entries);
      setLoading(false);
    } catch (err) {
      setError('Failed to load leaderboard');
      setLoading(false);
      console.error(err);
    }
  };

  const getRankIcon = (rank) => {
    switch (rank) {
      case 1: return '🥇';
      case 2: return '🥈';
      case 3: return '🥉';
      default: return `#${rank}`;
    }
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading leaderboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>{error}</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>🏆 Community Leaders</h1>
        <p style={styles.subtitle}>Top contributors keeping our community safe</p>
      </div>

      <div style={styles.leaderboard}>
        {leaderboard.map((entry, index) => (
          <div
            key={entry.user_id}
            style={{
              ...styles.entry,
              ...(index < 3 ? styles.topThree : {}),
            }}
          >
            <div style={styles.rank}>
              <span style={styles.rankIcon}>{getRankIcon(entry.rank)}</span>
            </div>
            
            <div style={styles.userInfo}>
              <div style={styles.username}>{entry.username}</div>
              <div style={styles.stats}>
                <span style={styles.stat}>
                  👍 {entry.verifications_count} verifications
                </span>
                <span style={styles.stat}>
                  🏅 {entry.badges_count} badges
                </span>
              </div>
            </div>
            
            <div style={styles.points}>
              <div style={styles.pointsValue}>{entry.reputation_points}</div>
              <div style={styles.pointsLabel}>points</div>
            </div>
          </div>
        ))}
      </div>

      <div style={styles.infoCard}>
        <h3>How to earn points:</h3>
        <ul style={styles.infoList}>
          <li>📝 Report an event: +1 point</li>
          <li>✅ Verify an event: +1 point</li>
          <li>🎯 Event gets validated: +5 points (for reporter)</li>
          <li>🚶 Complete a safe walk: +2 points</li>
          <li>🏅 Earn badges for achievements</li>
        </ul>
      </div>

      <button onClick={() => window.history.back()} style={styles.backButton}>
        ← Back to Map
      </button>
    </div>
  );
};

const styles = {
  container: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    padding: '20px',
  },
  loading: {
    color: 'white',
    fontSize: '20px',
    textAlign: 'center',
    marginTop: '100px',
  },
  error: {
    background: '#fee',
    color: '#c00',
    padding: '16px',
    borderRadius: '8px',
    textAlign: 'center',
  },
  header: {
    textAlign: 'center',
    color: 'white',
    marginBottom: '32px',
  },
  title: {
    fontSize: '36px',
    fontWeight: 'bold',
    margin: '0 0 8px 0',
  },
  subtitle: {
    fontSize: '18px',
    opacity: 0.9,
    margin: 0,
  },
  leaderboard: {
    maxWidth: '800px',
    margin: '0 auto',
  },
  entry: {
    display: 'flex',
    alignItems: 'center',
    background: 'white',
    borderRadius: '12px',
    padding: '20px',
    marginBottom: '12px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
    transition: 'transform 0.2s',
  },
  topThree: {
    transform: 'scale(1.02)',
    boxShadow: '0 6px 20px rgba(0,0,0,0.15)',
  },
  rank: {
    width: '60px',
    textAlign: 'center',
  },
  rankIcon: {
    fontSize: '32px',
  },
  userInfo: {
    flex: 1,
  },
  username: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#333',
    marginBottom: '4px',
  },
  stats: {
    display: 'flex',
    gap: '16px',
    fontSize: '14px',
    color: '#666',
  },
  stat: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  points: {
    textAlign: 'center',
    minWidth: '80px',
  },
  pointsValue: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#667eea',
  },
  pointsLabel: {
    fontSize: '12px',
    color: '#999',
  },
  infoCard: {
    maxWidth: '800px',
    margin: '32px auto',
    background: 'rgba(255,255,255,0.95)',
    borderRadius: '12px',
    padding: '24px',
  },
  infoList: {
    margin: '12px 0 0 0',
    paddingLeft: '20px',
    color: '#555',
    lineHeight: '1.8',
  },
  backButton: {
    display: 'block',
    margin: '24px auto',
    padding: '14px 32px',
    background: 'rgba(255,255,255,0.2)',
    color: 'white',
    border: '2px solid white',
    borderRadius: '8px',
    fontSize: '16px',
    cursor: 'pointer',
    transition: 'background 0.3s',
  },
};

export default LeaderboardPage;
