import React, { useEffect, useRef, useState, useCallback } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import './Map.css';
import { crimeAPI } from '../utils/api';

const Map = ({ origin, destination, routes }) => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [crimeMarkers, setCrimeMarkers] = useState([]);

  // Function to fetch and display crime markers
  const fetchCrimeMarkers = useCallback(async () => {
    if (!map.current) return;

    try {
      const bounds = map.current.getBounds();
      const crimesData = await crimeAPI.getRecent24HourCrimes(
        bounds.getSouth(),
        bounds.getNorth(),
        bounds.getWest(),
        bounds.getEast()
      );

      // Clear existing crime markers
      crimeMarkers.forEach(marker => marker.remove());
      setCrimeMarkers([]);

      // Create new markers for each crime
      const newMarkers = [];
      crimesData.crimes.forEach(crime => {
        const el = document.createElement('div');
        el.className = 'crime-marker';
        el.style.width = '20px';
        el.style.height = '20px';
        el.style.borderRadius = '50%';
        el.style.backgroundColor = '#DC3545';
        el.style.border = '2px solid #fff';
        el.style.boxShadow = '0 0 8px rgba(220,53,69,0.6)';
        el.style.cursor = 'pointer';

        const marker = new mapboxgl.Marker(el)
          .setLngLat([crime.lng, crime.lat])
          .setPopup(
            new mapboxgl.Popup({ offset: 25 })
              .setHTML(`
                <div style="padding: 8px; min-width: 200px;">
                  <h4 style="margin: 0 0 8px 0; color: #DC3545;">${crime.crime_type}</h4>
                  <p style="margin: 4px 0;"><strong>Severity:</strong> ${crime.severity}/10</p>
                  <p style="margin: 4px 0;"><strong>Time:</strong> ${new Date(crime.occurred_at).toLocaleString()}</p>
                  <p style="margin: 4px 0;"><strong>Address:</strong> ${crime.address || 'Unknown'}</p>
                  <p style="margin: 4px 0;"><strong>Agency:</strong> ${crime.agency || 'Unknown'}</p>
                  ${crime.description ? `<p style="margin: 4px 0;"><strong>Description:</strong> ${crime.description}</p>` : ''}
                </div>
              `)
          )
          .addTo(map.current);

        newMarkers.push(marker);
      });

      setCrimeMarkers(newMarkers);
    } catch (error) {
      console.error('Error fetching crime markers:', error);
    }
  }, [crimeMarkers]);

  useEffect(() => {
    if (map.current) return; // Initialize map only once

    mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN || 'pk.eyJ1IjoiZXhhbXBsZSIsImEiOiJja2VhZXhhbXBsZSJ9.example';
    
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/streets-v11',
      center: [-122.2585, 37.8726], // Berkeley center
      zoom: 15
    });

    map.current.on('load', () => {
      // Add navigation controls
      map.current.addControl(new mapboxgl.NavigationControl());
      
      // Fetch initial crime data
      fetchCrimeMarkers();
    });
  }, [fetchCrimeMarkers]);

  // Fetch crime markers when map moves
  useEffect(() => {
    if (!map.current) return;

    const handleMoveEnd = () => {
      fetchCrimeMarkers();
    };

    map.current.on('moveend', handleMoveEnd);
    map.current.on('zoomend', handleMoveEnd);

    return () => {
      if (map.current) {
        map.current.off('moveend', handleMoveEnd);
        map.current.off('zoomend', handleMoveEnd);
      }
    };
  }, [fetchCrimeMarkers]);

  useEffect(() => {
    if (!map.current || !origin || !destination) return;

    // Clear existing markers and routes
    const markers = document.querySelectorAll('.mapboxgl-marker');
    markers.forEach(marker => marker.remove());

    // Add origin marker
    new mapboxgl.Marker({ color: '#2E8B57' })
      .setLngLat([origin.lng, origin.lat])
      .setPopup(new mapboxgl.Popup().setHTML(`<strong>Origin:</strong> ${origin.name}`))
      .addTo(map.current);

    // Add destination marker
    new mapboxgl.Marker({ color: '#DC143C' })
      .setLngLat([destination.lng, destination.lat])
      .setPopup(new mapboxgl.Popup().setHTML(`<strong>Destination:</strong> ${destination.name}`))
      .addTo(map.current);

    // Fit map to show both points
    const bounds = new mapboxgl.LngLatBounds();
    bounds.extend([origin.lng, origin.lat]);
    bounds.extend([destination.lng, destination.lat]);
    map.current.fitBounds(bounds, { padding: 50 });
  }, [origin, destination]);

  useEffect(() => {
    if (!map.current || !routes) return;

    // Remove existing route sources
    if (map.current.getSource('route')) {
      map.current.removeLayer('route');
      map.current.removeSource('route');
    }
    if (map.current.getSource('route-trail')) {
      map.current.removeLayer('route-trail');
      map.current.removeSource('route-trail');
    }
    if (map.current.getSource('fastest-route')) {
      map.current.removeLayer('fastest-route');
      map.current.removeSource('fastest-route');
    }
    if (map.current.getSource('safest-route')) {
      map.current.removeLayer('safest-route');
      map.current.removeSource('safest-route');
    }
    if (map.current.getSource('crime-points')) {
      map.current.removeLayer('crime-points');
      map.current.removeSource('crime-points');
    }
    if (map.current.getLayer('crime-heatmap')) {
      map.current.removeLayer('crime-heatmap');
      map.current.removeSource('crime-heatmap');
    }
    if (map.current.getLayer('critical-crime-zones')) {
      map.current.removeLayer('critical-crime-zones');
      map.current.removeSource('critical-crime-zones');
    }
    // Remove existing segment layers
    for (let i = 0; i < 50; i++) { // Remove up to 50 segment layers
      if (map.current.getLayer(`segment-layer-${i}`)) {
        map.current.removeLayer(`segment-layer-${i}`);
        map.current.removeSource(`segment-${i}`);
      }
    }

    // Add animated route from backend data
    if (routes && routes.pathCoordinates && routes.pathCoordinates.length > 0) {
      const coordinates = routes.pathCoordinates.map(coord => [coord[1], coord[0]]); // Convert [lat, lng] to [lng, lat]
      
      // Add the route source (starts empty)
      map.current.addSource('route', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {
            safetyScore: routes.safetyScore || 0,
            distance: routes.distance || '',
            duration: routes.duration || ''
          },
          geometry: {
            type: 'LineString',
            coordinates: []
          }
        }
      });

      // Add the animated route layer
      map.current.addLayer({
        id: 'route',
        type: 'line',
        source: 'route',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#4ECDC4', // Teal color for crime-aware route
          'line-width': 6,
          'line-opacity': 0.8
        }
      });

      // Add animated route trail layer
      map.current.addSource('route-trail', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: {
            type: 'LineString',
            coordinates: []
          }
        }
      });

      map.current.addLayer({
        id: 'route-trail',
        type: 'line',
        source: 'route-trail',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#4ECDC4',
          'line-width': 8,
          'line-opacity': 0.8
        }
      });

      // Animate the route drawing
      animateRouteDrawing(coordinates, routes);
    }

    // Add safest route
    if (routes.safest_route && routes.safest_route.path) {
      map.current.addSource('safest-route', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: {
            type: 'LineString',
            coordinates: routes.safest_route.path.map(coord => [coord[1], coord[0]])
          }
        }
      });

      map.current.addLayer({
        id: 'safest-route',
        type: 'line',
        source: 'safest-route',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#4ECDC4',
          'line-width': 4
        }
      });
    }

    // Add crime density heatmap from backend data
    if (routes && routes.crimeData && routes.crimeData.heatmap_data && routes.crimeData.heatmap_data.length > 0) {
      const crimeFeatures = routes.crimeData.heatmap_data.map(point => ({
        type: 'Feature',
        properties: {
          density: point.density,
          intensity: point.intensity
        },
        geometry: {
          type: 'Point',
          coordinates: [point.lng, point.lat]
        }
      }));

      map.current.addSource('crime-heatmap', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: crimeFeatures
        }
      });

      map.current.addLayer({
        id: 'crime-heatmap',
        type: 'heatmap',
        source: 'crime-heatmap',
        paint: {
          'heatmap-weight': ['get', 'intensity'],
          'heatmap-intensity': 1,
          'heatmap-color': [
            'interpolate',
            ['linear'],
            ['heatmap-density'],
            0, 'rgba(33,102,172,0)',
            0.2, 'rgb(103,169,207)',
            0.4, 'rgb(209,229,240)',
            0.6, 'rgb(253,219,199)',
            0.8, 'rgb(239,138,98)',
            1, 'rgb(178,24,43)'
          ],
          'heatmap-radius': 20,
          'heatmap-opacity': 0.6
        }
      });
    }


    // Add critical crime zone markers from backend data
    if (routes && routes.crimeZones && routes.crimeZones.length > 0) {
      routes.crimeZones.forEach(crime => {
        const el = document.createElement('div');
        el.className = 'critical-crime-marker';
        el.style.width = '30px';
        el.style.height = '30px';
        el.style.borderRadius = '50%';
        el.style.backgroundColor = '#DC3545';
        el.style.border = '3px solid #fff';
        el.style.boxShadow = '0 0 10px rgba(220,53,69,0.5)';
        el.style.animation = 'pulse 2s infinite';

        new mapboxgl.Marker(el)
          .setLngLat([crime.lng, crime.lat])
          .setPopup(
            new mapboxgl.Popup({ offset: 25 })
              .setHTML(`
                <div style="padding: 8px;">
                  <strong style="color: #DC3545;">⚠️ CRITICAL ALERT</strong>
                  <p><strong>Crime:</strong> ${crime.crime_type || 'High Risk Area'}</p>
                  <p><strong>Severity:</strong> ${crime.severity || 'High'}</p>
                  <p style="color: #DC3545;"><strong>AVOID THIS AREA</strong></p>
                </div>
              `)
          )
          .addTo(map.current);
      });
    }

    // Safety segments will be added after animation completes
  }, [routes]);

  // Helper function for safety-based colors
  const getSafetyColor = (safetyScore) => {
    if (safetyScore >= 80) return '#28A745';  // Green - Very Safe
    if (safetyScore >= 60) return '#FFC107';  // Yellow - Moderate
    if (safetyScore >= 40) return '#FF9800';  // Orange - Caution
    if (safetyScore >= 20) return '#FF5722';  // Red-Orange - High Risk
    return '#DC3545';  // Red - Very High Risk
  };

  // Add safety-colored segments to the map
  const addSafetySegments = (routesData) => {
    if (!map.current || !routesData || !routesData.segments || routesData.segments.length === 0) return;

    routesData.segments.forEach((segment, index) => {
        const sourceId = `segment-${index}`;
        const layerId = `segment-layer-${index}`;
        
        // Color based on safety score
        const color = getSafetyColor(segment.safety_score);
        
        map.current.addSource(sourceId, {
          type: 'geojson',
          data: {
            type: 'Feature',
          properties: {
            safety_score: segment.safety_score,
            crime_density: segment.crime_density,
            distance: segment.distance
          },
            geometry: {
              type: 'LineString',
              coordinates: [
                [segment.start_lng, segment.start_lat],
                [segment.end_lng, segment.end_lat]
              ]
            }
          }
        });

        map.current.addLayer({
          id: layerId,
          type: 'line',
          source: sourceId,
          paint: {
            'line-color': color,
          'line-width': 4,
          'line-opacity': 0.7
        }
      });
    });
  };

  // Animate route drawing from start to finish
  const animateRouteDrawing = (coordinates, routesData) => {
    if (!map.current || !coordinates || coordinates.length < 2) return;

    let currentIndex = 0;
    const animationSpeed = 100; // milliseconds between points
    const totalDuration = coordinates.length * animationSpeed;

    const animate = () => {
      if (currentIndex < coordinates.length) {
        // Update both the main route and trail with current coordinates
        const currentCoordinates = coordinates.slice(0, currentIndex + 1);
        
        // Update the main route
        map.current.getSource('route').setData({
          type: 'Feature',
          properties: {
            safetyScore: routes.safetyScore || 0,
            distance: routes.distance || '',
            duration: routes.duration || ''
          },
          geometry: {
            type: 'LineString',
            coordinates: currentCoordinates
          }
        });
        
        // Update the trail (slightly thicker for highlight effect)
        map.current.getSource('route-trail').setData({
          type: 'Feature',
          properties: {},
          geometry: {
            type: 'LineString',
            coordinates: currentCoordinates
          }
        });

        // Add a pulsing effect to the current point
        if (currentIndex < coordinates.length - 1) {
          const currentPoint = coordinates[currentIndex];
          const nextPoint = coordinates[currentIndex + 1];
          
          // Create a temporary pulsing marker
          const el = document.createElement('div');
          el.className = 'route-animation-marker';
          el.style.width = '12px';
          el.style.height = '12px';
          el.style.borderRadius = '50%';
          el.style.backgroundColor = '#4ECDC4';
          el.style.border = '2px solid #fff';
          el.style.boxShadow = '0 0 15px rgba(78, 205, 196, 0.8)';
          el.style.animation = 'routePulse 0.5s infinite';

          // Remove previous marker
          const existingMarker = document.querySelector('.route-animation-marker');
          if (existingMarker) {
            existingMarker.remove();
          }

          // Add new marker
          new mapboxgl.Marker(el)
            .setLngLat(currentPoint)
            .addTo(map.current);
        }

        currentIndex++;
        setTimeout(animate, animationSpeed);
      } else {
        // Animation complete - remove the pulsing marker
        const marker = document.querySelector('.route-animation-marker');
        if (marker) {
          marker.remove();
        }
        
        // Add safety-colored segments now
        addSafetySegments(routesData);
        
        // Remove the trail after showing segments
        setTimeout(() => {
          if (map.current.getSource('route-trail')) {
            map.current.getSource('route-trail').setData({
              type: 'Feature',
              properties: {},
              geometry: {
                type: 'LineString',
                coordinates: []
              }
            });
          }
        }, 1000);
      }
    };

    // Start the animation
    animate();
  };

  return (
    <div className="map-container">
      <div ref={mapContainer} className="map" />
      {routes && (
        <div className="map-legend">
          <div className="legend-section">
            <h4>Route Safety</h4>
            <div className="legend-item">
              <div className="legend-color" style={{backgroundColor: '#28A745'}}></div>
              <span>Very Safe (80+)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{backgroundColor: '#FFC107'}}></div>
              <span>Moderate (60-79)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{backgroundColor: '#FF9800'}}></div>
              <span>Caution (40-59)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{backgroundColor: '#FF5722'}}></div>
              <span>High Risk (20-39)</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{backgroundColor: '#DC3545'}}></div>
              <span>Very High Risk (&lt;20)</span>
            </div>
          </div>
          <div className="legend-section">
            <h4>Crime Alerts</h4>
            <div className="legend-item">
              <div className="legend-color critical-marker"></div>
              <span>24h Critical Crime</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{backgroundColor: '#FF0000'}}></div>
              <span>High Risk Crime</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{backgroundColor: '#FFD700'}}></div>
              <span>Medium Risk Crime</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Map;
