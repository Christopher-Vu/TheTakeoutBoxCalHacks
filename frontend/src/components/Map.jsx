import React, { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import './Map.css';

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

    // Add crime density heatmap
    if (routes.crime_density_map && routes.crime_density_map.heatmap_data) {
      map.current.addSource('crime-heatmap', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: routes.crime_density_map.heatmap_data.map(point => ({
            type: 'Feature',
            properties: {
              intensity: point.intensity,
              density: point.density
            },
            geometry: {
              type: 'Point',
              coordinates: [point.lng, point.lat]
            }
          }))
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

    // Add 24-hour crime zone markers
    if (routes.critical_crime_zones) {
      routes.critical_crime_zones.forEach(crime => {
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
                  <p><strong>Crime:</strong> ${crime.crime_type}</p>
                  <p><strong>Severity:</strong> ${crime.severity}/10</p>
                  <p><strong>Time:</strong> ${crime.hours_ago.toFixed(1)} hours ago</p>
                  <p style="color: #DC3545;"><strong>AVOID THIS AREA</strong></p>
                </div>
              `)
          )
          .addTo(map.current);
      });
    }

    // Add safety-based route visualization
    if (routes.segments) {
      routes.segments.forEach((segment, index) => {
        const sourceId = `segment-${index}`;
        const layerId = `segment-layer-${index}`;
        
        // Color based on safety score
        const color = getSafetyColor(segment.safety_score);
        
        map.current.addSource(sourceId, {
          type: 'geojson',
          data: {
            type: 'Feature',
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
            'line-width': 6,
            'line-opacity': 0.8
          }
        });
      });
    }
  }, [routes]);

  // Helper function for safety-based colors
  const getSafetyColor = (safetyScore) => {
    if (safetyScore >= 80) return '#28A745';  // Green - Very Safe
    if (safetyScore >= 60) return '#FFC107';  // Yellow - Moderate
    if (safetyScore >= 40) return '#FF9800';  // Orange - Caution
    if (safetyScore >= 20) return '#FF5722';  // Red-Orange - High Risk
    return '#DC3545';  // Red - Very High Risk
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
