import React, { useState, useEffect } from 'react';
import Map from './components/Map';
import './styles/App.css';

function App() {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [originSuggestions, setOriginSuggestions] = useState([]);
  const [destinationSuggestions, setDestinationSuggestions] = useState([]);
  const [showOriginSuggestions, setShowOriginSuggestions] = useState(false);
  const [showDestinationSuggestions, setShowDestinationSuggestions] = useState(false);
  const [selectedOrigin, setSelectedOrigin] = useState(null);
  const [selectedDestination, setSelectedDestination] = useState(null);
  const [routes, setRoutes] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Mock location data for autocomplete
  const locationData = [
    { name: "Moffitt Library, Berkeley", lat: 37.8726, lng: -122.2605 },
    { name: "Moffitt Field, CA", lat: 37.1234, lng: -121.5678 },
    { name: "Moffitt Ave, Berkeley", lat: 37.8765, lng: -122.2345 },
    { name: "Durant Ave, Berkeley", lat: 37.8720, lng: -122.2588 },
    { name: "2400 Block Durant Ave", lat: 37.8721, lng: -122.2589 },
    { name: "2500 Block Durant Ave", lat: 37.8719, lng: -122.2585 },
    { name: "Telegraph Ave, Berkeley", lat: 37.8722, lng: -122.2592 },
    { name: "College Ave, Berkeley", lat: 37.8725, lng: -122.2595 },
    { name: "Bancroft Way, Berkeley", lat: 37.8720, lng: -122.2592 }
  ];

  // Handle origin input change
  const handleOriginChange = (e) => {
    const value = e.target.value;
    setOrigin(value);
    
    if (value.length > 0) {
      const filtered = locationData.filter(location => 
        location.name.toLowerCase().includes(value.toLowerCase())
      );
      setOriginSuggestions(filtered);
      setShowOriginSuggestions(true);
    } else {
      setOriginSuggestions([]);
      setShowOriginSuggestions(false);
    }
  };

  // Handle destination input change
  const handleDestinationChange = (e) => {
    const value = e.target.value;
    setDestination(value);
    
    if (value.length > 0) {
      const filtered = locationData.filter(location => 
        location.name.toLowerCase().includes(value.toLowerCase())
      );
      setDestinationSuggestions(filtered);
      setShowDestinationSuggestions(true);
    } else {
      setDestinationSuggestions([]);
      setShowDestinationSuggestions(false);
    }
  };

  // Handle origin selection
  const handleOriginSelect = (location) => {
    setOrigin(location.name);
    setSelectedOrigin(location);
    setShowOriginSuggestions(false);
  };

  // Handle destination selection
  const handleDestinationSelect = (location) => {
    setDestination(location.name);
    setSelectedDestination(location);
    setShowDestinationSuggestions(false);
  };

  // Find route
  const handleFindRoute = async () => {
    if (!selectedOrigin || !selectedDestination) {
      setError('Please select both origin and destination');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/route', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start: [selectedOrigin.lat, selectedOrigin.lng],
          end: [selectedDestination.lat, selectedDestination.lng]
        })
      });

      if (!response.ok) {
        throw new Error('Failed to calculate route');
      }

      const routeData = await response.json();
      setRoutes(routeData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="search-container">
        <h1>SafePath Route Finder</h1>
        
        <div className="input-group">
          <label htmlFor="origin">Origin:</label>
          <div className="autocomplete-container">
            <input
              id="origin"
              type="text"
              value={origin}
              onChange={handleOriginChange}
              placeholder="Type location (e.g., 'moff')"
              className="location-input"
            />
            {showOriginSuggestions && originSuggestions.length > 0 && (
              <div className="suggestions">
                {originSuggestions.map((location, index) => (
                  <div
                    key={index}
                    className="suggestion-item"
                    onClick={() => handleOriginSelect(location)}
                  >
                    {location.name}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="input-group">
          <label htmlFor="destination">Destination:</label>
          <div className="autocomplete-container">
            <input
              id="destination"
              type="text"
              value={destination}
              onChange={handleDestinationChange}
              placeholder="Type location (e.g., 'dur')"
              className="location-input"
            />
            {showDestinationSuggestions && destinationSuggestions.length > 0 && (
              <div className="suggestions">
                {destinationSuggestions.map((location, index) => (
                  <div
                    key={index}
                    className="suggestion-item"
                    onClick={() => handleDestinationSelect(location)}
                  >
                    {location.name}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <button 
          className="find-route-btn"
          onClick={handleFindRoute}
          disabled={!selectedOrigin || !selectedDestination || loading}
        >
          {loading ? 'Finding Route...' : 'Find Route'}
        </button>

        {error && <div className="error-message">{error}</div>}
      </div>

      {routes && (
        <div className="results-container">
          <div className="route-comparison">
            <div className="route-card fastest">
              <h3>Fastest Route</h3>
              <p>Distance: {routes.fastest_route.distance_meters}m</p>
              <p>Time: {routes.fastest_route.estimated_time_min} min</p>
              <p>Safety Score: {routes.fastest_route.safety_score}/10</p>
              <p>Danger Score: {routes.fastest_route.danger_score}/100</p>
            </div>
            
            <div className="route-card safest">
              <h3>Safest Route</h3>
              <p>Distance: {routes.safest_route.distance_meters}m</p>
              <p>Time: {routes.safest_route.estimated_time_min} min</p>
              <p>Safety Score: {routes.safest_route.safety_score}/10</p>
              <p>Danger Score: {routes.safest_route.danger_score}/100</p>
            </div>
          </div>

          {routes.comparison && (
            <div className="comparison">
              <h3>Recommendation</h3>
              <p><strong>{routes.comparison.recommendation}</strong> route recommended</p>
              <p>Time difference: {routes.comparison.time_difference_min} minutes</p>
              <p>Safety improvement: {routes.comparison.safety_improvement} points</p>
              <p>{routes.comparison.reason}</p>
            </div>
          )}

          {routes.warnings && routes.warnings.length > 0 && (
            <div className="warnings">
              <h3>Warnings</h3>
              {routes.warnings.map((warning, index) => (
                <div key={index} className={`warning ${warning.severity}`}>
                  {warning.message}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <Map 
        origin={selectedOrigin}
        destination={selectedDestination}
        routes={routes}
      />
    </div>
  );
}

export default App;
