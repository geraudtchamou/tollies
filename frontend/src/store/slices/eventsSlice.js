import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';

const initialState = {
  events: [],
  selectedEvent: null,
  loading: false,
  error: null,
  filters: {
    category: null,
    status: null,
    radius_km: 10,
  },
};

export const fetchEvents = createAsyncThunk(
  'events/fetchEvents',
  async (filters, { rejectWithValue }) => {
    try {
      const params = new URLSearchParams();
      if (filters.category) params.append('category', filters.category);
      if (filters.status) params.append('status_filter', filters.status);
      if (filters.latitude) params.append('latitude', filters.latitude);
      if (filters.longitude) params.append('longitude', filters.longitude);
      if (filters.radius_km) params.append('radius_km', filters.radius_km);
      
      const response = await api.get(`/events/?${params.toString()}`);
      return response.data.events;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch events');
    }
  }
);

export const createEvent = createAsyncThunk(
  'events/createEvent',
  async (eventData, { rejectWithValue }) => {
    try {
      const response = await api.post('/events/', eventData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to create event');
    }
  }
);

export const voteOnEvent = createAsyncThunk(
  'events/voteOnEvent',
  async ({ eventId, voteType }, { rejectWithValue }) => {
    try {
      const response = await api.post(`/events/${eventId}/vote`, { vote_type: voteType });
      return { eventId, data: response.data };
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to vote');
    }
  }
);

export const triggerSOS = createAsyncThunk(
  'events/triggerSOS',
  async (sosData, { rejectWithValue }) => {
    try {
      const response = await api.post('/sos', sosData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to trigger SOS');
    }
  }
);

const eventsSlice = createSlice({
  name: 'events',
  initialState,
  reducers: {
    setSelectedEvent: (state, action) => {
      state.selectedEvent = action.payload;
    },
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    updateEventFromWS: (state, action) => {
      const { event_id, data } = action.payload;
      const index = state.events.findIndex(e => e.id === event_id);
      if (index !== -1) {
        state.events[index] = { ...state.events[index], ...data };
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchEvents.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchEvents.fulfilled, (state, action) => {
        state.loading = false;
        state.events = action.payload;
      })
      .addCase(fetchEvents.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(createEvent.fulfilled, (state, action) => {
        state.events.unshift(action.payload);
      })
      .addCase(voteOnEvent.fulfilled, (state, action) => {
        const { eventId, data } = action.payload;
        const event = state.events.find(e => e.id === eventId);
        if (event) {
          event.yes_votes = data.yes_votes;
          event.no_votes = data.no_votes;
          event.status = data.status;
        }
      });
  },
});

export const { setSelectedEvent, setFilters, updateEventFromWS } = eventsSlice.actions;
export default eventsSlice.reducer;
