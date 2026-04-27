import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { NeuCard, GlassPanel, Badge, Skeleton } from './UIComponents';

const AnalyticsDashboard = () => {
  const { token, user } = useSelector((state) => state.auth);
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState(null);
  const [timeRange, setTimeRange] = useState(30); // days

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/features/analytics/advanced?days=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      } else {
        console.error('Failed to fetch analytics');
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!user || !['admin', 'moderator', 'official'].includes(user.role)) {
    return (
      <div style={styles.container}>
        <GlassPanel style={styles.accessDenied}>
          <h1>🔒 Access Denied</h1>
          <p>This dashboard is only available to administrators and moderators.</p>
        </GlassPanel>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingGrid}>
          {Array(8).fill(0).map((_, i) => (
            <Skeleton key={i} height={200} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <GlassPanel style={styles.header}>
        <h1 style={styles.title}>📊 Analytics Dashboard</h1>
        <p style={styles.subtitle}>Community insights and verification metrics</p>
        
        <div style={styles.timeRangeSelector}>
          {[7, 14, 30, 90].map(days => (
            <button
              key={days}
              onClick={() => setTimeRange(days)}
              style={{
                ...styles.timeRangeBtn,
                ...(timeRange === days ? styles.timeRangeBtnActive : {})
              }}
            >
              Last {days} days
            </button>
          ))}
        </div>
      </GlassPanel>

      {/* Summary Cards */}
      <div style={styles.summaryGrid}>
        <NeuCard style={styles.statCard}>
          <div style={styles.statIcon}>📋</div>
          <div style={styles.statContent}>
            <h3 style={styles.statValue}>{analytics?.total_events || 0}</h3>
            <p style={styles.statLabel}>Total Events</p>
          </div>
        </NeuCard>

        <NeuCard style={styles.statCard}>
          <div style={{...styles.statIcon, color: '#10b981'}}>✅</div>
          <div style={styles.statContent}>
            <h3 style={{...styles.statValue, color: '#10b981'}}>{analytics?.validated_events || 0}</h3>
            <p style={styles.statLabel}>Validated</p>
          </div>
        </NeuCard>

        <NeuCard style={styles.statCard}>
          <div style={{...styles.statIcon, color: '#f59e0b'}}>⏳</div>
          <div style={styles.statContent}>
            <h3 style={{...styles.statValue, color: '#f59e0b'}}>{analytics?.pending_events || 0}</h3>
            <p style={styles.statLabel}>Pending</p>
          </div>
        </NeuCard>

        <NeuCard style={styles.statCard}>
          <div style={{...styles.statIcon, color: '#ef4444'}}>❌</div>
          <div style={styles.statContent}>
            <h3 style={{...styles.statValue, color: '#ef4444'}}>{analytics?.invalidated_events || 0}</h3>
            <p style={styles.statLabel}>Invalidated</p>
          </div>
        </NeuCard>

        <NeuCard style={styles.statCard}>
          <div style={styles.statIcon}>👥</div>
          <div style={styles.statContent}>
            <h3 style={styles.statValue}>{analytics?.total_users || 0}</h3>
            <p style={styles.statLabel}>Total Users</p>
          </div>
        </NeuCard>

        <NeuCard style={styles.statCard}>
          <div style={styles.statIcon}>🟢</div>
          <div style={styles.statContent}>
            <h3 style={styles.statValue}>{analytics?.active_users_today || 0}</h3>
            <p style={styles.statLabel}>Active Today</p>
          </div>
        </NeuCard>

        <NeuCard style={styles.statCard}>
          <div style={styles.statIcon}>🎯</div>
          <div style={styles.statContent}>
            <h3 style={styles.statValue}>{analytics?.verification_accuracy || 0}%</h3>
            <p style={styles.statLabel}>Verification Accuracy</p>
          </div>
        </NeuCard>

        <NeuCard style={styles.statCard}>
          <div style={styles.statIcon}>⏱️</div>
          <div style={styles.statContent}>
            <h3 style={styles.statValue}>{analytics?.average_verification_time_minutes || 0}m</h3>
            <p style={styles.statLabel}>Avg Verification Time</p>
          </div>
        </NeuCard>
      </div>

      {/* Charts Row 1 */}
      <div style={styles.chartsRow}>
        {/* Verification Trends */}
        <NeuCard style={styles.chartCard}>
          <h3 style={styles.chartTitle}>📈 Verification Trends</h3>
          <div style={styles.trendChart}>
            {analytics?.verification_trends?.map((trend, index) => (
              <div key={index} style={styles.trendBar}>
                <div style={styles.barGroup}>
                  <div 
                    style={{
                      ...styles.bar,
                      ...styles.validatedBar,
                      height: `${Math.max(trend.validated * 5, 2)}px`
                    }}
                    title={`Validated: ${trend.validated}`}
                  />
                  <div 
                    style={{
                      ...styles.bar,
                      ...styles.invalidatedBar,
                      height: `${Math.max(trend.invalidated * 5, 2)}px`
                    }}
                    title={`Invalidated: ${trend.invalidated}`}
                  />
                  <div 
                    style={{
                      ...styles.bar,
                      ...styles.pendingBar,
                      height: `${Math.max(trend.pending * 5, 2)}px`
                    }}
                    title={`Pending: ${trend.pending}`}
                  />
                </div>
                <span style={styles.trendDate}>{new Date(trend.date).toLocaleDateString(undefined, {month: 'short', day: 'numeric'})}</span>
              </div>
            ))}
          </div>
          <div style={styles.legend}>
            <div style={styles.legendItem}>
              <div style={{...styles.legendDot, background: '#10b981'}}></div>
              <span>Validated</span>
            </div>
            <div style={styles.legendItem}>
              <div style={{...styles.legendDot, background: '#ef4444'}}></div>
              <span>Invalidated</span>
            </div>
            <div style={styles.legendItem}>
              <div style={{...styles.legendDot, background: '#f59e0b'}}></div>
              <span>Pending</span>
            </div>
          </div>
        </NeuCard>

        {/* Top Categories */}
        <NeuCard style={styles.chartCard}>
          <h3 style={styles.chartTitle}>📂 Top Categories</h3>
          <div style={styles.categoriesList}>
            {analytics?.top_categories?.slice(0, 8).map((cat, index) => (
              <div key={index} style={styles.categoryItem}>
                <div style={styles.categoryRank}>#{index + 1}</div>
                <div style={styles.categoryInfo}>
                  <span style={styles.categoryName}>{cat.category.replace('_', ' ')}</span>
                  <div style={styles.progressBar}>
                    <div 
                      style={{
                        ...styles.progressFill,
                        width: `${cat.percentage}%`,
                        background: `hsl(${index * 45}, 70%, 60%)`
                      }}
                    />
                  </div>
                </div>
                <div style={styles.categoryStats}>
                  <span style={styles.categoryCount}>{cat.count}</span>
                  <span style={styles.categoryPercentage}>{cat.percentage}%</span>
                </div>
              </div>
            ))}
          </div>
        </NeuCard>
      </div>

      {/* Charts Row 2 */}
      <div style={styles.chartsRow}>
        {/* Hot Spots */}
        <NeuCard style={styles.chartCard}>
          <h3 style={styles.chartTitle}>🔥 Hot Spots</h3>
          {analytics?.hot_spots?.length > 0 ? (
            <div style={styles.hotSpotsList}>
              {analytics.hot_spots.map((spot, index) => (
                <div key={index} style={styles.hotSpotItem}>
                  <div style={styles.hotSpotRank}>#{index + 1}</div>
                  <div style={styles.hotSpotInfo}>
                    <div style={styles.hotSpotCoords}>
                      📍 {spot.latitude.toFixed(4)}, {spot.longitude.toFixed(4)}
                    </div>
                    <div style={styles.hotSpotDetails}>
                      <Badge variant="danger">{spot.event_count} events</Badge>
                      <span style={styles.hotSpotRadius}>{spot.radius_km}km radius</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={styles.emptyMessage}>No hot spots detected in this period</p>
          )}
        </NeuCard>

        {/* Transport & Lost Items Stats */}
        <NeuCard style={styles.chartCard}>
          <h3 style={styles.chartTitle}>🚗 Transport Services</h3>
          <div style={styles.transportStats}>
            <div style={styles.transportStat}>
              <div style={styles.transportStatIcon}>📊</div>
              <div>
                <h4 style={styles.transportStatValue}>{analytics?.transport_requests_total || 0}</h4>
                <p style={styles.transportStatLabel}>Total Requests</p>
              </div>
            </div>
            <div style={styles.transportStat}>
              <div style={styles.transportStatIcon}>⏳</div>
              <div>
                <h4 style={styles.transportStatValue}>{analytics?.transport_requests_pending || 0}</h4>
                <p style={styles.transportStatLabel}>Pending</p>
              </div>
            </div>
          </div>

          <h3 style={{...styles.chartTitle, marginTop: '30px'}}>🔍 Lost & Found</h3>
          <div style={styles.lostFoundStats}>
            <div style={styles.foundRate}>
              <div style={styles.circularProgress}>
                <svg viewBox="0 0 100 100" style={styles.svg}>
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth="10"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="10"
                    strokeDasharray={`${(analytics?.lost_items_found_rate || 0) * 2.83} 283`}
                    transform="rotate(-90 50 50)"
                    style={styles.progressCircle}
                  />
                </svg>
                <div style={styles.foundRateText}>
                  {analytics?.lost_items_found_rate || 0}%
                </div>
              </div>
              <p style={styles.foundRateLabel}>Items Found Rate</p>
            </div>
            <div style={styles.foundTips}>
              <h4>💡 Tips to Improve</h4>
              <ul style={styles.tipsList}>
                <li>Encourage photo uploads</li>
                <li>Send push notifications</li>
                <li>Reward finders with points</li>
                <li>Create community awareness</li>
              </ul>
            </div>
          </div>
        </NeuCard>
      </div>

      {/* Export Options */}
      <GlassPanel style={styles.exportPanel}>
        <h3 style={styles.exportTitle}>📥 Export Data</h3>
        <div style={styles.exportButtons}>
          <button style={styles.exportBtn}>Export as CSV</button>
          <button style={styles.exportBtn}>Export as PDF</button>
          <button style={styles.exportBtn}>Generate Report</button>
        </div>
      </GlassPanel>
    </div>
  );
};

const styles = {
  container: {
    minHeight: '100vh',
    padding: '20px',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
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
  },
  subtitle: {
    fontSize: '1.1rem',
    color: 'rgba(255,255,255,0.9)',
    margin: '0 0 20px 0',
  },
  timeRangeSelector: {
    display: 'flex',
    gap: '10px',
    justifyContent: 'center',
    flexWrap: 'wrap',
  },
  timeRangeBtn: {
    padding: '10px 20px',
    border: 'none',
    borderRadius: '20px',
    background: 'rgba(255,255,255,0.2)',
    color: '#fff',
    cursor: 'pointer',
    backdropFilter: 'blur(10px)',
    transition: 'all 0.3s ease',
  },
  timeRangeBtnActive: {
    background: '#fff',
    color: '#667eea',
    boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
  },
  summaryGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '20px',
    marginBottom: '30px',
  },
  statCard: {
    padding: '25px',
    display: 'flex',
    alignItems: 'center',
    gap: '15px',
    background: 'rgba(255,255,255,0.95)',
  },
  statIcon: {
    fontSize: '2.5rem',
  },
  statContent: {
    flex: 1,
  },
  statValue: {
    fontSize: '2rem',
    fontWeight: '700',
    color: '#333',
    margin: '0 0 5px 0',
  },
  statLabel: {
    fontSize: '0.9rem',
    color: '#666',
    margin: 0,
  },
  chartsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
    gap: '20px',
    marginBottom: '20px',
  },
  chartCard: {
    padding: '25px',
    background: 'rgba(255,255,255,0.95)',
  },
  chartTitle: {
    fontSize: '1.3rem',
    fontWeight: '600',
    color: '#333',
    margin: '0 0 20px 0',
  },
  trendChart: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    height: '200px',
    padding: '20px 10px',
    background: 'linear-gradient(to bottom, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05))',
    borderRadius: '10px',
  },
  trendBar: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '8px',
  },
  barGroup: {
    display: 'flex',
    gap: '3px',
    alignItems: 'flex-end',
  },
  bar: {
    width: '12px',
    borderRadius: '3px 3px 0 0',
    transition: 'height 0.3s ease',
  },
  validatedBar: {
    background: '#10b981',
  },
  invalidatedBar: {
    background: '#ef4444',
  },
  pendingBar: {
    background: '#f59e0b',
  },
  trendDate: {
    fontSize: '0.75rem',
    color: '#666',
    transform: 'rotate(-45deg)',
  },
  legend: {
    display: 'flex',
    justifyContent: 'center',
    gap: '20px',
    marginTop: '15px',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '0.85rem',
    color: '#666',
  },
  legendDot: {
    width: '12px',
    height: '12px',
    borderRadius: '3px',
  },
  categoriesList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  categoryItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  categoryRank: {
    fontSize: '1.2rem',
    fontWeight: '700',
    color: '#667eea',
    width: '30px',
  },
  categoryInfo: {
    flex: 1,
  },
  categoryName: {
    fontSize: '0.95rem',
    color: '#333',
    display: 'block',
    marginBottom: '6px',
    textTransform: 'capitalize',
  },
  progressBar: {
    height: '8px',
    background: '#e5e7eb',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: '4px',
    transition: 'width 0.5s ease',
  },
  categoryStats: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
    gap: '4px',
  },
  categoryCount: {
    fontSize: '1rem',
    fontWeight: '600',
    color: '#333',
  },
  categoryPercentage: {
    fontSize: '0.85rem',
    color: '#999',
  },
  hotSpotsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px',
  },
  hotSpotItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '15px',
    padding: '12px',
    background: 'rgba(239, 68, 68, 0.05)',
    borderRadius: '10px',
  },
  hotSpotRank: {
    fontSize: '1.2rem',
    fontWeight: '700',
    color: '#ef4444',
    width: '30px',
  },
  hotSpotInfo: {
    flex: 1,
  },
  hotSpotCoords: {
    fontSize: '0.95rem',
    color: '#333',
    marginBottom: '6px',
  },
  hotSpotDetails: {
    display: 'flex',
    gap: '10px',
    alignItems: 'center',
  },
  hotSpotRadius: {
    fontSize: '0.85rem',
    color: '#666',
  },
  transportStats: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '15px',
  },
  transportStat: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '15px',
    background: 'rgba(102, 126, 234, 0.05)',
    borderRadius: '10px',
  },
  transportStatIcon: {
    fontSize: '2rem',
  },
  transportStatValue: {
    fontSize: '1.8rem',
    fontWeight: '700',
    color: '#333',
    margin: '0 0 5px 0',
  },
  transportStatLabel: {
    fontSize: '0.85rem',
    color: '#666',
    margin: 0,
  },
  lostFoundStats: {
    display: 'flex',
    gap: '30px',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  foundRate: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  circularProgress: {
    position: 'relative',
    width: '120px',
    height: '120px',
  },
  svg: {
    width: '100%',
    height: '100%',
  },
  progressCircle: {
    strokeLinecap: 'round',
    transition: 'stroke-dasharray 0.5s ease',
  },
  foundRateText: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    fontSize: '1.5rem',
    fontWeight: '700',
    color: '#10b981',
  },
  foundRateLabel: {
    fontSize: '0.9rem',
    color: '#666',
    marginTop: '10px',
  },
  foundTips: {
    flex: 1,
    minWidth: '200px',
  },
  tipsList: {
    margin: '10px 0 0 0',
    paddingLeft: '20px',
    color: '#666',
    fontSize: '0.9rem',
  },
  emptyMessage: {
    textAlign: 'center',
    color: '#999',
    padding: '40px 20px',
  },
  exportPanel: {
    padding: '25px',
    textAlign: 'center',
  },
  exportTitle: {
    fontSize: '1.2rem',
    fontWeight: '600',
    color: '#fff',
    margin: '0 0 20px 0',
  },
  exportButtons: {
    display: 'flex',
    gap: '15px',
    justifyContent: 'center',
    flexWrap: 'wrap',
  },
  exportBtn: {
    padding: '12px 24px',
    border: 'none',
    borderRadius: '25px',
    background: '#fff',
    color: '#667eea',
    fontSize: '0.95rem',
    fontWeight: '600',
    cursor: 'pointer',
    boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
    transition: 'all 0.3s ease',
  },
  loadingGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '20px',
    padding: '20px',
  },
  accessDenied: {
    textAlign: 'center',
    padding: '60px 20px',
    color: '#fff',
  },
};

export default AnalyticsDashboard;
