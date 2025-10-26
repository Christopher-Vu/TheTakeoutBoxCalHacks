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
import { routingAPI } from '../utils/api';
import AddressAutocomplete from './AddressAutocomplete';
import Map from './Map';
import SafetyDashboard from './SafetyDashboard';
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
  const [routeType, setRouteType] = useState('balanced');

  const travelModes = [
    { id: 'walking', icon: FaWalking, label: 'Walking' },
    { id: 'biking', icon: FaBicycle, label: 'Biking' },
  ];

  const handleFindRoutes = async () => {
    if (!selectedOrigin || !selectedDestination) return;

    setIsSearching(true);
    
    try {
      // Call crime-aware routing API
      const crimeAwareRoute = await routingAPI.getCrimeAwareRoute(
        selectedOrigin.lat,
        selectedOrigin.lng,
        selectedDestination.lat,
        selectedDestination.lng,
        routeType
      );
      
      // Transform API response to match Map component expectations
      const transformedRoutes = {
        path_coordinates: crimeAwareRoute.path_coordinates,
        segments: crimeAwareRoute.segments,
        crime_density_map: crimeAwareRoute.crime_density_map,
        critical_crime_zones: crimeAwareRoute.critical_crime_zones,
        route_safety_breakdown: crimeAwareRoute.route_safety_breakdown,
        total_distance: crimeAwareRoute.total_distance,
        total_safety_score: crimeAwareRoute.total_safety_score,
        route_type: crimeAwareRoute.route_type
      };
      
      setRoutes([transformedRoutes]);
      setSelectedRoute(transformedRoutes);
      setDirections([]);
      
    } catch (error) {
      console.error('Error fetching crime-aware route:', error);
      // Fallback to mock data if API fails
      const mockRoutes = generateMockRoutes(selectedOrigin.name, selectedDestination.name, travelMode);
      setRoutes(mockRoutes);
      setSelectedRoute(null);
    } finally {
      setIsSearching(false);
    }
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

        <div className="route-type-selector">
          <label>Route Priority:</label>
          <div className="route-type-buttons">
            <button 
              className={`route-type-btn ${routeType === 'safest' ? 'active' : ''}`}
              onClick={() => setRouteType('safest')}
            >
              🛡️ Safest
            </button>
            <button 
              className={`route-type-btn ${routeType === 'balanced' ? 'active' : ''}`}
              onClick={() => setRouteType('balanced')}
            >
              ⚖️ Balanced
            </button>
            <button 
              className={`route-type-btn ${routeType === 'fastest' ? 'active' : ''}`}
              onClick={() => setRouteType('fastest')}
            >
              ⚡ Fastest
            </button>
          </div>
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
        <Map 
          origin={selectedOrigin}
          destination={selectedDestination}
          routes={selectedRoute}
        />
      </div>

      {selectedRoute && selectedRoute.route_safety_breakdown && (
        <SafetyDashboard safetyBreakdown={selectedRoute.route_safety_breakdown} />
      )}
    </div>
  );
};

export default RoutePlanning;
