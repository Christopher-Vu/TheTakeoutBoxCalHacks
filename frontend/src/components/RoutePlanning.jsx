import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FaArrowLeft,
  FaWalking,
  FaBicycle,
  FaBus,
  FaCar,
  FaSearch,
  FaChevronDown,
  FaChevronUp,
  FaArrowRight,
  FaArrowUp,
  FaCheckCircle,
  FaExpand,
  FaLayerGroup,
  FaPlus,
  FaMinus,
  FaCrosshairs
} from 'react-icons/fa';
import {
  generateMockRoutes,
  generateMockDirections,
  getSafetyScoreColor,
  getSafetyScoreLabel
} from '../utils/mockData';
import AddressAutocomplete from './AddressAutocomplete';
import './RoutePlanning.css';

const RoutePlanning = () => {
  const navigate = useNavigate();
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [selectedOrigin, setSelectedOrigin] = useState(null);
  const [selectedDestination, setSelectedDestination] = useState(null);
  const [travelMode, setTravelMode] = useState('walking');
  const [routes, setRoutes] = useState([]);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [directions, setDirections] = useState([]);
  const [directionsExpanded, setDirectionsExpanded] = useState(true);
  const [isSearching, setIsSearching] = useState(false);

  const travelModes = [
    { id: 'walking', icon: FaWalking, label: 'Walking' },
    { id: 'biking', icon: FaBicycle, label: 'Biking' },
  ];

  const handleFindRoutes = () => {
    if (!selectedOrigin || !selectedDestination) return;

    setIsSearching(true);
    // Simulate API call
    setTimeout(() => {
      const mockRoutes = generateMockRoutes(selectedOrigin.name, selectedDestination.name, travelMode);
      setRoutes(mockRoutes);
      setSelectedRoute(null);
      setDirections([]);
      setIsSearching(false);
    }, 1000);
  };

  const handleOriginSelect = (location) => {
    setSelectedOrigin(location);
    setOrigin(location.name);
  };

  const handleDestinationSelect = (location) => {
    setSelectedDestination(location);
    setDestination(location.name);
  };

  const handleSelectRoute = (route) => {
    setSelectedRoute(route);
    const mockDirections = generateMockDirections(route.id);
    setDirections(mockDirections);
    setDirectionsExpanded(true);
  };

  const getManeuverIcon = (maneuver) => {
    switch (maneuver) {
      case 'turn-left':
      case 'turn-right':
        return FaArrowUp;
      case 'straight':
        return FaArrowRight;
      case 'arrive':
        return FaCheckCircle;
      default:
        return FaArrowRight;
    }
  };

  return (
    <div className="route-planning-page">
      <aside className="route-sidebar">
        <div className="sidebar-header">
          <button className="btn-back" onClick={() => navigate('/')}>
            <FaArrowLeft /> Back
          </button>
          <h1>Plan Your Route</h1>
        </div>

        <div className="route-inputs">
          <AddressAutocomplete
            placeholder="Starting location"
            value={origin}
            onChange={setOrigin}
            onSelect={handleOriginSelect}
            className="origin-autocomplete"
          />

          <AddressAutocomplete
            placeholder="Destination"
            value={destination}
            onChange={setDestination}
            onSelect={handleDestinationSelect}
            className="destination-autocomplete"
          />
        </div>

        <div className="travel-modes">
          {travelModes.map((mode) => {
            const Icon = mode.icon;
            return (
              <button
                key={mode.id}
                className={`mode-button ${travelMode === mode.id ? 'active' : ''}`}
                onClick={() => setTravelMode(mode.id)}
              >
                <Icon />
                <span>{mode.label}</span>
              </button>
            );
          })}
        </div>

        <button
          className="btn btn-primary btn-lg find-routes-btn"
          onClick={handleFindRoutes}
          disabled={!selectedOrigin || !selectedDestination || isSearching}
        >
          <FaSearch />
          {isSearching ? 'Searching...' : 'Find Routes'}
        </button>

        {routes.length > 0 && !selectedRoute && (
          <div className="routes-results">
            <h3>Route Options</h3>
            {routes.map((route) => (
              <div key={route.id} className="route-card fade-in">
                <div className="route-header">
                  <div className="route-info">
                    <span className="route-duration">{route.duration}</span>
                    <span className="route-distance">{route.distance}</span>
                  </div>
                </div>

                <div className="route-description">{route.description}</div>

                <div className="safety-score-section">
                  <div className="safety-label">
                    <span>Safety Score</span>
                    <span className="score-value">{route.safetyScore}/100</span>
                  </div>
                  <div className="safety-bar">
                    <div
                      className="safety-fill"
                      style={{
                        width: `${route.safetyScore}%`,
                        background: getSafetyScoreColor(route.safetyScore)
                      }}
                    />
                  </div>
                  <div className="safety-status" style={{ color: getSafetyScoreColor(route.safetyScore) }}>
                    {getSafetyScoreLabel(route.safetyScore)}
                  </div>
                </div>

                <button
                  className="btn btn-primary select-route-btn"
                  onClick={() => handleSelectRoute(route)}
                >
                  Select Route
                </button>
              </div>
            ))}
          </div>
        )}

        {selectedRoute && directions.length > 0 && (
          <div className="directions-section">
            <div className="directions-header" onClick={() => setDirectionsExpanded(!directionsExpanded)}>
              <h3>Turn-by-Turn Directions</h3>
              <button className="expand-btn">
                {directionsExpanded ? <FaChevronUp /> : <FaChevronDown />}
              </button>
            </div>

            {directionsExpanded && (
              <div className="directions-list">
                {directions.map((step, index) => {
                  const Icon = getManeuverIcon(step.maneuver);
                  return (
                    <div
                      key={step.id}
                      className="direction-step"
                      style={{ animationDelay: `${index * 0.05}s` }}
                    >
                      <div className="step-icon">
                        <Icon />
                      </div>
                      <div className="step-content">
                        <div className="step-instruction">{step.instruction}</div>
                        {step.distance !== '0 mi' && (
                          <div className="step-meta">
                            {step.distance} · {step.duration}
                          </div>
                        )}
                        {step.safetyNote && (
                          <div className="safety-note">
                            ⚠️ {step.safetyNote}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}

                <div className="directions-summary">
                  <div className="summary-item">
                    <strong>Total Distance:</strong> {selectedRoute.distance}
                  </div>
                  <div className="summary-item">
                    <strong>Estimated Time:</strong> {selectedRoute.duration}
                  </div>
                  <div className="summary-item">
                    <strong>Safety Score:</strong>{' '}
                    <span style={{ color: getSafetyScoreColor(selectedRoute.safetyScore) }}>
                      {selectedRoute.safetyScore}/100
                    </span>
                  </div>
                </div>

                <button className="btn btn-success btn-lg start-nav-btn">
                  Start Navigation
                </button>

                <button
                  className="btn btn-outline view-routes-btn"
                  onClick={() => {
                    setSelectedRoute(null);
                    setDirections([]);
                  }}
                >
                  View All Routes
                </button>
              </div>
            )}
          </div>
        )}
      </aside>

      <div className="map-container">
        <div className="map-placeholder">
          <div className="map-grid-pattern"></div>
          <div className="map-overlay-content">
            <div className="map-badge">
              <FaLayerGroup /> Map Integration Coming Soon
            </div>
            <p className="map-placeholder-text">
              Interactive map with safety indicators and route visualization will be displayed here
            </p>
          </div>

          <div className="map-controls">
            <button className="map-control-btn" title="Zoom in">
              <FaPlus />
            </button>
            <button className="map-control-btn" title="Zoom out">
              <FaMinus />
            </button>
            <button className="map-control-btn" title="Center location">
              <FaCrosshairs />
            </button>
            <button className="map-control-btn" title="Toggle layers">
              <FaLayerGroup />
            </button>
            <button className="map-control-btn" title="Fullscreen">
              <FaExpand />
            </button>
          </div>

          {selectedRoute && (
            <div className="selected-route-overlay card">
              <h4>Selected Route</h4>
              <div className="overlay-route-info">
                <div className="overlay-stat">
                  <div className="stat-value">{selectedRoute.duration}</div>
                  <div className="stat-label">Duration</div>
                </div>
                <div className="overlay-stat">
                  <div className="stat-value">{selectedRoute.distance}</div>
                  <div className="stat-label">Distance</div>
                </div>
                <div className="overlay-stat">
                  <div className="stat-value" style={{ color: getSafetyScoreColor(selectedRoute.safetyScore) }}>
                    {selectedRoute.safetyScore}
                  </div>
                  <div className="stat-label">Safety</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RoutePlanning;
