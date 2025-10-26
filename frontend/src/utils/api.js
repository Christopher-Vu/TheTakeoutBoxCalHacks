// Backend API calls for SAFEPATH
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Crime Data API
export const crimeAPI = {
  // Get crimes within geographic bounds
  getCrimesInBounds: async (minLat, maxLat, minLng, maxLng, options = {}) => {
    const params = {
      min_lat: minLat,
      max_lat: maxLat,
      min_lng: minLng,
      max_lng: maxLng,
      ...options
    };
    
    try {
      const response = await api.get('/crimes', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching crimes:', error);
      throw error;
    }
  },

  // Get crimes near a specific point
  getCrimesNear: async (lat, lng, radius = 100, daysBack = 7) => {
    try {
      const response = await api.get('/crimes/near', {
        params: { lat, lng, radius, days_back: daysBack }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching crimes near point:', error);
      throw error;
    }
  },

  // Get crime statistics for an area
  getCrimeStats: async (minLat, maxLat, minLng, maxLng, daysBack = 30) => {
    try {
      const response = await api.get('/stats', {
        params: { min_lat: minLat, max_lat: maxLat, min_lng: minLng, max_lng: maxLng, days_back: daysBack }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching crime stats:', error);
      throw error;
    }
  },

  // Get crime heatmap data
  getCrimeHeatmap: async (minLat, maxLat, minLng, maxLng, gridSize = 50) => {
    try {
      const response = await api.get('/data/heatmap', {
        params: { min_lat: minLat, max_lat: maxLat, min_lng: minLng, max_lng: maxLng, grid_size: gridSize }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching crime heatmap:', error);
      throw error;
    }
  }
};

// Safety Analysis API
export const safetyAPI = {
  // Get safety analysis for a specific point
  getPointSafety: async (lat, lng) => {
    try {
      const response = await api.get('/safety/point', {
        params: { lat, lng }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting point safety:', error);
      throw error;
    }
  },

  // Get safety analysis for a route
  getRouteSafety: async (routePoints) => {
    try {
      const response = await api.get('/safety/route', {
        params: { route_points: JSON.stringify(routePoints) }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting route safety:', error);
      throw error;
    }
  },

  // Get safety heatmap data
  getSafetyHeatmap: async (minLat, maxLat, minLng, maxLng) => {
    try {
      const response = await api.get('/safety/heatmap', {
        params: { min_lat: minLat, max_lat: maxLat, min_lng: minLng, max_lng: maxLng }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting safety heatmap:', error);
      throw error;
    }
  },

  // Get high-risk areas
  getHighRiskAreas: async (minLat, maxLat, minLng, maxLng, safetyThreshold = 30) => {
    try {
      const response = await api.get('/safety/high-risk-areas', {
        params: { 
          min_lat: minLat, 
          max_lat: maxLat, 
          min_lng: minLng, 
          max_lng: maxLng, 
          safety_threshold: safetyThreshold 
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting high-risk areas:', error);
      throw error;
    }
  }
};

// Safe Routing API
export const routingAPI = {
  // Get safe route between two points
  getSafeRoute: async (startLat, startLng, endLat, endLng, routeType = 'balanced') => {
    try {
      const response = await api.post('/route/safe', null, {
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
      console.error('Error getting safe route:', error);
      throw error;
    }
  },

  // Compare different route options
  compareRoutes: async (startLat, startLng, endLat, endLng) => {
    try {
      const response = await api.post('/route/compare', null, {
        params: { start_lat: startLat, start_lng: startLng, end_lat: endLat, end_lng: endLng }
      });
      return response.data;
    } catch (error) {
      console.error('Error comparing routes:', error);
      throw error;
    }
  },

  // Get crime-aware route using Dijkstra algorithm
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

  // Compare all crime-aware route types (safest, fastest, balanced)
  compareCrimeAwareRoutes: async (startLat, startLng, endLat, endLng) => {
    try {
      const response = await api.post('/route/crime-aware/compare', null, {
        params: { start_lat: startLat, start_lng: startLng, end_lat: endLat, end_lng: endLng }
      });
      return response.data;
    } catch (error) {
      console.error('Error comparing crime-aware routes:', error);
      throw error;
    }
  }
};

// Real-time Alerts API
export const alertsAPI = {
  // Check for new alerts
  checkAlerts: async () => {
    try {
      const response = await api.get('/alerts/check');
      return response.data;
    } catch (error) {
      console.error('Error checking alerts:', error);
      throw error;
    }
  },

  // Get alerts for a specific area
  getAreaAlerts: async (lat, lng, radiusKm = 1.0) => {
    try {
      const response = await api.get('/alerts/area', {
        params: { lat, lng, radius_km: radiusKm }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting area alerts:', error);
      throw error;
    }
  },

  // Check if a route is affected by alerts
  checkRouteAlerts: async (routePoints) => {
    try {
      const response = await api.post('/alerts/route-check', null, {
        params: { route_points: JSON.stringify(routePoints) }
      });
      return response.data;
    } catch (error) {
      console.error('Error checking route alerts:', error);
      throw error;
    }
  }
};

// Data Management API
export const dataAPI = {
  // Get data statistics
  getDataStatistics: async () => {
    try {
      const response = await api.get('/data/statistics');
      return response.data;
    } catch (error) {
      console.error('Error getting data statistics:', error);
      throw error;
    }
  },

  // Sync data sources
  syncData: async (limit = null) => {
    try {
      const response = await api.post('/data/sync', null, {
        params: limit ? { limit } : {}
      });
      return response.data;
    } catch (error) {
      console.error('Error syncing data:', error);
      throw error;
    }
  },

  // Get crime trends
  getCrimeTrends: async (days = 30) => {
    try {
      const response = await api.get('/data/trends', {
        params: { days }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting crime trends:', error);
      throw error;
    }
  }
};

// Utility functions
export const apiUtils = {
  // Convert coordinates to bounds
  coordsToBounds: (lat, lng, radiusKm = 1) => {
    const latDelta = radiusKm / 111; // Approximate km per degree latitude
    const lngDelta = radiusKm / (111 * Math.cos(lat * Math.PI / 180));
    
    return {
      minLat: lat - latDelta,
      maxLat: lat + latDelta,
      minLng: lng - lngDelta,
      maxLng: lng + lngDelta
    };
  },

  // Format route points for API
  formatRoutePoints: (points) => {
    return points.map(point => ({
      lat: point.lat || point[0],
      lng: point.lng || point[1]
    }));
  },

  // Get safety score color
  getSafetyScoreColor: (score) => {
    if (score >= 85) return '#00AA55'; // Green
    if (score >= 70) return '#FFAA00'; // Orange
    if (score >= 50) return '#FF6600'; // Red-Orange
    return '#DC3545'; // Red
  },

  // Get safety score label
  getSafetyScoreLabel: (score) => {
    if (score >= 85) return 'Very Safe';
    if (score >= 70) return 'Moderately Safe';
    if (score >= 50) return 'Use Caution';
    return 'High Risk';
  },

  // Get alert severity color
  getAlertSeverityColor: (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical': return '#DC3545';
      case 'high': return '#FF6600';
      case 'medium': return '#FFAA00';
      case 'low': return '#28A745';
      default: return '#6C757D';
    }
  }
};

export default api;