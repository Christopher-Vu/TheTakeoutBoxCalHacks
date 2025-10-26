#!/usr/bin/env python3
"""
Crime-Aware Router - Dijkstra algorithm with crime data integration
Uses PostgreSQL crime data to create safety-weighted routes
"""

import math
import heapq
import asyncio
from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import sys
import os
import asyncpg
from sqlalchemy import create_engine, text
import requests
import logging
from typing import Optional

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logger = logging.getLogger(__name__)

# Mapbox configuration
MAPBOX_ACCESS_TOKEN = os.getenv('MAPBOX_ACCESS_TOKEN', 'your_mapbox_token_here')
MAPBOX_DIRECTIONS_URL = 'https://api.mapbox.com/directions/v5/mapbox'

@dataclass
class CrimePoint:
    """Crime data point with location and severity"""
    lat: float
    lng: float
    severity: int
    crime_type: str
    occurred_at: datetime
    hours_ago: float
    distance_to_route: float = 0.0

@dataclass
class RouteSegment:
    """Route segment with safety metrics"""
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    distance: float
    safety_score: float
    crime_density: float
    high_severity_crimes: int
    recent_crimes: int
    critical_crimes_24h: int  # Crimes within 24 hours
    hours_to_nearest_crime: float  # Time to nearest recent crime
    crime_density_score: float  # Weighted density score
    edge_weight: float

@dataclass
class SafetyRoute:
    """Complete route with crime-aware safety metrics"""
    segments: List[RouteSegment]
    total_distance: float
    total_safety_score: float
    total_crime_penalty: float
    route_type: str
    path_coordinates: List[Tuple[float, float]]

class CrimeAwareRouter:
    """Router using Dijkstra's algorithm with crime data integration"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        
        # Crime influence parameters
        self.severity_weights = {
            1: 0.1,   # Very low
            2: 0.2,   # Low
            3: 0.3,   # Low-Medium
            4: 0.4,   # Medium
            5: 0.5,   # Medium-High
            6: 0.7,   # High
            7: 0.8,   # High
            8: 0.9,   # Very High
            9: 1.0,   # Critical
            10: 1.0   # Critical
        }
        
        # Time decay factors with hour-level precision
        self.critical_hours = 24      # 24-hour crimes (extreme penalty)
        self.recent_days = 7          # Recent crimes (high weight)
        self.medium_days = 30         # Medium recency (reduced weight)
        self.old_days = 90            # Old crimes (minimal weight)
        
        # Penalty multipliers for different time windows
        self.critical_penalty_multiplier = 10000.0  # 24-hour crimes (near-blocking)
        self.recent_penalty_multiplier = 10.0       # 1-7 days
        self.medium_penalty_multiplier = 1.0       # 7-30 days
        self.old_penalty_multiplier = 0.3           # 30-90 days
        self.ancient_penalty_multiplier = 0.1       # 90+ days
        
        # Distance influence radius (meters) - reduced to 100m
        self.crime_influence_radius = 100  # 100m radius
        
        # Mapbox configuration
        self.mapbox_token = MAPBOX_ACCESS_TOKEN
        self.max_waypoints = 25  # Mapbox limit
        
    async def find_optimal_route(self, start_lat: float, start_lng: float,
                                end_lat: float, end_lng: float,
                                route_type: str = 'balanced') -> Dict[str, Any]:
        """Find both fastest and safest routes for comparison"""
        
        # Get crime data for the area
        buffer = 0.01  # ~1km buffer
        crime_data = await self._get_crime_data_for_area(
            min(start_lat, end_lat) - buffer,
            min(start_lng, end_lng) - buffer,
            max(start_lat, end_lat) + buffer,
            max(start_lng, end_lng) + buffer
        )
        
        # 1. Get FASTEST route (direct, no crime avoidance)
        fastest_waypoints = [(start_lng, start_lat), (end_lng, end_lat)]
        fastest_response = await self._get_mapbox_route(fastest_waypoints, profile='walking')
        
        if not fastest_response:
            raise Exception("Failed to get fastest route from Mapbox")
        
        # 2. Get SAFEST route (crime-aware waypoints)
        safest_waypoints = await self._get_crime_aware_waypoints(
            start_lat, start_lng, end_lat, end_lng, crime_data
        )
        safest_response = await self._get_mapbox_route(safest_waypoints, profile='walking')
        
        if not safest_response:
            raise Exception("Failed to get safest route from Mapbox")
        
        # Build both routes
        fastest_route = self._build_route_from_response(fastest_response, crime_data, 'fastest')
        safest_route = self._build_route_from_response(safest_response, crime_data, 'safest')
        
        # Calculate comparison metrics
        time_diff_seconds = safest_response['routes'][0]['duration'] - fastest_response['routes'][0]['duration']
        distance_diff_meters = safest_route['total_distance'] - fastest_route['total_distance']
        safety_improvement = safest_route['total_safety_score'] - fastest_route['total_safety_score']
        
        return {
            'fastest_route': fastest_route,
            'safest_route': safest_route,
            'comparison': {
                'time_difference_seconds': round(time_diff_seconds, 1),
                'time_difference_minutes': round(time_diff_seconds / 60, 1),
                'distance_difference_meters': round(distance_diff_meters, 1),
                'distance_difference_percent': round((distance_diff_meters / fastest_route['total_distance']) * 100, 1),
                'safety_improvement': round(safety_improvement, 1),
                'safety_improvement_percent': round((safety_improvement / max(fastest_route['total_safety_score'], 0.1)) * 100, 1)
            }
        }
    
    def _build_route_from_response(self, mapbox_response: dict, crime_data: List[CrimePoint], route_type: str) -> Dict[str, Any]:
        """Build route data from Mapbox response"""
        # Parse route coordinates
        path_coordinates = self._parse_mapbox_route(mapbox_response)
        
        if not path_coordinates:
            raise Exception("No route found")
        
        # Calculate route metrics
        segments = self._create_route_segments(path_coordinates, crime_data)
        
        # Calculate totals
        total_distance = mapbox_response['routes'][0]['distance']  # meters
        total_duration = mapbox_response['routes'][0]['duration']  # seconds
        total_safety_score = sum(seg.safety_score * seg.distance for seg in segments) / total_distance if total_distance > 0 else 0
        total_crime_penalty = sum(self._calculate_segment_crime_penalty(
            seg.start_lat, seg.start_lng, seg.end_lat, seg.end_lng, crime_data
        ) for seg in segments)
        
        # Get critical crime zones
        critical_crimes = [
            {
                'lat': crime.lat,
                'lng': crime.lng,
                'crime_type': crime.crime_type,
                'severity': crime.severity,
                'hours_ago': crime.hours_ago
            }
            for crime in crime_data 
            if crime.hours_ago <= 24 and crime.severity >= 7
        ]
        
        return {
            'route_type': route_type,
            'total_distance': total_distance,
            'total_duration': total_duration,
            'total_safety_score': total_safety_score,
            'total_crime_penalty': total_crime_penalty,
            'path_coordinates': [(coord[0], coord[1]) for coord in path_coordinates],
            'segments': [
                {
                    'start_lat': seg.start_lat,
                    'start_lng': seg.start_lng,
                    'end_lat': seg.end_lat,
                    'end_lng': seg.end_lng,
                    'distance': seg.distance,
                    'safety_score': seg.safety_score,
                    'crime_density': seg.crime_density,
                    'high_severity_crimes': seg.high_severity_crimes,
                    'recent_crimes': seg.recent_crimes
                }
                for seg in segments
            ],
            'critical_crime_zones': critical_crimes[:20]  # Limit to 20 most critical
        }
    
    def _generate_waypoints(self, start_lat: float, start_lng: float,
                           end_lat: float, end_lng: float, num_points: int = 50) -> List[Tuple[float, float]]:
        """Generate waypoints between start and end"""
        waypoints = []
        
        # Add start point
        waypoints.append((start_lat, start_lng))
        
        # Generate intermediate points
        for i in range(1, num_points - 1):
            ratio = i / (num_points - 1)
            lat = start_lat + (end_lat - start_lat) * ratio
            lng = start_lng + (end_lng - start_lng) * ratio
            
            # Add some variation to avoid exact straight line
            variation_lat = (i % 3 - 1) * 0.001  # Small variation
            variation_lng = (i % 2) * 0.001
            waypoints.append((lat + variation_lat, lng + variation_lng))
        
        # Add end point
        waypoints.append((end_lat, end_lng))
        
        return waypoints
    
    async def _get_crime_data_for_area(self, min_lat: float, min_lng: float,
                                     max_lat: float, max_lng: float) -> List[CrimePoint]:
        """Get crime data for the bounding area"""
        
        # Expand bounding box to ensure we capture nearby crimes
        lat_buffer = 0.01  # ~1km
        lng_buffer = 0.01
        
        query = text("""
            SELECT lat, lng, severity, crime_type, occurred_at,
                   EXTRACT(EPOCH FROM (NOW() - occurred_at))/3600 as hours_ago
            FROM crimes 
            WHERE lat BETWEEN :min_lat - :lat_buffer AND :max_lat + :lat_buffer
            AND lng BETWEEN :min_lng - :lng_buffer AND :max_lng + :lng_buffer
            AND occurred_at >= NOW() - INTERVAL '90 days'
            ORDER BY occurred_at DESC
        """)
        
        with self.engine.connect() as conn:
            result = conn.execute(query, {
                'min_lat': min_lat,
                'max_lat': max_lat,
                'min_lng': min_lng,
                'max_lng': max_lng,
                'lat_buffer': lat_buffer,
                'lng_buffer': lng_buffer
            })
            
            crimes = []
            for row in result:
                crimes.append(CrimePoint(
                    lat=float(row.lat),
                    lng=float(row.lng),
                    severity=int(row.severity),
                    crime_type=str(row.crime_type),
                    occurred_at=row.occurred_at,
                    hours_ago=float(row.hours_ago)
                ))
            
            return crimes
    
    async def _get_crime_aware_waypoints(self, start_lat: float, start_lng: float,
                                         end_lat: float, end_lng: float,
                                         crime_data: List[CrimePoint]) -> List[Tuple[float, float]]:
        """
        Generate waypoints that avoid high-crime areas.
        Returns list of (lng, lat) tuples for Mapbox API.
        """
        waypoints = [(start_lng, start_lat)]
        
        # Find critical crime zones (24-hour crimes with high severity)
        critical_zones = [
            crime for crime in crime_data 
            if crime.hours_ago <= 24 and crime.severity >= 7
        ]
        
        # If there are critical zones, add avoidance waypoints
        if critical_zones and len(critical_zones) < 10:
            # Create a simple path that avoids the most dangerous areas
            mid_lat = (start_lat + end_lat) / 2
            mid_lng = (start_lng + end_lng) / 2
            
            # Check if middle point is safe
            is_safe = True
            for crime in critical_zones:
                dist = self._calculate_distance(mid_lat, mid_lng, crime.lat, crime.lng)
                if dist < 200:  # Within 200m of critical crime
                    is_safe = False
                    break
            
            if not is_safe:
                # Add offset waypoint to avoid the area
                offset_lat = mid_lat + (0.002 if start_lat < end_lat else -0.002)
                offset_lng = mid_lng + (0.002 if start_lng < end_lng else -0.002)
                waypoints.append((offset_lng, offset_lat))
        
        waypoints.append((end_lng, end_lat))
        return waypoints
    
    async def _get_mapbox_route(self, waypoints: List[Tuple[float, float]], 
                               profile: str = 'walking') -> Optional[dict]:
        """
        Get route from Mapbox Directions API.
        
        Args:
            waypoints: List of (lng, lat) tuples
            profile: 'walking', 'cycling', or 'driving'
        
        Returns:
            Mapbox route response or None
        """
        # Format waypoints for Mapbox API
        coordinates = ';'.join([f"{lng},{lat}" for lng, lat in waypoints])
        
        # Build API URL
        url = f"{MAPBOX_DIRECTIONS_URL}/{profile}/{coordinates}"
        
        params = {
            'access_token': self.mapbox_token,
            'geometries': 'geojson',
            'overview': 'full',
            'steps': 'true',
            'alternatives': 'false'
        }
        
        try:
            # Make async HTTP request
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.get(url, params=params, timeout=10)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Mapbox API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Mapbox API request failed: {e}")
            return None
    
    def _parse_mapbox_route(self, mapbox_response: dict) -> List[List[float]]:
        """
        Extract coordinates from Mapbox response.
        
        Returns:
            List of [lat, lng] coordinates
        """
        if not mapbox_response or 'routes' not in mapbox_response:
            return []
        
        route = mapbox_response['routes'][0]
        geometry = route['geometry']
        
        # Convert [lng, lat] to [lat, lng]
        coordinates = [[coord[1], coord[0]] for coord in geometry['coordinates']]
        
        return coordinates
    
    def _create_route_segments(self, path_coordinates: List[List[float]], 
                              crime_data: List[CrimePoint]) -> List[RouteSegment]:
        """Create route segments from path coordinates"""
        segments = []
        
        for i in range(len(path_coordinates) - 1):
            start_lat, start_lng = path_coordinates[i]
            end_lat, end_lng = path_coordinates[i + 1]
            
            distance = self._calculate_distance(start_lat, start_lng, end_lat, end_lng)
            segment_crimes = self._get_crimes_near_segment(
                start_lat, start_lng, end_lat, end_lng, crime_data
            )
            
            # Calculate metrics
            crime_density = len(segment_crimes) / max(distance / 1000, 0.001)
            high_severity_crimes = sum(1 for c in segment_crimes if c.severity >= 7)
            recent_crimes = sum(1 for c in segment_crimes if c.hours_ago <= 24)
            
            safety_score = 100.0
            if segment_crimes:
                penalty = min(100, crime_density * 10 + high_severity_crimes * 20 + recent_crimes * 30)
                safety_score = max(0, 100 - penalty)
            
            hours_to_nearest_crime = min((c.hours_ago for c in segment_crimes), default=999.0)
            crime_density_score = min(1.0, crime_density / 10.0)
            edge_weight = distance + self._calculate_segment_crime_penalty(
                start_lat, start_lng, end_lat, end_lng, crime_data
            )
            
            segments.append(RouteSegment(
                start_lat=start_lat, start_lng=start_lng,
                end_lat=end_lat, end_lng=end_lng,
                distance=distance, safety_score=safety_score,
                crime_density=crime_density,
                high_severity_crimes=high_severity_crimes,
                recent_crimes=recent_crimes,
                critical_crimes_24h=recent_crimes,
                hours_to_nearest_crime=hours_to_nearest_crime,
                crime_density_score=crime_density_score,
                edge_weight=edge_weight
            ))
        
        return segments
    
    def _build_crime_weighted_graph(self, waypoints: List[Tuple[float, float]], 
                                   crime_data: List[CrimePoint]) -> Dict[int, List[Tuple[int, float]]]:
        """Build graph with crime-weighted edges"""
        graph = {i: [] for i in range(len(waypoints))}
        
        for i in range(len(waypoints)):
            for j in range(i + 1, min(i + 5, len(waypoints))):  # Connect to next 4 points
                start_lat, start_lng = waypoints[i]
                end_lat, end_lng = waypoints[j]
                
                # Calculate base distance
                distance = self._calculate_distance(start_lat, start_lng, end_lat, end_lng)
                
                # Calculate crime penalty for this segment
                crime_penalty = self._calculate_segment_crime_penalty(
                    start_lat, start_lng, end_lat, end_lng, crime_data
                )
                
                # Calculate edge weight
                edge_weight = distance + crime_penalty
                
                graph[i].append((j, edge_weight))
        
        return graph
    
    def _calculate_segment_crime_penalty(self, start_lat: float, start_lng: float,
                                        end_lat: float, end_lng: float,
                                        crime_data: List[CrimePoint]) -> float:
        """
        Calculate crime penalty for a route segment using enhanced formula.
        
        This method implements the core penalty calculation that heavily penalizes
        routes passing through high-crime areas, especially recent crimes within 24 hours.
        
        Args:
            start_lat, start_lng: Segment start coordinates
            end_lat, end_lng: Segment end coordinates  
            crime_data: List of crime points in the area
            
        Returns:
            Total penalty for this route segment
            
        Formula:
            For 24-hour crimes: penalty = time_factor × distance_factor × severity_factor × segment_distance × 1000
            For other crimes: penalty = time_factor × distance_factor × severity_factor × 100
            
        This ensures that:
        - 24-hour crimes create penalties proportional to segment length (longer segments = higher penalty)
        - Recent crimes are heavily penalized but not absolutely blocked
        - Older crimes have minimal impact on routing decisions
        """
        penalty = 0.0
        segment_distance = self._calculate_distance(start_lat, start_lng, end_lat, end_lng)
        
        # Get crimes near this segment
        segment_crimes = self._get_crimes_near_segment(
            start_lat, start_lng, end_lat, end_lng, crime_data
        )
        
        for crime in segment_crimes:
            # Calculate time decay factor using hours_ago
            time_factor = self._calculate_time_decay(crime.hours_ago)
            
            # Calculate distance factor (closer = higher impact)
            # Formula: max(0, 1 - (crime_distance / 100m))
            distance_factor = max(0, 1 - (crime.distance_to_route / self.crime_influence_radius))
            
            # Calculate severity factor from existing weights
            severity_factor = self.severity_weights.get(crime.severity, 0.5)
            
            # Base penalty calculation
            base_penalty = time_factor * distance_factor * severity_factor
            
            # For 24-hour crimes, make penalty proportional to segment distance
            # This ensures longer segments through recent crime areas are heavily penalized
            if crime.hours_ago <= self.critical_hours:
                penalty += base_penalty * segment_distance * 1000  # Extreme penalty for 24h crimes
            else:
                penalty += base_penalty * 100  # Standard penalty for older crimes
        
        return penalty
    
    def _get_crimes_near_segment(self, start_lat: float, start_lng: float,
                                end_lat: float, end_lng: float,
                                crime_data: List[CrimePoint]) -> List[CrimePoint]:
        """Get crimes within influence radius of segment"""
        nearby_crimes = []
        
        for crime in crime_data:
            # Calculate distance from crime to segment
            distance = self._distance_point_to_line_segment(
                crime.lat, crime.lng,
                start_lat, start_lng, end_lat, end_lng
            )
            
            if distance <= self.crime_influence_radius:
                crime.distance_to_route = distance
                nearby_crimes.append(crime)
        
        return nearby_crimes
    
    def _distance_point_to_line_segment(self, px: float, py: float,
                                       x1: float, y1: float, x2: float, y2: float) -> float:
        """Calculate distance from point to line segment"""
        # Convert to meters (approximate)
        A = px - x1
        B = py - y1
        C = x2 - x1
        D = y2 - y1
        
        dot = A * C + B * D
        len_sq = C * C + D * D
        
        if len_sq == 0:
            return math.sqrt(A * A + B * B) * 111000  # Convert to meters
        
        param = dot / len_sq
        
        if param < 0:
            xx, yy = x1, y1
        elif param > 1:
            xx, yy = x2, y2
        else:
            xx = x1 + param * C
            yy = y1 + param * D
        
        dx = px - xx
        dy = py - yy
        return math.sqrt(dx * dx + dy * dy) * 111000  # Convert to meters
    
    def _calculate_time_decay(self, hours_ago: float) -> float:
        """
        Calculate time decay factor for crime recency with hour-level precision.
        
        This method implements the core time decay logic that heavily penalizes
        recent crimes, especially those within 24 hours, to ensure routes avoid
        fresh crime scenes.
        
        Args:
            hours_ago: Hours since the crime occurred
            
        Returns:
            Time decay factor (0.1 to 10000.0)
            
        Formula:
            - 0-24 hours: 10000.0 (extreme penalty, near-blocking)
            - 1-7 days: 10.0 (high penalty)
            - 7-30 days: 1.0 (normal penalty)
            - 30-90 days: 0.3 (reduced penalty)
            - 90+ days: 0.1 (minimal penalty)
        """
        if hours_ago <= self.critical_hours:
            return self.critical_penalty_multiplier  # 10000.0 - extreme penalty
        elif hours_ago <= self.recent_days * 24:
            return self.recent_penalty_multiplier    # 10.0 - high penalty
        elif hours_ago <= self.medium_days * 24:
            return self.medium_penalty_multiplier    # 1.0 - normal penalty
        elif hours_ago <= self.old_days * 24:
            return self.old_penalty_multiplier        # 0.3 - reduced penalty
        else:
            return self.ancient_penalty_multiplier   # 0.1 - minimal penalty
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in meters"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _dijkstra_safest(self, graph: Dict[int, List[Tuple[int, float]]], 
                        start: int, end: int) -> List[int]:
        """Dijkstra for safest route (prioritizes safety over distance)"""
        return self._dijkstra(graph, start, end, safety_weight=0.8, distance_weight=0.2)
    
    def _dijkstra_fastest(self, graph: Dict[int, List[Tuple[int, float]]], 
                         start: int, end: int) -> List[int]:
        """Dijkstra for fastest route (prioritizes distance over safety)"""
        return self._dijkstra(graph, start, end, safety_weight=0.2, distance_weight=0.8)
    
    def _dijkstra_balanced(self, graph: Dict[int, List[Tuple[int, float]]], 
                          start: int, end: int) -> List[int]:
        """Dijkstra for balanced route"""
        return self._dijkstra(graph, start, end, safety_weight=0.5, distance_weight=0.5)
    
    def _dijkstra(self, graph: Dict[int, List[Tuple[int, float]]], 
                  start: int, end: int, safety_weight: float, distance_weight: float) -> List[int]:
        """Dijkstra's algorithm implementation"""
        distances = {node: float('inf') for node in graph}
        distances[start] = 0
        previous = {node: None for node in graph}
        
        pq = [(0, start)]
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if current == end:
                break
            
            if current_dist > distances[current]:
                continue
            
            for neighbor, weight in graph[current]:
                new_dist = current_dist + weight
                
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))
        
        # Reconstruct path
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = previous[current]
        
        return path[::-1]
    
    def _path_to_segments(self, path: List[int], waypoints: List[Tuple[float, float]], 
                         crime_data: List[CrimePoint]) -> List[RouteSegment]:
        """Convert path to route segments with safety metrics"""
        segments = []
        
        for i in range(len(path) - 1):
            start_idx = path[i]
            end_idx = path[i + 1]
            
            start_lat, start_lng = waypoints[start_idx]
            end_lat, end_lng = waypoints[end_idx]
            
            distance = self._calculate_distance(start_lat, start_lng, end_lat, end_lng)
            
            # Calculate safety metrics for this segment
            segment_crimes = self._get_crimes_near_segment(
                start_lat, start_lng, end_lat, end_lng, crime_data
            )
            
            safety_score = self._calculate_segment_safety(segment_crimes)
            crime_density = len(segment_crimes)
            high_severity = sum(1 for c in segment_crimes if c.severity >= 7)
            recent_crimes = sum(1 for c in segment_crimes if c.hours_ago <= 7 * 24)  # 7 days in hours
            critical_crimes_24h = sum(1 for c in segment_crimes if c.hours_ago <= 24)
            
            # Calculate hours to nearest crime
            if segment_crimes:
                hours_to_nearest_crime = min(c.hours_ago for c in segment_crimes)
            else:
                hours_to_nearest_crime = 999999.0  # Use large number instead of inf
            
            # Calculate weighted crime density score
            crime_density_score = sum(
                self._calculate_time_decay(c.hours_ago) * self.severity_weights.get(c.severity, 0.5)
                for c in segment_crimes
            )
            
            segments.append(RouteSegment(
                start_lat=start_lat,
                start_lng=start_lng,
                end_lat=end_lat,
                end_lng=end_lng,
                distance=distance,
                safety_score=safety_score,
                crime_density=crime_density,
                high_severity_crimes=high_severity,
                recent_crimes=recent_crimes,
                critical_crimes_24h=critical_crimes_24h,
                hours_to_nearest_crime=hours_to_nearest_crime,
                crime_density_score=crime_density_score,
                edge_weight=distance + (100 - safety_score) * 10
            ))
        
        return segments
    
    def _calculate_segment_safety(self, crimes: List[CrimePoint]) -> float:
        """
        Calculate safety score for a segment (0-100, higher = safer).
        
        This method calculates the safety score based on crime density, recency,
        and severity within the segment's influence radius.
        
        Args:
            crimes: List of crime points near this segment
            
        Returns:
            Safety score from 0-100 (100 = safest, 0 = most dangerous)
            
        Formula:
            safety_score = max(0, 100 - total_penalty)
            where total_penalty = Σ(time_factor × severity_factor × distance_factor × 20)
        """
        if not crimes:
            return 100.0
        
        total_penalty = 0
        for crime in crimes:
            # Use hours_ago for more precise time decay calculation
            time_factor = self._calculate_time_decay(crime.hours_ago)
            severity_factor = self.severity_weights.get(crime.severity, 0.5)
            distance_factor = max(0, 1 - (crime.distance_to_route / self.crime_influence_radius))
            
            penalty = time_factor * severity_factor * distance_factor * 20
            total_penalty += penalty
        
        safety_score = max(0, 100 - total_penalty)
        return safety_score
    
    def _calculate_crime_density_map(self, min_lat: float, min_lng: float,
                                   max_lat: float, max_lng: float,
                                   crime_data: List[CrimePoint]) -> Dict[Tuple[int, int], float]:
        """
        Calculate crime density map for visualization and route optimization.
        
        Creates a spatial grid that tracks crime density for visualization and routing.
        Divides the area into 100m × 100m grid cells and counts crimes per cell
        weighted by severity and recency.
        
        Args:
            min_lat, min_lng: Bounding box minimum coordinates
            max_lat, max_lng: Bounding box maximum coordinates
            crime_data: List of crime points in the area
            
        Returns:
            Dictionary mapping (grid_x, grid_y) to weighted crime density
        """
        # Calculate grid cell size (100m × 100m)
        lat_per_100m = 100 / 111000  # Approximate latitude per 100m
        lng_per_100m = 100 / (111000 * math.cos(math.radians((min_lat + max_lat) / 2)))
        
        # Calculate grid dimensions
        lat_range = max_lat - min_lat
        lng_range = max_lng - min_lng
        grid_lat_cells = int(lat_range / lat_per_100m) + 1
        grid_lng_cells = int(lng_range / lng_per_100m) + 1
        
        # Initialize density map
        density_map = {}
        
        # Process each crime
        for crime in crime_data:
            # Calculate grid coordinates
            grid_lat = int((crime.lat - min_lat) / lat_per_100m)
            grid_lng = int((crime.lng - min_lng) / lng_per_100m)
            
            # Skip crimes outside the grid
            if grid_lat < 0 or grid_lat >= grid_lat_cells or grid_lng < 0 or grid_lng >= grid_lng_cells:
                continue
            
            # Calculate weighted density contribution
            time_factor = self._calculate_time_decay(crime.hours_ago)
            severity_factor = self.severity_weights.get(crime.severity, 0.5)
            weighted_contribution = time_factor * severity_factor
            
            # Add to density map
            grid_key = (grid_lat, grid_lng)
            if grid_key not in density_map:
                density_map[grid_key] = 0.0
            density_map[grid_key] += weighted_contribution
        
        return density_map
    
    async def get_crime_density_heatmap(self, min_lat: float, min_lng: float,
                                 max_lat: float, max_lng: float) -> Dict[str, Any]:
        """
        Get crime density heatmap data for frontend visualization.
        
        Returns a grid of crime density values suitable for heatmap visualization.
        
        Args:
            min_lat, min_lng: Bounding box minimum coordinates
            max_lat, max_lng: Bounding box maximum coordinates
            
        Returns:
            Dictionary containing heatmap data for visualization
        """
        # Get crime data for the area
        crime_data = await self._get_crime_data_for_area(min_lat, min_lng, max_lat, max_lng)
        
        # Calculate density map
        density_map = self._calculate_crime_density_map(min_lat, min_lng, max_lat, max_lng, crime_data)
        
        # Convert to frontend-friendly format
        heatmap_data = []
        for (grid_lat, grid_lng), density in density_map.items():
            # Convert grid coordinates back to lat/lng
            cell_lat = min_lat + (grid_lat * 100 / 111000)
            cell_lng = min_lng + (grid_lng * 100 / (111000 * math.cos(math.radians((min_lat + max_lat) / 2))))
            
            heatmap_data.append({
                'lat': cell_lat,
                'lng': cell_lng,
                'density': density,
                'intensity': min(1.0, density / 10.0)  # Normalize for visualization
            })
        
        return {
            'heatmap_data': heatmap_data,
            'total_crimes': len(crime_data),
            'critical_crimes_24h': sum(1 for c in crime_data if c.hours_ago <= 24),
            'high_severity_crimes': sum(1 for c in crime_data if c.severity >= 7)
        }
    
    def get_route_safety_breakdown(self, route: SafetyRoute) -> Dict[str, Any]:
        """
        Get detailed safety breakdown for a route.
        
        Returns comprehensive safety metrics for route analysis.
        
        Args:
            route: SafetyRoute object to analyze
            
        Returns:
            Dictionary containing detailed safety breakdown
        """
        total_24h_crimes = sum(seg.critical_crimes_24h for seg in route.segments)
        total_high_severity = sum(seg.high_severity_crimes for seg in route.segments)
        total_recent_crimes = sum(seg.recent_crimes for seg in route.segments)
        avg_crime_density = sum(seg.crime_density_score for seg in route.segments) / len(route.segments)
        
        # Find most dangerous segment
        most_dangerous_segment = min(route.segments, key=lambda s: s.safety_score)
        
        return {
            '24h_crimes_avoided': total_24h_crimes,
            'high_severity_crimes_avoided': total_high_severity,
            'recent_crimes_encountered': total_recent_crimes,
            'average_crime_density': avg_crime_density,
            'most_dangerous_segment': {
                'safety_score': most_dangerous_segment.safety_score,
                'crime_density': most_dangerous_segment.crime_density,
                'critical_crimes_24h': most_dangerous_segment.critical_crimes_24h
            },
            'route_safety_summary': {
                'total_distance': route.total_distance,
                'average_safety': route.total_safety_score,
                'safety_grade': self._calculate_safety_grade(route.total_safety_score)
            }
        }
    
    def _calculate_safety_grade(self, safety_score: float) -> str:
        """Calculate safety grade from safety score"""
        if safety_score >= 85:
            return 'A'  # Very Safe
        elif safety_score >= 70:
            return 'B'  # Safe
        elif safety_score >= 50:
            return 'C'  # Moderate Risk
        elif safety_score >= 30:
            return 'D'  # High Risk
        else:
            return 'F'  # Very High Risk
    
    async def get_blocked_areas(self, min_lat: float, min_lng: float,
                         max_lat: float, max_lng: float) -> List[Dict[str, Any]]:
        """
        Get coordinates of 24-hour crime zones (blocked areas).
        
        Returns areas with recent crimes that should be avoided.
        
        Args:
            min_lat, min_lng: Bounding box minimum coordinates
            max_lat, max_lng: Bounding box maximum coordinates
            
        Returns:
            List of blocked area coordinates with crime details
        """
        # Get crime data for the area
        crime_data = await self._get_crime_data_for_area(min_lat, min_lng, max_lat, max_lng)
        
        # Filter for 24-hour crimes
        critical_crimes = [c for c in crime_data if c.hours_ago <= 24]
        
        blocked_areas = []
        for crime in critical_crimes:
            blocked_areas.append({
                'lat': crime.lat,
                'lng': crime.lng,
                'severity': crime.severity,
                'crime_type': crime.crime_type,
                'hours_ago': crime.hours_ago,
                'blocked_radius': 100,  # 100m blocked radius
                'penalty_level': 'CRITICAL'
            })
        
        return blocked_areas
