import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { NeuButton, NeuCard, NeuInput, GlassPanel, Badge, Skeleton } from './UIComponents';

const LostAndFoundPage = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { token, user } = useSelector((state) => state.auth);
  const [activeTab, setActiveTab] = useState('documents'); // documents, items, pets
  const [loading, setLoading] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [items, setItems] = useState([]);
  
  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    latitude: 0,
    longitude: 0,
    address: '',
    // Document specific
    documentType: '',
    documentNumber: '',
    holderName: '',
    issuingAuthority: '',
    isSensitive: true,
    // Item specific
    itemType: '',
    brand: '',
    color: '',
    size: '',
    locationDescription: '',
    containsValuables: false,
  });

  useEffect(() => {
    fetchItems();
    getCurrentLocation();
  }, [activeTab]);

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setFormData(prev => ({
            ...prev,
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          }));
        },
        (error) => {
          console.error('Error getting location:', error);
        }
      );
    }
  };

  const fetchItems = async () => {
    setLoading(true);
    try {
      const endpoint = activeTab === 'documents' ? '/api/v1/features/lost-documents' : 
                       activeTab === 'items' ? '/api/v1/features/forgotten-items' :
                       '/api/v1/events?category=lost_pet';
      
      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setItems(data);
      }
    } catch (error) {
      console.error('Error fetching items:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        title: formData.title,
        description: formData.description,
        category: activeTab === 'documents' ? 'lost_document' : 
                  activeTab === 'items' ? 'forgotten_bag' : 'lost_pet',
        latitude: formData.latitude,
        longitude: formData.longitude,
        address: formData.address,
        media_urls: [],
      };

      if (activeTab === 'documents') {
        payload.document_details = {
          document_type: formData.documentType,
          document_number: formData.documentNumber,
          holder_name: formData.holderName,
          issuing_authority: formData.issuingAuthority,
          is_sensitive: formData.isSensitive,
          contact_info: user.phone || user.email
        };
      } else if (activeTab === 'items') {
        payload.forgotten_item_details = {
          item_type: formData.itemType,
          brand: formData.brand,
          color: formData.color,
          size: formData.size,
          location_description: formData.locationDescription,
          description: formData.description,
          contains_valuables: formData.containsValuables,
          contact_info: user.phone || user.email
        };
      }

      const endpoint = activeTab === 'documents' ? '/api/v1/features/lost-document' :
                       activeTab === 'items' ? '/api/v1/features/forgotten-item' :
                       '/api/v1/events';

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        alert('Report submitted successfully!');
        setShowReportModal(false);
        fetchItems();
        resetForm();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to submit report');
      }
    } catch (error) {
      console.error('Error submitting report:', error);
      alert('Failed to submit report');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      latitude: 0,
      longitude: 0,
      address: '',
      documentType: '',
      documentNumber: '',
      holderName: '',
      issuingAuthority: '',
      isSensitive: true,
      itemType: '',
      brand: '',
      color: '',
      size: '',
      locationDescription: '',
      containsValuables: false,
    });
  };

  const handleMarkFound = async (id) => {
    try {
      const endpoint = activeTab === 'documents' ? 
        `/api/v1/features/lost-document/${id}/found` :
        `/api/v1/features/forgotten-item/${id}/claim`;
      
      const response = await fetch(endpoint, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        alert('Item marked as found/claimed!');
        fetchItems();
      }
    } catch (error) {
      console.error('Error marking as found:', error);
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <GlassPanel style={styles.header}>
        <h1 style={styles.title}>🔍 Lost & Found</h1>
        <p style={styles.subtitle}>Report or search for lost items, documents, and pets</p>
      </GlassPanel>

      {/* Tabs */}
      <div style={styles.tabs}>
        <button
          onClick={() => setActiveTab('documents')}
          style={{
            ...styles.tab,
            ...(activeTab === 'documents' ? styles.activeTab : {})
          }}
        >
          📄 Documents
        </button>
        <button
          onClick={() => setActiveTab('items')}
          style={{
            ...styles.tab,
            ...(activeTab === 'items' ? styles.activeTab : {})
          }}
        >
          🎒 Items & Bags
        </button>
        <button
          onClick={() => setActiveTab('pets')}
          style={{
            ...styles.tab,
            ...(activeTab === 'pets' ? styles.activeTab : {})
          }}
        >
          🐾 Pets
        </button>
      </div>

      {/* Action Bar */}
      <div style={styles.actionBar}>
        <NeuButton
          variant="primary"
          icon="➕"
          onClick={() => setShowReportModal(true)}
        >
          Report Lost Item
        </NeuButton>
      </div>

      {/* Items List */}
      <div style={styles.itemsGrid}>
        {loading ? (
          Array(6).fill(0).map((_, i) => (
            <Skeleton key={i} height={200} />
          ))
        ) : items.length === 0 ? (
          <GlassPanel style={styles.emptyState}>
            <p>No items found in this category</p>
            <NeuButton variant="primary" onClick={() => setShowReportModal(true)}>
              Be the first to report
            </NeuButton>
          </GlassPanel>
        ) : (
          items.map((item) => (
            <NeuCard key={item.id} style={styles.itemCard}>
              <div style={styles.cardHeader}>
                <Badge variant={item.is_found || item.is_claimed ? 'success' : 'warning'}>
                  {item.is_found || item.is_claimed ? '✅ Found' : '⏳ Pending'}
                </Badge>
                {item.contains_valuables && (
                  <Badge variant="danger">💎 Valuables</Badge>
                )}
              </div>
              
              <h3 style={styles.itemTitle}>{item.item_type || item.document_type || 'Unknown'}</h3>
              
              {item.brand && <p style={styles.itemDetail}>Brand: {item.brand}</p>}
              {item.color && <p style={styles.itemDetail}>Color: {item.color}</p>}
              {item.holder_name && <p style={styles.itemDetail}>Owner: {item.holder_name}</p>}
              {item.location_description && (
                <p style={styles.itemDetail}>📍 {item.location_description}</p>
              )}
              
              <p style={styles.itemDescription}>{item.description}</p>
              
              <div style={styles.cardFooter}>
                <span style={styles.timestamp}>
                  {new Date(item.created_at).toLocaleDateString()}
                </span>
                {!item.is_found && !item.is_claimed && (
                  <NeuButton
                    variant="success"
                    size="small"
                    onClick={() => handleMarkFound(item.id)}
                  >
                    Mark as Found
                  </NeuButton>
                )}
              </div>
            </NeuCard>
          ))
        )}
      </div>

      {/* Report Modal */}
      {showReportModal && (
        <div style={styles.modalOverlay}>
          <NeuCard style={styles.modal}>
            <h2 style={styles.modalTitle}>
              {activeTab === 'documents' ? '📄 Report Lost Document' :
               activeTab === 'items' ? '🎒 Report Forgotten Item' :
               '🐾 Report Lost Pet'}
            </h2>
            
            <form onSubmit={handleSubmit} style={styles.form}>
              <NeuInput
                label="Title"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                placeholder="Brief title"
                required
              />
              
              <NeuInput
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Detailed description"
                multiline
                rows={3}
              />
              
              {activeTab === 'documents' && (
                <>
                  <NeuInput
                    label="Document Type"
                    value={formData.documentType}
                    onChange={(e) => setFormData({...formData, documentType: e.target.value})}
                    placeholder="ID, Passport, License, etc."
                    required
                  />
                  <NeuInput
                    label="Document Number (optional)"
                    value={formData.documentNumber}
                    onChange={(e) => setFormData({...formData, documentNumber: e.target.value})}
                    placeholder="Last 4 digits only for security"
                  />
                  <NeuInput
                    label="Holder Name"
                    value={formData.holderName}
                    onChange={(e) => setFormData({...formData, holderName: e.target.value})}
                    placeholder="Name on document"
                  />
                  <NeuInput
                    label="Issuing Authority"
                    value={formData.issuingAuthority}
                    onChange={(e) => setFormData({...formData, issuingAuthority: e.target.value})}
                    placeholder="DMV, Embassy, etc."
                  />
                  <label style={styles.checkboxLabel}>
                    <input
                      type="checkbox"
                      checked={formData.isSensitive}
                      onChange={(e) => setFormData({...formData, isSensitive: e.target.checked})}
                    />
                    Contains sensitive information
                  </label>
                </>
              )}
              
              {activeTab === 'items' && (
                <>
                  <NeuInput
                    label="Item Type"
                    value={formData.itemType}
                    onChange={(e) => setFormData({...formData, itemType: e.target.value})}
                    placeholder="Bag, Phone, Wallet, etc."
                    required
                  />
                  <NeuInput
                    label="Brand"
                    value={formData.brand}
                    onChange={(e) => setFormData({...formData, brand: e.target.value})}
                    placeholder="Brand name"
                  />
                  <NeuInput
                    label="Color"
                    value={formData.color}
                    onChange={(e) => setFormData({...formData, color: e.target.value})}
                    placeholder="Primary color"
                  />
                  <NeuInput
                    label="Size"
                    value={formData.size}
                    onChange={(e) => setFormData({...formData, size: e.target.value})}
                    placeholder="Small, Medium, Large"
                  />
                  <NeuInput
                    label="Location Description"
                    value={formData.locationDescription}
                    onChange={(e) => setFormData({...formData, locationDescription: e.target.value})}
                    placeholder="Where was it left?"
                  />
                  <label style={styles.checkboxLabel}>
                    <input
                      type="checkbox"
                      checked={formData.containsValuables}
                      onChange={(e) => setFormData({...formData, containsValuables: e.target.checked})}
                    />
                    Contains valuables (cash, jewelry, etc.)
                  </label>
                </>
              )}
              
              <NeuInput
                label="Address/Location"
                value={formData.address}
                onChange={(e) => setFormData({...formData, address: e.target.value})}
                placeholder="Where was it lost?"
              />
              
              <div style={styles.modalActions}>
                <NeuButton
                  type="button"
                  variant="secondary"
                  onClick={() => setShowReportModal(false)}
                >
                  Cancel
                </NeuButton>
                <NeuButton type="submit" variant="primary" loading={loading}>
                  Submit Report
                </NeuButton>
              </div>
            </form>
          </NeuCard>
        </div>
      )}
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
    textShadow: '0 2px 4px rgba(0,0,0,0.2)',
  },
  subtitle: {
    fontSize: '1.1rem',
    color: 'rgba(255,255,255,0.9)',
    margin: 0,
  },
  tabs: {
    display: 'flex',
    gap: '10px',
    marginBottom: '20px',
    justifyContent: 'center',
    flexWrap: 'wrap',
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
    color: '#667eea',
    boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
  },
  actionBar: {
    display: 'flex',
    justifyContent: 'center',
    marginBottom: '30px',
  },
  itemsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '20px',
  },
  itemCard: {
    padding: '20px',
    background: 'rgba(255,255,255,0.95)',
  },
  cardHeader: {
    display: 'flex',
    gap: '8px',
    marginBottom: '12px',
    flexWrap: 'wrap',
  },
  itemTitle: {
    fontSize: '1.3rem',
    fontWeight: '600',
    color: '#333',
    margin: '0 0 10px 0',
  },
  itemDetail: {
    fontSize: '0.9rem',
    color: '#666',
    margin: '5px 0',
  },
  itemDescription: {
    fontSize: '0.95rem',
    color: '#555',
    margin: '10px 0',
    lineHeight: '1.5',
  },
  cardFooter: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: '15px',
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
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.7)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    padding: '20px',
    overflow: 'auto',
  },
  modal: {
    width: '100%',
    maxWidth: '600px',
    maxHeight: '90vh',
    overflow: 'auto',
    background: '#fff',
  },
  modalTitle: {
    fontSize: '1.8rem',
    fontWeight: '600',
    color: '#333',
    marginBottom: '20px',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px',
  },
  checkboxLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontSize: '0.95rem',
    color: '#555',
    cursor: 'pointer',
  },
  modalActions: {
    display: 'flex',
    gap: '10px',
    justifyContent: 'flex-end',
    marginTop: '20px',
  },
};

export default LostAndFoundPage;
