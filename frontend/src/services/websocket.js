class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.listeners = [];
    this.eventListeners = new Map();
  }

  connect(userId) {
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/events';
    
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      
      // Subscribe to live feed
      this.send({ action: 'get_live_feed' });
      
      if (userId) {
        this.updateLocation(userId);
      }
      
      this.notifyListeners({ type: 'connected' });
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.notifyListeners({ type: 'disconnected' });
      this.attemptReconnect(userId);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  handleMessage(message) {
    console.log('Received WebSocket message:', message);
    
    // Notify all listeners
    this.notifyListeners(message);
    
    // Handle specific event types
    if (message.event_id && this.eventListeners.has(message.event_id)) {
      this.eventListeners.get(message.event_id)(message);
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket not connected, cannot send:', data);
    }
  }

  subscribeToEvent(eventId, callback) {
    this.send({ action: 'subscribe', event_id: eventId });
    this.eventListeners.set(eventId, callback);
    
    return () => {
      this.unsubscribeFromEvent(eventId);
    };
  }

  unsubscribeFromEvent(eventId) {
    this.send({ action: 'unsubscribe', event_id: eventId });
    this.eventListeners.delete(eventId);
  }

  updateLocation(userId, latitude, longitude) {
    if (latitude && longitude) {
      this.send({
        action: 'update_location',
        user_id: userId,
        latitude,
        longitude,
      });
    }
  }

  addListener(callback) {
    this.listeners.push(callback);
    return () => {
      this.removeListener(callback);
    };
  }

  removeListener(callback) {
    this.listeners = this.listeners.filter(l => l !== callback);
  }

  notifyListeners(message) {
    this.listeners.forEach(listener => listener(message));
  }

  attemptReconnect(userId) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      
      console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
      
      setTimeout(() => {
        this.connect(userId);
      }, delay);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.listeners = [];
    this.eventListeners.clear();
  }
}

// Singleton instance
const websocketService = new WebSocketService();

export default websocketService;
