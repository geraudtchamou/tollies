import React from 'react';
import { Routes, Route } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import MapPage from './pages/MapPage';
import EventDetailPage from './pages/EventDetailPage';
import SOSPage from './pages/SOSPage';
import LeaderboardPage from './pages/LeaderboardPage';
import LostAndFoundPage from './pages/LostAndFoundPage';
import TransportPage from './pages/TransportPage';
import AnalyticsDashboard from './pages/AnalyticsDashboard';
import PrivateRoute from './components/PrivateRoute';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/sos" element={<SOSPage />} />
      <Route path="/leaderboard" element={<LeaderboardPage />} />
      <Route path="/lost-found" element={<LostAndFoundPage />} />
      <Route path="/transport" element={<TransportPage />} />
      <Route path="/analytics" element={<AnalyticsDashboard />} />

      {/* Protected routes */}
      <Route path="/" element={
        <PrivateRoute>
          <MapPage />
        </PrivateRoute>
      } />
      <Route path="/event/:id" element={
        <PrivateRoute>
          <EventDetailPage />
        </PrivateRoute>
      } />
    </Routes>
  );
}

export default App;
