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

  // Transform backend route data to UI format
  const transformBackendRoute = (backendData, routeType = 'balanced') => {
    // Convert meters to miles
    const distanceMiles = (backendData.total_distance / 1609.34).toFixed(1);

    // Estimate duration based on distance and travel mode
    // Walking: ~3 mph, Biking: ~10 mph
    const speedMph = travelMode === 'walking' ? 3 : 10;
    const durationMinutes = Math.round((parseFloat(distanceMiles) / speedMph) * 60);

    return {
      id: routeType,
      duration: `${durationMinutes} min`,
      distance: `${distanceMiles} mi`,
      description: `${routeType.charAt(0).toUpperCase() + routeType.slice(1)} route via crime-aware pathfinding`,
      safetyScore: Math.round(backendData.total_safety_score),
      pathCoordinates: backendData.path_coordinates,
      segments: backendData.segments,
      crimeZones: backendData.critical_crime_zones || [],
      crimeData: backendData.crime_density_map || {},
      safetyBreakdown: backendData.route_safety_breakdown || {}
    };
  };

  const handleFindRoutes = async () => {
    if (!selectedOrigin || !selectedDestination) return;

    setIsSearching(true);

    try {
      console.log('Requesting route from API:', {
        start: { lat: selectedOrigin.lat, lng: selectedOrigin.lng },
        end: { lat: selectedDestination.lat, lng: selectedDestination.lng },
        mode: travelMode
      });

      // Call the crime-aware routing API
      const backendData = await routingAPI.getCrimeAwareRoute(
        selectedOrigin.lat,
        selectedOrigin.lng,
        selectedDestination.lat,
        selectedDestination.lng,
        'balanced' // Can map travelMode to route_type if needed
      );

      console.log('Received route from API:', backendData);

      // Transform backend data to UI format
      const transformedRoute = transformBackendRoute(backendData, 'balanced');

      setRoutes([transformedRoute]);
      setSelectedRoute(null);
      setDirections([]);

    } catch (error) {
      console.error('Error fetching route from API:', error);

      // Fallback to mock data on error
      console.log('Falling back to mock data...');
      const mockRoutes = generateMockRoutes(selectedOrigin.name, selectedDestination.name, travelMode);
      setRoutes(mockRoutes);
      setSelectedRoute(null);
      setDirections([]);

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
        <div className="route-header">
          <button className="btn-back" onClick={() => navigate('/')}>
            <FaArrowLeft /> Back to Home
          </button>
          <h1>Find Routes</h1>
          <p className="route-subtitle">Plan your journey with maximum safety in mind</p>
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
