# Crime-Aware Routing Demo Guide

## Overview
This guide demonstrates the crime-aware routing system that helps users find the safest routes between two points while avoiding high-crime areas, especially recent severe crimes.

## Features Demonstrated

### 1. Crime-Aware Route Calculation
- **Safest Route**: Prioritizes safety over distance
- **Balanced Route**: Balances safety and efficiency
- **Fastest Route**: Prioritizes speed while avoiding critical crime areas

### 2. Real-Time Crime Visualization
- **Crime Density Heatmap**: Shows crime concentration across the area
- **24-Hour Critical Crime Zones**: Highlights recent severe crimes with pulsing markers
- **Route Safety Visualization**: Color-coded route segments based on safety scores

### 3. Safety Analysis Dashboard
- **Safety Grade**: Overall route safety rating (A-F)
- **Crime Statistics**: Total crimes, recent crimes, severity breakdown
- **Route Metrics**: Distance, estimated time, safety score

## Demo Scenarios

### Scenario 1: Safe Route Through Low-Crime Area
**Start**: Union Square, San Francisco  
**End**: Golden Gate Park, San Francisco  
**Route Type**: Safest

**Expected Results**:
- Route avoids known high-crime areas
- Green/yellow safety visualization
- High safety grade (A or B)
- Minimal recent crime exposure

### Scenario 2: Balanced Route Through Mixed Area
**Start**: Mission District, San Francisco  
**End**: Financial District, San Francisco  
**Route Type**: Balanced

**Expected Results**:
- Route balances safety and efficiency
- Mixed safety colors (green, yellow, orange)
- Moderate safety grade (B or C)
- Some crime exposure but manageable

### Scenario 3: Critical Crime Avoidance
**Start**: Tenderloin, San Francisco  
**End**: Marina District, San Francisco  
**Route Type**: Safest

**Expected Results**:
- Route completely avoids 24-hour critical crime zones
- Heavy penalty for recent severe crimes
- May take longer route to avoid danger
- Safety grade reflects risk avoidance

## How to Test

### 1. Start the Backend
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start the Frontend
```bash
cd frontend
npm start
```

### 3. Access the Application
- Open http://localhost:3000
- Navigate to Route Planning
- Enter origin and destination coordinates
- Select route type (Safest/Balanced/Fastest)
- Click "Find Routes"

### 4. Observe the Results
- **Map Visualization**: Crime heatmap, critical zones, route colors
- **Safety Dashboard**: Detailed safety metrics and grades
- **Route Comparison**: Different route options with safety trade-offs

## Key Algorithm Features

### Crime Influence Parameters
- **Influence Radius**: 100 meters
- **Critical Hours**: 24 hours (hard penalty)
- **Time Decay**: Exponential decay for older crimes
- **Severity Weighting**: Higher penalties for more severe crimes

### Safety Scoring
- **Route Safety Score**: 0-100 (higher = safer)
- **Safety Grade**: A (90-100), B (80-89), C (70-79), D (60-69), F (<60)
- **Segment Analysis**: Individual segment safety scores

### Visualization Elements
- **Crime Heatmap**: Density-based visualization
- **Critical Zones**: 24-hour crime markers
- **Route Colors**: Green (safe) to Red (risky)
- **Safety Legend**: Color coding explanation

## Expected API Responses

### Crime-Aware Route Response
```json
{
  "route_type": "safest",
  "total_distance": 2.5,
  "estimated_time": 15,
  "safety_score": 85,
  "crime_density_map": {
    "heatmap_data": [...],
    "bounds": {...}
  },
  "critical_crime_zones": [...],
  "route_safety_breakdown": {
    "route_safety_summary": {...},
    "segment_analysis": [...],
    "crime_statistics": {...}
  },
  "segments": [...]
}
```

## Troubleshooting

### Common Issues
1. **Map not displaying**: Check Mapbox token in .env
2. **No routes returned**: Verify coordinates are valid
3. **Backend errors**: Check database connection and crime data
4. **Frontend errors**: Check browser console for API errors

### Debug Steps
1. Check backend logs for routing errors
2. Verify crime data in database
3. Test API endpoints directly
4. Check frontend network requests

## Performance Notes
- Route calculation: 1-3 seconds for typical distances
- Crime data query: Optimized with spatial indexing
- Frontend rendering: Smooth map interactions
- Real-time updates: Crime data refreshed periodically

## Next Steps
1. Test with different San Francisco locations
2. Compare route types side-by-side
3. Analyze safety metrics for decision making
4. Explore crime density patterns
5. Test edge cases (very short/long routes)
