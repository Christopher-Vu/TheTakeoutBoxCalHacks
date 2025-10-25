import React, { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const Map = ({ origin, destination, routes }) => {
  const mapContainer = useRef(null);
  const map = useRef(null);

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
    });
  }, []);

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

    // Add fastest route
    if (routes.fastest_route && routes.fastest_route.path) {
      map.current.addSource('fastest-route', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: {
            type: 'LineString',
            coordinates: routes.fastest_route.path.map(coord => [coord[1], coord[0]])
          }
        }
      });

      map.current.addLayer({
        id: 'fastest-route',
        type: 'line',
        source: 'fastest-route',
        layout: {
          'line-join': 'round',
          'line-cap': 'round'
        },
        paint: {
          'line-color': '#FF6B6B',
          'line-width': 4
        }
      });
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

    // Add crime points
    if (routes.crime_points && routes.crime_points.length > 0) {
      const crimeFeatures = routes.crime_points.map(crime => ({
        type: 'Feature',
        properties: {
          id: crime.id,
          type: crime.type,
          severity: crime.severity,
          description: crime.description,
          time_ago: crime.time_ago
        },
        geometry: {
          type: 'Point',
          coordinates: [crime.lng, crime.lat]
        }
      }));

      map.current.addSource('crime-points', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: crimeFeatures
        }
      });

      map.current.addLayer({
        id: 'crime-points',
        type: 'circle',
        source: 'crime-points',
        paint: {
          'circle-color': [
            'case',
            ['>=', ['get', 'severity'], 8], '#FF0000',
            ['>=', ['get', 'severity'], 6], '#FF8C00',
            ['>=', ['get', 'severity'], 4], '#FFD700',
            '#90EE90'
          ],
          'circle-radius': [
            'case',
            ['>=', ['get', 'severity'], 8], 8,
            ['>=', ['get', 'severity'], 6], 6,
            ['>=', ['get', 'severity'], 4], 4,
            3
          ]
        }
      });

      // Add click handler for crime points
      map.current.on('click', 'crime-points', (e) => {
        const feature = e.features[0];
        new mapboxgl.Popup()
          .setLngLat(e.lngLat)
          .setHTML(`
            <div>
              <strong>${feature.properties.type}</strong><br/>
              Severity: ${feature.properties.severity}/10<br/>
              ${feature.properties.description}<br/>
              <small>${feature.properties.time_ago}</small>
            </div>
          `)
          .addTo(map.current);
      });

      map.current.on('mouseenter', 'crime-points', () => {
        map.current.getCanvas().style.cursor = 'pointer';
      });

      map.current.on('mouseleave', 'crime-points', () => {
        map.current.getCanvas().style.cursor = '';
      });
    }
  }, [routes]);

  return (
    <div className="map-container">
      <div ref={mapContainer} className="map" />
      {routes && (
        <div className="map-legend">
          <div className="legend-item">
            <div className="legend-color" style={{backgroundColor: '#FF6B6B'}}></div>
            <span>Fastest Route</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{backgroundColor: '#4ECDC4'}}></div>
            <span>Safest Route</span>
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
      )}
    </div>
  );
};

export default Map;
