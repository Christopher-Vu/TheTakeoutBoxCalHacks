import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import ReportIncident from './components/ReportIncident';
import RoutePlanning from './components/RoutePlanning';

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/report-incident" element={<ReportIncident />} />
          <Route path="/route-planning" element={<RoutePlanning />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
