# SAFEPATH API Requirements & Frontend Development Guide

## **Recommended API Endpoint**

### **San Francisco Police Department API** ⭐ **BEST CHOICE**
```
https://data.sfgov.org/api/v3/views/wg3w-h783/query.json
```

**Why this is perfect for your project:**
- ✅ **Free and public** - no API key required
- ✅ **Updates every 24 hours** - exactly what you need
- ✅ **Comprehensive data** - all crime types with locations
- ✅ **Flexible querying** - you can filter by date, location, crime type
- ✅ **JSON format** - easy to parse and integrate
- ✅ **Historical data** - goes back to 2018
- ✅ **Geographic coverage** - covers San Francisco area

**Sample Query for Last 7 Days:**
```javascript
const query = `SELECT * WHERE \`incident_date\` >= '2024-01-01' AND \`incident_date\` < '2024-01-08'`;
const url = `https://data.sfgov.org/api/v3/views/wg3w-h783/query.json?query=${encodeURIComponent(query)}`;
```

## **Complete API Stack for SAFEPATH**

### **1. Crime Data APIs** (Primary Data Sources)

#### **San Francisco Police Department** ⭐ **PRIMARY**
- **Endpoint**: `https://data.sfgov.org/api/v3/views/wg3w-h783/query.json`
- **Update Frequency**: Every 24 hours
- **Coverage**: San Francisco area
- **Cost**: Free
- **Setup**: No API key required

#### **Berkeley PD Open Data** ⭐ **SECONDARY**
- **Endpoint**: `https://data.cityofberkeley.info/api/views/k2nh-s5h5/rows.json`
- **Update Frequency**: Daily
- **Coverage**: Berkeley, CA
- **Cost**: Free
- **Setup**: No API key required

#### **CrimeoMeter API** (Optional - Paid)
- **Endpoint**: `https://api.crimeometer.com/v1/incidents/raw-data`
- **Update Frequency**: 15 minutes
- **Coverage**: 700+ U.S. cities
- **Cost**: $50-200/month
- **Setup**: Requires API key

### **2. Mapping & Geocoding APIs**

#### **Mapbox API** ⭐ **RECOMMENDED**
- **Purpose**: Interactive maps, routing, geocoding
- **Cost**: Free tier (50,000 requests/month)
- **Setup**: Requires API key
- **Documentation**: [docs.mapbox.com](https://docs.mapbox.com)

#### **Google Maps API** (Alternative)
- **Purpose**: Maps, geocoding, routing
- **Cost**: $200/month free credit
- **Setup**: Requires API key
- **Documentation**: [developers.google.com/maps](https://developers.google.com/maps)

#### **OpenStreetMap Nominatim** (Free Geocoding)
- **Purpose**: Address to coordinates conversion
- **Cost**: Free
- **Rate Limit**: 1 request/second
- **Setup**: No API key required

### **3. Routing APIs**

#### **Mapbox Directions API** ⭐ **RECOMMENDED**
- **Purpose**: Calculate routes between points
- **Cost**: Free tier (100,000 requests/month)
- **Features**: Walking, driving, cycling routes
- **Setup**: Same API key as Mapbox

#### **Google Directions API** (Alternative)
- **Purpose**: Route calculation
- **Cost**: $5 per 1,000 requests
- **Features**: Multiple transportation modes
- **Setup**: Same API key as Google Maps

### **4. Weather API** (Optional Enhancement)

#### **OpenWeatherMap API**
- **Purpose**: Weather conditions for route planning
- **Cost**: Free tier (1,000 calls/day)
- **Setup**: Requires API key
- **Use Case**: "Avoid walking in heavy rain"

## **Frontend Development Stack**

### **Core Technologies**

#### **React.js** ⭐ **RECOMMENDED**
- **Purpose**: User interface framework
- **Why**: Component-based, great for maps
- **Learning Curve**: Moderate
- **Ecosystem**: Huge community, lots of libraries

#### **Mapbox GL JS** ⭐ **RECOMMENDED**
- **Purpose**: Interactive maps
- **Why**: Better performance than Leaflet, great for crime visualization
- **Features**: Heatmaps, clustering, custom styling
- **Cost**: Free tier available

#### **Alternative: Leaflet.js**
- **Purpose**: Lightweight mapping
- **Why**: Simpler, smaller bundle size
- **Features**: Good for basic maps
- **Cost**: Completely free

### **UI Framework**

#### **Tailwind CSS** ⭐ **RECOMMENDED**
- **Purpose**: Styling and responsive design
- **Why**: Rapid development, mobile-first
- **Learning Curve**: Easy
- **Features**: Utility classes, responsive design

#### **Alternative: Material-UI**
- **Purpose**: Pre-built components
- **Why**: Google Material Design
- **Learning Curve**: Moderate
- **Features**: Consistent design system

### **State Management**

#### **React Context + useReducer** ⭐ **RECOMMENDED**
- **Purpose**: App state management
- **Why**: Built into React, no extra dependencies
- **Use Case**: Store user location, route data, crime data

#### **Alternative: Redux Toolkit**
- **Purpose**: Advanced state management
- **Why**: Better for complex apps
- **Learning Curve**: Steeper
- **Use Case**: Large-scale applications

### **Data Visualization**

#### **D3.js** ⭐ **RECOMMENDED**
- **Purpose**: Crime statistics charts
- **Why**: Most powerful visualization library
- **Learning Curve**: Steep
- **Features**: Custom charts, animations

#### **Chart.js** (Alternative)
- **Purpose**: Simple charts and graphs
- **Why**: Easier to learn
- **Learning Curve**: Easy
- **Features**: Pre-built chart types

## **Frontend Architecture**

### **Component Structure**
```
src/
├── components/
│   ├── Map.jsx              # Main map component
│   ├── Sidebar.jsx          # Route comparison
│   ├── RouteCard.jsx        # Individual route display
│   ├── CrimeMarker.jsx      # Crime popup details
│   ├── SaveLocationModal.jsx # Save location dialog
│   └── QuickAccessButtons.jsx # [Home] [Work] buttons
├── utils/
│   ├── api.js               # Backend API calls
│   ├── mapUtils.js          # Map drawing functions
│   ├── letta.js             # Letta integration
│   └── formatters.js        # Data formatting
├── hooks/
│   ├── useMap.js            # Map state management
│   ├── useCrimeData.js      # Crime data fetching
│   └── useRouting.js        # Route calculations
└── styles/
    └── App.css              # Global styles
```

### **Key Frontend Features**

#### **1. Interactive Map**
- **Mapbox GL JS** for rendering
- **Crime heatmap** overlay
- **Route visualization** (fastest vs safest)
- **Click to set start/end points**
- **Crime marker clustering**

#### **2. Route Comparison Sidebar**
- **Two route cards**: Fastest vs Safest
- **Time estimates**: Minutes for each route
- **Distance**: Miles/kilometers
- **Safety scores**: 1-10 scale
- **Danger warnings**: High-crime areas

#### **3. Crime Data Visualization**
- **Heatmap**: Red = dangerous, blue = safe
- **Individual markers**: Click for details
- **Crime type filtering**: Robbery, assault, etc.
- **Time filtering**: Last 24 hours, week, month

#### **4. User Location Management**
- **Save locations**: Home, work, gym
- **Quick access buttons**: [Home] [Work] [Gym]
- **Letta integration**: Persistent storage
- **One-click routing**: Click button → route appears

## **API Integration Examples**

### **Fetching Crime Data**
```javascript
// utils/api.js
const API_BASE = 'http://localhost:8000';

export const fetchCrimes = async (bounds) => {
  const response = await fetch(
    `${API_BASE}/crimes?min_lat=${bounds.south}&max_lat=${bounds.north}&min_lng=${bounds.west}&max_lng=${bounds.east}`
  );
  return response.json();
};
```

### **Calculating Routes**
```javascript
export const calculateRoute = async (start, end) => {
  const response = await fetch(`${API_BASE}/route`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ start, end })
  });
  return response.json();
};
```

### **Map Integration**
```javascript
// components/Map.jsx
import mapboxgl from 'mapbox-gl';

const Map = () => {
  useEffect(() => {
    const map = new mapboxgl.Map({
      container: 'map',
      style: 'mapbox://styles/mapbox/dark-v10',
      center: [-122.2585, 37.8719], // Berkeley
      zoom: 13
    });
    
    // Add crime heatmap
    map.addSource('crimes', {
      type: 'geojson',
      data: crimeData
    });
    
    map.addLayer({
      id: 'crime-heatmap',
      type: 'heatmap',
      source: 'crimes',
      paint: {
        'heatmap-weight': ['interpolate', ['linear'], ['get', 'severity'], 0, 0, 10, 1],
        'heatmap-color': [
          'interpolate', ['linear'], ['heatmap-density'],
          0, 'rgba(0,0,255,0)',
          0.1, 'rgba(0,0,255,1)',
          0.5, 'rgba(0,255,0,1)',
          0.7, 'rgba(255,255,0,1)',
          1, 'rgba(255,0,0,1)'
        ]
      }
    });
  }, []);
};
```

## **Development Workflow**

### **1. Backend Setup**
```bash
cd backend
pip install -r requirements.txt
python main.py  # Starts API server on :8000
```

### **2. Frontend Setup**
```bash
cd frontend
npm install
npm start  # Starts React app on :3000
```

### **3. Database Setup**
```bash
# Install PostgreSQL with PostGIS
createdb safepath
psql safepath -c "CREATE EXTENSION postgis;"
```

### **4. API Key Configuration**
```bash
# Create .env file
echo "MAPBOX_ACCESS_TOKEN=your_token_here" > .env
echo "DATABASE_URL=postgresql://user:pass@localhost/safepath" >> .env
```

## **Cost Breakdown**

### **Free Tier (Recommended for MVP)**
- **San Francisco Police API**: Free
- **Berkeley PD API**: Free
- **Mapbox**: 50,000 requests/month free
- **OpenStreetMap**: Free
- **Total**: $0/month

### **Production Tier**
- **CrimeoMeter API**: $50-200/month
- **Mapbox**: $0-50/month (depending on usage)
- **Google Maps**: $0-100/month
- **Total**: $50-350/month

## **Next Steps**

1. **Set up San Francisco Police API integration**
2. **Configure Mapbox for mapping**
3. **Build basic React frontend**
4. **Implement crime data visualization**
5. **Add routing functionality**
6. **Integrate Letta for user preferences**

This setup gives you a production-ready crime data aggregation system with a modern, interactive frontend!
