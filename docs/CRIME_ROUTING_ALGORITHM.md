# Crime Density Routing Algorithm Documentation

## Overview

The Crime Density Routing Algorithm is a sophisticated pathfinding system that uses Dijkstra's algorithm with crime data integration to find optimal routes that balance distance and safety. The algorithm heavily penalizes routes through high-crime areas, especially recent crimes within 24 hours, to ensure users avoid dangerous areas.

## Algorithm Components

### 1. Dijkstra's Algorithm Implementation

The core routing algorithm uses Dijkstra's shortest path algorithm with weighted edges. Each edge weight is calculated as:

```
edge_weight = segment_distance + crime_penalty
```

Where:
- `segment_distance`: Physical distance between waypoints in meters
- `crime_penalty`: Calculated penalty based on nearby crimes

### 2. Crime Weighting System

#### Severity Score Mapping (1-10 Scale)

The algorithm uses the existing severity scores from the database:

| Severity | Crime Type | Weight | Description |
|----------|------------|--------|-------------|
| 10 | HOMICIDE | 1.0 | Critical - Maximum penalty |
| 9 | SEXUAL_ASSAULT | 1.0 | Critical - Maximum penalty |
| 8 | ROBBERY, WEAPON_OFFENSE | 0.9 | Very High - Near maximum penalty |
| 7 | ASSAULT | 0.8 | High - Significant penalty |
| 6 | BURGLARY | 0.7 | High - Moderate-high penalty |
| 5 | DRUG_OFFENSE | 0.5 | Medium-High - Moderate penalty |
| 4 | THEFT | 0.4 | Medium - Lower penalty |
| 3 | VANDALISM | 0.3 | Low-Medium - Minimal penalty |
| 2 | OTHER | 0.2 | Low - Very minimal penalty |

#### Time Decay Factors

Crime recency is weighted using hour-level precision:

```
time_factor = {
  10000.0  if hours_ago ≤ 24      # Extreme penalty (near-blocking)
  10.0     if hours_ago ≤ 168     # High penalty (1-7 days)
  1.0      if hours_ago ≤ 720     # Normal penalty (7-30 days)
  0.3      if hours_ago ≤ 2160    # Reduced penalty (30-90 days)
  0.1      if hours_ago > 2160    # Minimal penalty (90+ days)
}
```

#### Distance Influence (100m Radius)

Crimes within 100 meters of a route segment influence the penalty:

```
distance_factor = max(0, 1 - (crime_distance / 100m))
```

Where:
- `crime_distance`: Distance from crime to route segment in meters
- Crimes at 0m distance have full influence (factor = 1.0)
- Crimes at 100m+ distance have no influence (factor = 0.0)

### 3. Edge Weight Calculation Formula

The final edge weight combines distance and crime penalties:

```
edge_weight = segment_distance + crime_penalty

where crime_penalty = Σ(time_factor × distance_factor × severity_weight × scale_factor)
```

#### Enhanced Penalty Calculation

For 24-hour crimes, the penalty is proportional to segment distance:

```
if hours_ago ≤ 24:
    penalty = time_factor × distance_factor × severity_factor × segment_distance × 1000
else:
    penalty = time_factor × distance_factor × severity_factor × 100
```

This ensures that:
- Longer segments through recent crime areas receive exponentially higher penalties
- 24-hour crimes create near-blocking conditions
- Older crimes have minimal impact on routing decisions

### 4. Safety Score Calculation

Each route segment receives a safety score (0-100, higher = safer):

```
safety_score = max(0, 100 - total_penalty)

where total_penalty = Σ(time_factor × severity_factor × distance_factor × 20)
```

### 5. Route Optimization Strategy

The algorithm supports three route types with different weight distributions:

#### Safest Route (safety_weight=0.8, distance_weight=0.2)
- Prioritizes safety over distance
- Heavily avoids high-crime areas
- May result in longer routes

#### Fastest Route (safety_weight=0.2, distance_weight=0.8)
- Prioritizes distance over safety
- Takes more direct paths
- May pass through higher-crime areas

#### Balanced Route (safety_weight=0.5, distance_weight=0.5)
- Equal weight on safety and distance
- Optimal compromise between safety and efficiency

## Example Calculations

### Scenario: Route from Point A to Point B

**Input:**
- Start: 37.7749, -122.4194 (San Francisco)
- End: 37.7849, -122.4094
- Route type: balanced

**Crime Data in Area:**
- 1 HOMICIDE (severity=10) 2 hours ago at 50m from route
- 3 ASSAULTS (severity=7) 3 days ago at 30m from route
- 5 THEFTS (severity=4) 2 weeks ago at 80m from route

**Calculations:**

1. **HOMICIDE (2 hours ago, 50m distance):**
   - time_factor = 10000.0 (24-hour extreme penalty)
   - distance_factor = max(0, 1 - 50/100) = 0.5
   - severity_factor = 1.0
   - penalty = 10000.0 × 0.5 × 1.0 × segment_distance × 1000 = 5,000,000 × segment_distance

2. **ASSAULTS (3 days ago, 30m distance):**
   - time_factor = 10.0 (recent penalty)
   - distance_factor = max(0, 1 - 30/100) = 0.7
   - severity_factor = 0.8
   - penalty = 10.0 × 0.7 × 0.8 × 100 = 560

3. **THEFTS (2 weeks ago, 80m distance):**
   - time_factor = 1.0 (normal penalty)
   - distance_factor = max(0, 1 - 80/100) = 0.2
   - severity_factor = 0.4
   - penalty = 1.0 × 0.2 × 0.4 × 100 = 8

**Result:** The route will heavily avoid the homicide area and moderately avoid assault areas, while being less concerned about theft areas.

## Configuration Parameters

### Core Parameters

```python
# Crime influence radius (meters)
crime_influence_radius = 100

# Time decay thresholds
critical_hours = 24          # 24-hour crimes (extreme penalty)
recent_days = 7              # Recent crimes (high penalty)
medium_days = 30             # Medium recency (normal penalty)
old_days = 90                # Old crimes (reduced penalty)

# Penalty multipliers
critical_penalty_multiplier = 10000.0  # 24-hour crimes
recent_penalty_multiplier = 10.0       # 1-7 days
medium_penalty_multiplier = 1.0       # 7-30 days
old_penalty_multiplier = 0.3           # 30-90 days
ancient_penalty_multiplier = 0.1       # 90+ days
```

### Route Optimization Weights

```python
# Safest route
safety_weight = 0.8
distance_weight = 0.2

# Fastest route
safety_weight = 0.2
distance_weight = 0.8

# Balanced route
safety_weight = 0.5
distance_weight = 0.5
```

## API Response Format

The enhanced API returns comprehensive crime density data:

```json
{
  "route_type": "balanced",
  "total_distance": 2059.59,
  "total_safety_score": 25.70,
  "total_crime_penalty": 1190,
  "path_coordinates": [[37.7749, -122.4194], ...],
  "crime_density_map": {
    "heatmap_data": [...],
    "total_crimes": 150,
    "critical_crimes_24h": 3,
    "high_severity_crimes": 12
  },
  "critical_crime_zones": [
    {
      "lat": 37.7750,
      "lng": -122.4190,
      "severity": 10,
      "crime_type": "HOMICIDE",
      "hours_ago": 2.5,
      "blocked_radius": 100,
      "penalty_level": "CRITICAL"
    }
  ],
  "route_safety_breakdown": {
    "24h_crimes_avoided": 3,
    "high_severity_crimes_avoided": 12,
    "recent_crimes_encountered": 8,
    "average_crime_density": 2.5,
    "most_dangerous_segment": {
      "safety_score": 15.2,
      "crime_density": 8,
      "critical_crimes_24h": 1
    },
    "route_safety_summary": {
      "total_distance": 2059.59,
      "average_safety": 25.70,
      "safety_grade": "D"
    }
  },
  "segments": [
    {
      "start_lat": 37.7749,
      "start_lng": -122.4194,
      "end_lat": 37.7757,
      "end_lng": -122.4186,
      "distance": 115.70,
      "safety_score": 37.77,
      "crime_density": 36,
      "high_severity_crimes": 8,
      "recent_crimes": 0,
      "critical_crimes_24h": 0,
      "hours_to_nearest_crime": 48.5,
      "crime_density_score": 2.3
    }
  ]
}
```

## Safety Grade System

Routes receive safety grades based on average safety score:

- **A (85-100)**: Very Safe - Minimal crime exposure
- **B (70-84)**: Safe - Low crime exposure
- **C (50-69)**: Moderate Risk - Some crime exposure
- **D (30-49)**: High Risk - Significant crime exposure
- **F (0-29)**: Very High Risk - Heavy crime exposure

## Performance Considerations

### Database Optimization

- Crimes are filtered by bounding box and time range
- Spatial indexing on lat/lng coordinates
- Time-based filtering (90-day window)
- Severity-based filtering for high-impact crimes

### Algorithm Complexity

- **Time Complexity**: O(V log V + E) where V = waypoints, E = edges
- **Space Complexity**: O(V + E) for graph storage
- **Waypoint Generation**: 50 points per route (configurable)
- **Crime Influence**: 100m radius per segment

### Caching Strategy

- Crime data cached for route area
- Density maps cached for visualization
- Route segments cached for repeated requests

## Implementation Notes

### Error Handling

- Database connection failures fall back to basic routing
- Missing crime data uses default safety scores
- Invalid coordinates return error responses

### Edge Cases

- No crime data: Routes use distance-only optimization
- All routes blocked: Returns shortest path with warning
- Single waypoint: Returns direct route
- Invalid coordinates: Returns validation error

### Monitoring and Metrics

- Route calculation time tracking
- Crime data freshness monitoring
- Safety score distribution analysis
- API response time metrics

## Future Enhancements

### Planned Features

1. **Real-time Crime Updates**: Live crime data integration
2. **Weather Integration**: Weather-based safety adjustments
3. **Time-of-Day Factors**: Rush hour and night-time adjustments
4. **User Preferences**: Customizable safety vs. speed weights
5. **Machine Learning**: Predictive crime modeling

### Performance Improvements

1. **Spatial Indexing**: R-tree implementation for faster crime queries
2. **Route Caching**: Pre-computed routes for common destinations
3. **Parallel Processing**: Multi-threaded crime analysis
4. **Graph Optimization**: Reduced waypoint generation for faster routing

## References

- Dijkstra's Algorithm: [Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- Crime Data Sources: SF Police Department, CrimeOMeter API
- Spatial Analysis: PostGIS documentation
- Route Optimization: Graph theory and network analysis
