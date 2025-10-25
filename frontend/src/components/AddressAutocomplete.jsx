import React, { useState, useEffect, useRef } from 'react';
import { FaMapMarkerAlt, FaSearch } from 'react-icons/fa';
import './AddressAutocomplete.css';

const AddressAutocomplete = ({ 
  placeholder, 
  value, 
  onChange, 
  onSelect,
  className = "" 
}) => {
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);
  const timeoutRef = useRef(null);

  // Debounced search function
  const searchAddresses = async (query) => {
    if (query.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    setLoading(true);
    
    try {
      // Option 1: Google Places API (requires API key)
      if (window.google && window.google.maps && window.google.maps.places) {
        await searchWithGooglePlaces(query);
      } else {
        // Option 2: Free OpenStreetMap Nominatim API (no key required)
        await searchWithNominatim(query);
      }
    } catch (error) {
      console.error('Error fetching addresses:', error);
      // Fallback to mock data if API fails
      setSuggestions(getMockSuggestions(query));
      setShowSuggestions(true);
    } finally {
      setLoading(false);
    }
  };

  // Google Places API search
  const searchWithGooglePlaces = async (query) => {
    return new Promise((resolve, reject) => {
      const service = new window.google.maps.places.AutocompleteService();
      const request = {
        input: query,
        types: ['address'],
        componentRestrictions: { country: 'us' }
      };

      service.getPlacePredictions(request, (predictions, status) => {
        if (status === window.google.maps.places.PlacesServiceStatus.OK && predictions) {
          const formattedSuggestions = predictions.map(prediction => ({
            id: prediction.place_id,
            address: prediction.description,
            coordinates: null, // Will be filled when selected
            context: prediction.terms || []
          }));
          
          setSuggestions(formattedSuggestions);
          setShowSuggestions(true);
          resolve();
        } else {
          reject(new Error('Google Places API failed'));
        }
      });
    });
  };

  // Free OpenStreetMap Nominatim API (no key required)
  const searchWithNominatim = async (query) => {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&countrycodes=us&addressdetails=1`
      );
      
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      
      const data = await response.json();
      
      if (data && Array.isArray(data) && data.length > 0) {
        const formattedSuggestions = data.map(item => ({
          id: item.place_id || Math.random().toString(),
          address: item.display_name || 'Unknown address',
          coordinates: [parseFloat(item.lon) || 0, parseFloat(item.lat) || 0], // [lng, lat]
          context: item.address || []
        }));
        
        setSuggestions(formattedSuggestions);
        setShowSuggestions(true);
      } else {
        // Fallback to mock data
        setSuggestions(getMockSuggestions(query));
        setShowSuggestions(true);
      }
    } catch (error) {
      console.error('Nominatim API error:', error);
      // Fallback to mock data
      setSuggestions(getMockSuggestions(query));
      setShowSuggestions(true);
    }
  };

  // Mock suggestions as fallback
  const getMockSuggestions = (query) => {
    const mockAddresses = [
      { id: '1', address: 'UC Berkeley, Berkeley, CA', coordinates: [-122.2585, 37.8719] },
      { id: '2', address: 'Downtown Berkeley, Berkeley, CA', coordinates: [-122.2691, 37.8703] },
      { id: '3', address: 'Telegraph Ave, Berkeley, CA', coordinates: [-122.2585, 37.8726] },
      { id: '4', address: 'Shattuck Ave, Berkeley, CA', coordinates: [-122.2691, 37.8703] },
      { id: '5', address: 'Oakland, CA', coordinates: [-122.2711, 37.8044] },
      { id: '6', address: 'San Francisco, CA', coordinates: [-122.4194, 37.7749] }
    ];

    return mockAddresses.filter(addr => 
      addr.address.toLowerCase().includes(query.toLowerCase())
    );
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    onChange(value);

    // Clear previous timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Debounce the search
    timeoutRef.current = setTimeout(() => {
      searchAddresses(value);
    }, 300);
  };

  const handleSuggestionClick = (suggestion) => {
    onSelect({
      name: suggestion.address,
      lat: suggestion.coordinates[1],
      lng: suggestion.coordinates[0]
    });
    setShowSuggestions(false);
    setSuggestions([]);
  };

  const handleInputFocus = () => {
    if (suggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  const handleInputBlur = () => {
    // Delay hiding suggestions to allow clicks
    setTimeout(() => {
      setShowSuggestions(false);
    }, 200);
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return (
    <div className={`address-autocomplete ${className}`}>
      <div className="input-container">
        <FaMapMarkerAlt className="input-icon" />
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          onBlur={handleInputBlur}
          placeholder={placeholder}
          className="address-input"
          autoComplete="off"
        />
        {loading && <div className="loading-spinner" />}
      </div>

      {showSuggestions && suggestions.length > 0 && (
        <div className="suggestions-dropdown">
          {suggestions.map((suggestion) => (
            <div
              key={suggestion.id}
              className="suggestion-item"
              onClick={() => handleSuggestionClick(suggestion)}
            >
              <FaSearch className="suggestion-icon" />
              <div className="suggestion-content">
                <div className="suggestion-address">{suggestion.address}</div>
                {suggestion.context && Array.isArray(suggestion.context) && suggestion.context.length > 0 && (
                  <div className="suggestion-context">
                    {suggestion.context.map(ctx => ctx && ctx.text ? ctx.text : '').filter(text => text).join(', ')}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AddressAutocomplete;
