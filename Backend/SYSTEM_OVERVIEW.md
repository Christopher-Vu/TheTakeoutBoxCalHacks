# SAFEPATH Safety Analysis System

## Overview
Complete safety analysis system that analyzes crime density, calculates safety scores, optimizes routes for safety vs distance, and provides real-time alerts for new crime data.

## Core Components

### 1. Safety Analyzer (`safety_analyzer.py`)
- **Point Safety Analysis**: Analyzes safety for specific coordinates
- **Route Safety Analysis**: Analyzes safety along route points
- **Area Safety Analysis**: Analyzes safety for rectangular areas
- **Safety Heatmap**: Generates heatmap data for visualization
- **High-Risk Areas**: Identifies areas below safety threshold

**Key Features:**
- Crime density calculation (crimes per km²)
- Recent crime analysis (last 30 days)
- High severity crime detection (severity ≥ 7)
- Confidence level calculation
- Safety percentage scoring (0-100, 100 = safest)

### 2. Safe Router (`safe_router.py`)
- **Safest Route**: Prioritizes safety over distance
- **Fastest Route**: Prioritizes distance over safety
- **Balanced Route**: Optimizes both safety and distance
- **Route Comparison**: Compares different route options

**Key Features:**
- Distance vs safety optimization
- Route scoring algorithm
- Waypoint generation and analysis
- Detour calculation for avoiding high-crime areas

### 3. Real-Time Alerts (`real_time_alerts.py`)
- **High Crime Area Alerts**: 3+ crimes in same area
- **Severity Increase Alerts**: High severity crimes (≥7)
- **Safety Decline Alerts**: Areas with safety < 30%
- **Route Blockage Alerts**: Crimes that may block routes

**Key Features:**
- Alert severity levels (Low, Medium, High, Critical)
- Alert expiration times
- Route safety checking
- Safety recommendations

### 4. Data Management
- **Database**: SQLite with 92,256+ crime records
- **Incremental Sync**: 24-hour cycle for new data
- **Data Sources**: San Francisco Police Department API
- **Historical Analysis**: Past year of crime data

## API Endpoints

### Safety Analysis
- `GET /safety/point` - Point safety analysis
- `GET /safety/route` - Route safety analysis
- `GET /safety/heatmap` - Safety heatmap data
- `GET /safety/high-risk-areas` - High-risk areas

### Safe Routing
- `POST /route/safe` - Get safe route
- `POST /route/compare` - Compare route options

### Real-Time Alerts
- `GET /alerts/check` - Check for new alerts
- `GET /alerts/area` - Get area alerts
- `POST /alerts/route-check` - Check route for alerts

## Data Flow

1. **Historical Analysis**: Uses past year of crime data for baseline safety scores
2. **Real-Time Updates**: 24-hour incremental sync adds new crime data
3. **Safety Calculation**: Combines crime density, severity, and recency
4. **Route Optimization**: Balances safety vs distance for optimal paths
5. **Alert Generation**: Monitors new data for safety alerts

## Safety Scoring Algorithm

```
Safety Percentage = 100 - (Density Penalty + Recent Penalty + Severity Penalty + Severity-Weighted Penalty)

Where:
- Density Penalty = min(50, density_per_km² × 2.0)
- Recent Penalty = min(30, recent_crimes × 3.0)
- Severity Penalty = min(40, high_severity_crimes × 8.0)
- Severity-Weighted Penalty = min(20, severity_weighted_density × 1.5)
```

## Route Optimization

```
Route Score = (Safety Score × Safety Weight) + (Distance Score × Distance Weight)

Where:
- Safety Weight = 0.6 (default)
- Distance Weight = 0.4 (default)
- Safety Score = average_safety / 100.0
- Distance Score = 1.0 - min(1.0, total_distance / 30.0)
```

## Alert Types

1. **HIGH_CRIME_AREA**: 3+ crimes in same location
2. **RECENT_INCIDENT**: New crime in last 24 hours
3. **SEVERITY_INCREASE**: High severity crime (≥7)
4. **ROUTE_BLOCKED**: Crime that may block routes
5. **SAFETY_DECLINE**: Area safety < 30%

## Usage Example

```python
# Point Safety Analysis
GET /safety/point?lat=37.7749&lng=-122.4194
Response: {
    "safety_percentage": 54.2,
    "crime_density": 8.91,
    "recent_crimes": 0,
    "high_severity_crimes": 1,
    "confidence_level": 0.36,
    "risk_level": "High Risk"
}

# Safe Route
POST /route/safe?start_lat=37.7749&start_lng=-122.4194&end_lat=37.7849&end_lng=-122.4094&route_type=balanced
Response: {
    "route_type": "balanced",
    "total_distance_km": 1.42,
    "average_safety_percentage": 40.9,
    "route_score": 0.838,
    "points": [...]
}
```

## Database Schema

- **CrimeReport**: Main crime data table
- **DataSource**: Data source configuration
- **DataSyncLog**: Sync operation logs

## Dependencies

- FastAPI: Web framework
- SQLAlchemy: Database ORM
- Pandas/NumPy: Data processing
- AioHTTP: Async HTTP client
- Schedule: Task scheduling

## Performance

- **Database**: 92,256+ crime records
- **Analysis Speed**: ~1-2 seconds per point
- **Route Calculation**: ~2-5 seconds per route
- **Alert Processing**: Real-time monitoring
- **Sync Frequency**: Every 24 hours
