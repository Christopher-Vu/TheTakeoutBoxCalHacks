<!-- 9d88838b-5e61-4c79-9508-fe208469f36a fab2ec7e-d3a6-4711-af4f-f9f65a27cab6 -->
# Crime-Aware Route Visualization Integration

## Overview

Integrate the enhanced crime-aware routing algorithm with the existing Mapbox GL frontend to display routes with crime density heatmaps, safety scores, and 24-hour crime zones.

## Current State Analysis

**Existing Resources:**

- Mapbox GL JS already installed (`mapbox-gl@2.15.0`)
- Map component exists at `frontend/src/components/Map.jsx`
- API utilities exist at `frontend/src/utils/api.js`
- Mapbox token configured: `process.env.REACT_APP_MAPBOX_TOKEN`
- RoutePlanning component at `frontend/src/components/RoutePlanning.jsx`

**What's Missing:**

- Integration with `/route/crime-aware` API endpoint
- Crime density heatmap visualization
- 24-hour crime zone markers
- Safety score visualization per segment
- Route comparison UI for safest/fastest/balanced

## Implementation Steps

### 1. Add Crime-Aware Routing API to Frontend

**File:** `frontend/src/utils/api.js`

Add new API function to the existing `routingAPI` object:

```javascript
// Safe Routing API
export const routingAPI = {
  // ... existing methods ...
  
  // NEW: Crime-aware routing with full crime density data
  getCrimeAwareRoute: async (startLat, startLng, endLat, endLng, routeType = 'balanced') => {
    try {
      const response = await api.post('/route/crime-aware', null, {
        params: {
          start_lat: startLat,
          start_lng: startLng,
          end_lat: endLat,
          end_lng: endLng,
          route_type: routeType
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting crime-aware route:', error);
      throw error;
    }
  },
  
  // NEW: Compare all crime-aware route types
  compareCrimeAwareRoutes: async (startLat, startLng, endLat, endLng) => {
    try {
      const response = await api.post('/route/crime-aware/compare', null, {
        params: {
          start_lat: startLat,
          start_lng: startLng,
          end_lat: endLat,
          end_lng: endLng
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error comparing crime-aware routes:', error);
      throw error;
    }
  }
};
```

### 2. Enhance Map Component for Crime Visualization

**File:** `frontend/src/components/Map.jsx`

**Current capabilities:**

- Displays origin/destination markers
- Shows fastest/safest routes
- Shows crime points

**Enhancements needed:**

#### A. Add Crime Density Heatmap Layer

```javascript
// Add after line 68 (crime-points source removal)
if (map.current.getLayer('crime-heatmap')) {
  map.current.removeLayer('crime-heatmap');
  map.current.removeSource('crime-heatmap');
}

// Add heatmap visualization
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
```

#### B. Add 24-Hour Crime Zone Markers

```javascript
// Add critical crime zone markers (24-hour crimes)
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
```

#### C. Visualize Route with Safety Gradient

```javascript
// Enhanced route visualization with safety-based coloring
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

// Helper function for safety-based colors
function getSafetyColor(safetyScore) {
  if (safetyScore >= 80) return '#28A745';  // Green - Very Safe
  if (safetyScore >= 60) return '#FFC107';  // Yellow - Moderate
  if (safetyScore >= 40) return '#FF9800';  // Orange - Caution
  if (safetyScore >= 20) return '#FF5722';  // Red-Orange - High Risk
  return '#DC3545';  // Red - Very High Risk
}
```

### 3. Update RoutePlanning Component

**File:** `frontend/src/components/RoutePlanning.jsx`

**Changes needed:**

#### A. Update handleFindRoutes function (around line 48)

```javascript
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
      'balanced'  // or let user choose: safest, fastest, balanced
    );
    
    // Transform API response to match Map component expectations
    const transformedRoutes = {
      path_coordinates: crimeAwareRoute.path_coordinates,
      segments: crimeAwareRoute.segments,
      crime_density_map: crimeAwareRoute.crime_density_map,
      critical_crime_zones: crimeAwareRoute.critical_crime_zones,
      route_safety_breakdown: crimeAwareRoute.route_safety_breakdown,
      total_distance: crimeAwareRoute.total_distance,
      total_safety_score: crimeAwareRoute.total_safety_score
    };
    
    setRoutes([transformedRoutes]);
    setSelectedRoute(transformedRoutes);
    
  } catch (error) {
    console.error('Error fetching crime-aware route:', error);
    // Fallback to mock data if API fails
    const mockRoutes = generateMockRoutes(selectedOrigin, selectedDestination);
    setRoutes(mockRoutes);
  } finally {
    setIsSearching(false);
  }
};
```

#### B. Add Route Type Selector

```javascript
// Add state for route type
const [routeType, setRouteType] = useState('balanced');

// Add UI component (insert before travel mode selector)
<div className="route-type-selector">
  <label>Route Priority:</label>
  <div className="route-type-buttons">
    <button 
      className={routeType === 'safest' ? 'active' : ''}
      onClick={() => setRouteType('safest')}
    >
      🛡️ Safest
    </button>
    <button 
      className={routeType === 'balanced' ? 'active' : ''}
      onClick={() => setRouteType('balanced')}
    >
      ⚖️ Balanced
    </button>
    <button 
      className={routeType === 'fastest' ? 'active' : ''}
      onClick={() => setRouteType('fastest')}
    >
      ⚡ Fastest
    </button>
  </div>
</div>
```

### 4. Add Safety Dashboard Component

**Create new file:** `frontend/src/components/SafetyDashboard.jsx`

Display comprehensive safety metrics:

```javascript
import React from 'react';
import './SafetyDashboard.css';

const SafetyDashboard = ({ safetyBreakdown }) => {
  if (!safetyBreakdown) return null;

  return (
    <div className="safety-dashboard">
      <h3>Route Safety Analysis</h3>
      
      <div className="safety-grade">
        <div className={`grade-badge grade-${safetyBreakdown.route_safety_summary.safety_grade}`}>
          {safetyBreakdown.route_safety_summary.safety_grade}
        </div>
        <span>Safety Grade</span>
      </div>

      <div className="safety-metrics">
        <div className="metric">
          <span className="metric-value">{safetyBreakdown['24h_crimes_avoided']}</span>
          <span className="metric-label">24h Crimes Avoided</span>
        </div>
        <div className="metric">
          <span className="metric-value">{safetyBreakdown.high_severity_crimes_avoided}</span>
          <span className="metric-label">High-Risk Areas Avoided</span>
        </div>
        <div className="metric">
          <span className="metric-value">{safetyBreakdown.average_crime_density.toFixed(1)}</span>
          <span className="metric-label">Avg Crime Density</span>
        </div>
      </div>

      <div className="most-dangerous-segment">
        <h4>⚠️ Most Cautious Segment</h4>
        <p>Safety Score: {safetyBreakdown.most_dangerous_segment.safety_score.toFixed(1)}</p>
        <p>Crime Density: {safetyBreakdown.most_dangerous_segment.crime_density}</p>
        <p>24h Crimes: {safetyBreakdown.most_dangerous_segment.critical_crimes_24h}</p>
      </div>
    </div>
  );
};

export default SafetyDashboard;
```

### 5. Add CSS Animations and Styling

**File:** `frontend/src/components/Map.css` (create if doesn't exist)

```css
/* Critical crime marker pulse animation */
@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(220, 53, 69, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(220, 53, 69, 0);
  }
}

.critical-crime-marker {
  cursor: pointer;
  transition: transform 0.2s;
}

.critical-crime-marker:hover {
  transform: scale(1.2);
}

/* Safety dashboard styling */
.safety-dashboard {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin: 20px 0;
}

.grade-badge {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: bold;
  color: white;
}

.grade-A { background: #28A745; }
.grade-B { background: #5CB85C; }
.grade-C { background: #FFC107; }
.grade-D { background: #FF9800; }
.grade-F { background: #DC3545; }
```

### 6. Environment Configuration

**Create:** `frontend/.env` (if doesn't exist)

```
REACT_APP_MAPBOX_TOKEN=pk.eyJ1IjoiYW5keXltYW9vIiwiYSI6ImNtaDYzMGhrdzA4dnAya29vbW4wcHZ6ODEifQ.NNhIooCa7yGJzYEegxEdAw
REACT_APP_API_URL=http://localhost:8000
```

### 7. Testing & Demo Script

**Create:** `docs/ROUTE_VISUALIZATION_DEMO.md`

Demo script for showcasing the feature:

1. Start backend: `docker-compose up -d`
2. Start frontend: `cd frontend && npm start`
3. Navigate to Route Planning
4. Enter test coordinates:

   - Origin: 37.7749, -122.4194 (SF Downtown)
   - Destination: 37.7849, -122.4094

5. Select route type (Safest/Balanced/Fastest)
6. View visualization:

   - Crime density heatmap
   - 24-hour crime zones (red pulsing markers)
   - Route colored by safety score
   - Safety dashboard with metrics

## Files to Modify/Create

1. `frontend/src/utils/api.js` - Add crime-aware routing API calls
2. `frontend/src/components/Map.jsx` - Enhance with crime visualization
3. `frontend/src/components/RoutePlanning.jsx` - Integrate API calls
4. `frontend/src/components/SafetyDashboard.jsx` - NEW: Safety metrics display
5. `frontend/src/components/Map.css` - NEW: Styling for crime markers
6. `frontend/src/components/SafetyDashboard.css` - NEW: Dashboard styling
7. `frontend/.env` - Mapbox token configuration
8. `docs/ROUTE_VISUALIZATION_DEMO.md` - NEW: Demo instructions

## Expected User Experience

1. User enters origin and destination
2. Selects route priority (safest/balanced/fastest)
3. Map displays:

   - **Heatmap**: Crime density overlay (blue to red gradient)
   - **Route**: Color-coded by safety (green=safe, red=dangerous)
   - **Critical Zones**: Pulsing red markers for 24h crimes
   - **Markers**: Origin (green) and destination (red)

4. Safety dashboard shows:

   - Overall safety grade (A-F)
   - 24h crimes avoided count
   - High-risk areas avoided
   - Most dangerous segment details

5. User can compare different route types side-by-side

### To-dos

- [ ] Update crime influence parameters (100m radius, 24h penalty)
- [ ] Enhance time decay calculation with hour-level precision
- [ ] Update crime penalty calculation formula
- [ ] Enhance crime data query to include hours_ago
- [ ] Add crime density map calculation method
- [ ] Update RouteSegment dataclass with 24h crime fields
- [ ] Create comprehensive CRIME_ROUTING_ALGORITHM.md documentation
- [ ] Add detailed inline documentation and docstrings
- [ ] Add visualization helper methods for frontend
- [ ] Update API response format with crime density data