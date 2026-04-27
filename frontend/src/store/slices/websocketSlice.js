import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  connected: false,
  liveFeed: [],
  notifications: [],
};

const websocketSlice = createSlice({
  name: 'websocket',
  initialState,
  reducers: {
    setConnected: (state, action) => {
      state.connected = action.payload;
    },
    addNotification: (state, action) => {
      state.notifications.unshift({
        id: Date.now(),
        ...action.payload,
        read: false,
      });
      // Keep only last 50 notifications
      if (state.notifications.length > 50) {
        state.notifications = state.notifications.slice(0, 50);
      }
    },
    markNotificationRead: (state, action) => {
      const notification = state.notifications.find(n => n.id === action.payload);
      if (notification) {
        notification.read = true;
      }
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
    updateLiveFeed: (state, action) => {
      state.liveFeed = action.payload;
    },
    addLiveEvent: (state, action) => {
      const exists = state.liveFeed.find(e => e.id === action.payload.id);
      if (!exists) {
        state.liveFeed.unshift(action.payload);
        if (state.liveFeed.length > 100) {
          state.liveFeed.pop();
        }
      }
    },
  },
});

export const {
  setConnected,
  addNotification,
  markNotificationRead,
  clearNotifications,
  updateLiveFeed,
  addLiveEvent,
} = websocketSlice.actions;

export default websocketSlice.reducer;
