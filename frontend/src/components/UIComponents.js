/**
 * Advanced UI Components with Neumorphism & Glassmorphism
 * Reusable, responsive, and animated components
 */
import React from 'react';

// Button Component with variants
export const NeuButton = ({ 
  children, 
  variant = 'default', 
  size = 'md', 
  icon, 
  loading = false,
  onClick,
  className = '',
  ...props 
}) => {
  const baseClass = 'neu-btn';
  const variantClass = variant === 'primary' ? 'neu-btn-primary' : 
                       variant === 'success' ? 'neu-btn-success' :
                       variant === 'danger' ? 'neu-btn-danger' : '';
  const sizeClass = size === 'sm' ? 'text-sm p-2' : 
                    size === 'lg' ? 'text-lg p-4' : '';
  
  return (
    <button 
      className={`${baseClass} ${variantClass} ${sizeClass} ${className}`}
      onClick={onClick}
      disabled={loading}
      {...props}
    >
      {loading ? (
        <span className="animate-shimmer" style={{width: '20px', height: '20px', display: 'inline-block'}}></span>
      ) : (
        <>
          {icon && <span>{icon}</span>}
          {children}
        </>
      )}
    </button>
  );
};

// Card Component
export const NeuCard = ({ children, className = '', hover = true, ...props }) => {
  return (
    <div className={`glass-card ${hover ? '' : 'no-hover'} ${className}`} {...props}>
      {children}
    </div>
  );
};

// Glass Panel
export const GlassPanel = ({ children, className = '', blur = 12, ...props }) => {
  const style = {
    backdropFilter: `blur(${blur}px)`,
    WebkitBackdropFilter: `blur(${blur}px)`
  };
  
  return (
    <div className={`glass-panel ${className}`} style={style} {...props}>
      {children}
    </div>
  );
};

// Input Component
export const NeuInput = ({ 
  label, 
  icon, 
  error, 
  className = '', 
  ...props 
}) => {
  return (
    <div className={`w-full ${className}`}>
      {label && <label className="text-sm font-bold mb-2 block">{label}</label>}
      <div className="relative">
        {icon && (
          <span style={{
            position: 'absolute',
            left: '1rem',
            top: '50%',
            transform: 'translateY(-50%)',
            zIndex: 1
          }}>
            {icon}
          </span>
        )}
        <input 
          className={`neu-input ${icon ? 'pl-12' : ''}`}
          {...props} 
        />
      </div>
      {error && <p className="text-danger text-xs mt-1">{error}</p>}
    </div>
  );
};

// Icon Button
export const IconButton = ({ icon, size = 'md', variant = 'default', onClick, className = '', ...props }) => {
  const sizeClass = size === 'sm' ? 'w-8 h-8' : 
                    size === 'lg' ? 'w-14 h-14' : 'w-10 h-10';
  
  return (
    <button 
      className={`neu-btn ${sizeClass} rounded-full p-0 ${className}`}
      onClick={onClick}
      {...props}
    >
      {icon}
    </button>
  );
};

// Badge Component
export const Badge = ({ children, variant = 'default', size = 'md', className = '', ...props }) => {
  const variantStyles = {
    default: { background: 'var(--bg-body)', color: 'var(--text-main)' },
    primary: { background: 'var(--primary)', color: 'white' },
    success: { background: 'var(--success)', color: 'white' },
    warning: { background: 'var(--warning)', color: 'white' },
    danger: { background: 'var(--danger)', color: 'white' },
    info: { background: 'var(--info)', color: 'white' },
  };
  
  const sizeClass = size === 'sm' ? 'text-xs px-2 py-0.5' : 
                    size === 'lg' ? 'text-base px-4 py-1' : 'text-sm px-3 py-0.5';
  
  return (
    <span 
      className={`rounded-full font-bold ${sizeClass} ${className}`}
      style={variantStyles[variant]}
      {...props}
    >
      {children}
    </span>
  );
};

// Skeleton Loader
export const Skeleton = ({ width = '100%', height = '1rem', className = '', ...props }) => {
  return (
    <div 
      className={`skeleton ${className}`}
      style={{ width, height }}
      {...props}
    />
  );
};

// Status Indicator with Animation
export const StatusIndicator = ({ status = 'pending', size = 'md', className = '' }) => {
  const colors = {
    pending: 'var(--warning)',
    validated: 'var(--success)',
    invalidated: 'var(--danger)',
    live: 'var(--primary)'
  };
  
  const sizeClass = size === 'sm' ? 'w-2 h-2' : 
                    size === 'lg' ? 'w-4 h-4' : 'w-3 h-3';
  
  const animation = status === 'live' ? 'animate-pulse-glow' : '';
  
  return (
    <span 
      className={`${sizeClass} rounded-full ${animation}`}
      style={{ 
        backgroundColor: colors[status] || colors.pending,
        display: 'inline-block'
      }}
      className={className}
    />
  );
};

// Event Card Component
export const EventCard = ({ event, onClick }) => {
  const statusColors = {
    pending: 'warning',
    validated: 'success',
    invalidated: 'danger'
  };
  
  return (
    <NeuCard className="animate-slide-up" style={{ cursor: 'pointer' }} onClick={onClick}>
      <div className="flex justify-between items-start mb-3">
        <Badge variant={statusColors[event.status]}>{event.status}</Badge>
        <StatusIndicator status={event.status} />
      </div>
      
      <h3 className="text-xl font-bold mb-2">{event.title}</h3>
      <p className="text-muted text-sm mb-3">{event.description}</p>
      
      <div className="flex items-center gap-2 text-xs text-muted">
        <span>📍 {event.location_name}</span>
        <span>•</span>
        <span>👁️ {event.view_count || 0}</span>
        <span>•</span>
        <span>❤️ {event.like_count || 0}</span>
      </div>
      
      {event.image_url && (
        <img 
          src={event.image_url} 
          alt={event.title}
          style={{ width: '100%', borderRadius: 'var(--radius-md)', marginTop: '1rem' }}
        />
      )}
    </NeuCard>
  );
};

// Navigation Item
export const NavItem = ({ icon, label, active, onClick }) => {
  return (
    <button
      className={`flex flex-col items-center gap-1 p-2 rounded-lg transition-all ${
        active ? 'text-primary neu-pressed' : 'text-muted'
      }`}
      onClick={onClick}
    >
      <span className="text-xl">{icon}</span>
      <span className="text-xs">{label}</span>
    </button>
  );
};

// Loading Spinner
export const LoadingSpinner = ({ size = 'md', color = 'var(--primary)' }) => {
  const sizeClass = size === 'sm' ? 'w-4 h-4' : 
                    size === 'lg' ? 'w-12 h-12' : 'w-8 h-8';
  
  return (
    <div 
      className={`${sizeClass} rounded-full border-4 animate-spin`}
      style={{ 
        borderColor: `${color}20`,
        borderTopColor: color,
        margin: '0 auto'
      }}
    />
  );
};

// Modal Component
export const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;
  
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.5)',
      backdropFilter: 'blur(4px)',
      zIndex: 2000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 'var(--space-md)'
    }}>
      <div className="glass-card animate-slide-up" style={{ maxWidth: '500px', width: '100%', maxHeight: '90vh', overflow: 'auto' }}>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">{title}</h2>
          <IconButton icon="✕" onClick={onClose} size="sm" />
        </div>
        {children}
      </div>
    </div>
  );
};

export default {
  NeuButton,
  NeuCard,
  GlassPanel,
  NeuInput,
  IconButton,
  Badge,
  Skeleton,
  StatusIndicator,
  EventCard,
  NavItem,
  LoadingSpinner,
  Modal
};
