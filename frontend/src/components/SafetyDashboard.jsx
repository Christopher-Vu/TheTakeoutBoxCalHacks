import React from 'react';
import './SafetyDashboard.css';

const SafetyDashboard = ({ safetyBreakdown }) => {
  if (!safetyBreakdown) return null;

  return (
    <div className="safety-dashboard">
      <h3>Route Safety Analysis</h3>
      
      <div className="safety-grade">
        <div className={`grade-badge grade-${safetyBreakdown.route_safety_summary?.safety_grade || 'B'}`}>
          {safetyBreakdown.route_safety_summary?.safety_grade || 'B'}
        </div>
        <span>Safety Grade</span>
      </div>

      <div className="safety-metrics">
        <div className="metric">
          <span className="metric-value">{safetyBreakdown['24h_crimes_avoided'] || 0}</span>
          <span className="metric-label">24h Crimes Avoided</span>
        </div>
        <div className="metric">
          <span className="metric-value">{safetyBreakdown.high_severity_crimes_avoided || 0}</span>
          <span className="metric-label">High-Risk Areas Avoided</span>
        </div>
        <div className="metric">
          <span className="metric-value">{(safetyBreakdown.average_crime_density || 0).toFixed(1)}</span>
          <span className="metric-label">Avg Crime Density</span>
        </div>
      </div>

      <div className="most-dangerous-segment">
        <h4>⚠️ Most Cautious Segment</h4>
        <p>Safety Score: {(safetyBreakdown.most_dangerous_segment?.safety_score || 0).toFixed(1)}</p>
        <p>Crime Density: {safetyBreakdown.most_dangerous_segment?.crime_density || 0}</p>
        <p>24h Crimes: {safetyBreakdown.most_dangerous_segment?.critical_crimes_24h || 0}</p>
      </div>
    </div>
  );
};

export default SafetyDashboard;
