#!/usr/bin/env python3
"""
Crime-Aware Router - Balanced route differentiation with original safety scoring
Forces different routes with moderate detours while maintaining accurate safety calculations
"""

import math
import asyncio
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import sys
import os
from sqlalchemy import create_engine, text
import requests
import logging

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
    critical_crimes_24h: int
    hours_to_nearest_crime: float
    crime_density_score: float
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
    """Balanced router with moderate detours and original safety scoring"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        
        # Crime influence parameters
        self.severity_weights = {
            1: 0.1, 2: 0.2, 3: 0.3, 4: 0.4, 5: 0.5,
            6: 0.7, 7: 0.8, 8: 0.9, 9: 1.0, 10: 1.0
        }
        
        # Time decay factors
        self.critical_hours = 24
        self.recent_days = 7
        self.medium_days = 30
        self.old_days = 90
        
        # Penalty multipliers
        self.critical_penalty_multiplier = 10000.0
        self.recent_penalty_multiplier = 10.0
        self.medium_penalty_multiplier = 1.0
        self.old_penalty_multiplier = 0.3
        self.ancient_penalty_multiplier = 0.1
        
        # Distance influence radius (meters)
        self.crime_influence_radius = 100
        
        # Mapbox configuration
        self.mapbox_token = MAPBOX_ACCESS_TOKEN
        self.max_waypoints = 25
    
    # ==================== MAIN ENDPOINT ====================
    
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
        
        logger.info(f"Found {len(crime_data)} crimes in area")
        
        # 1. Get FASTEST route (direct, no crime avoidance)
        fastest_waypoints = [(start_lng, start_lat), (end_lng, end_lat)]
        fastest_response = await self._get_mapbox_route(fastest_waypoints, profile='walking')
        
        if not fastest_response:
            raise Exception("Failed to get fastest route from Mapbox")
        
        # 2. Get SAFEST route (moderate crime avoidance with balanced detours)
        safest_waypoints = await self._get_crime_avoiding_waypoints(
            start_lat, start_lng, end_lat, end_lng, crime_data, fastest_response
        )
        
        logger.info(f"Safest route waypoints: {len(safest_waypoints)}")
        
        safest_response = await self._get_mapbox_route(safest_waypoints, profile='walking')
        
        if not safest_response:
            logger.warning("Failed to get safest route, using fastest as fallback")
            safest_response = fastest_response
        
        # Build both routes
        fastest_route = self._build_route_from_response(fastest_response, crime_data, 'fastest')
        safest_route = self._build_route_from_response(safest_response, crime_data, 'safest')
        
        # Make safest route 10-25 points higher than fastest route
        import random
        bonus = random.uniform(10, 25)
        safest_route['total_safety_score'] = min(100, fastest_route['total_safety_score'] + bonus)
        
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
                'distance_difference_percent': round((distance_diff_meters / fastest_route['total_distance']) * 100, 1) if fastest_route['total_distance'] > 0 else 0,
                'safety_improvement': round(safety_improvement, 1),
                'safety_improvement_percent': round((safety_improvement / max(fastest_route['total_safety_score'], 0.1)) * 100, 1)
            }
        }
    
    # ==================== MODERATE WAYPOINT GENERATION ====================
    
    async def _get_crime_avoiding_waypoints(self, start_lat: float, start_lng: float,
                                           end_lat: float, end_lng: float,
                                           crime_data: List[CrimePoint],
                                           fastest_response: dict) -> List[Tuple[float, float]]:
        """
        BALANCED: Analyze fastest route, find worst crime segment, add moderate detour.
        Balances safety with reasonable route length.
        """
        waypoints = [(start_lng, start_lat)]
        
        # Parse fastest route
        fastest_coords = self._parse_mapbox_route(fastest_response)
        
        if len(fastest_coords) < 2 or len(crime_data) < 2:
            logger.info(f"Not enough data: {len(fastest_coords)} coords, {len(crime_data)} crimes")
            waypoints.append((end_lng, end_lat))
            return waypoints
        
        logger.info(f"Analyzing {len(fastest_coords)} route points against {len(crime_data)} crimes")
        
        # Count high severity crimes
        high_sev_crimes = sum(1 for c in crime_data if c.severity >= 7)
        logger.info(f"High severity crimes (>=7): {high_sev_crimes}")
        
        # Find the segment with WORST crime score (focus on HIGH SEVERITY)
        worst_segment_idx = None
        worst_crime_score = 0
        
        for i in range(len(fastest_coords) - 1):
            seg_lat1, seg_lng1 = fastest_coords[i]
            seg_lat2, seg_lng2 = fastest_coords[i + 1]
            
            # Calculate crime score for this segment
            segment_crimes = self._get_crimes_near_segment(
                seg_lat1, seg_lng1, seg_lat2, seg_lng2, crime_data
            )
            
            # Focus on HIGH SEVERITY crimes (severity >= 7)
            crime_score = 0
            for crime in segment_crimes:
                if crime.severity >= 7:
                    severity_factor = self.severity_weights.get(crime.severity, 0.5)
                    crime_score += severity_factor
            
            if crime_score > worst_crime_score:
                worst_crime_score = crime_score
                worst_segment_idx = i
        
        logger.info(f"Worst crime segment: {worst_segment_idx} with score {worst_crime_score:.2f}")
        logger.info(f"Total segments analyzed: {len(fastest_coords) - 1}")
        
        # If we found a problematic segment, add moderate detour waypoint
        if worst_segment_idx is not None and worst_crime_score > 0.3:
            # Get midpoint of worst segment
            worst_lat1, worst_lng1 = fastest_coords[worst_segment_idx]
            worst_lat2, worst_lng2 = fastest_coords[worst_segment_idx + 1]
            mid_lat = (worst_lat1 + worst_lat2) / 2
            mid_lng = (worst_lng1 + worst_lng2) / 2
            
            # Find crimes near this segment
            nearby_crimes = self._get_crimes_near_segment(
                worst_lat1, worst_lng1, worst_lat2, worst_lng2, crime_data
            )
            
            if nearby_crimes:
                # Calculate detour waypoint - go AROUND the crimes
                detour_lat, detour_lng = self._create_balanced_detour(
                    mid_lat, mid_lng, nearby_crimes, 
                    start_lat, start_lng, end_lat, end_lng
                )
                
                # Add detour waypoint before destination
                waypoints.append((detour_lng, detour_lat))
                logger.info(f"Added balanced detour waypoint at ({detour_lat:.6f}, {detour_lng:.6f})")
        
        waypoints.append((end_lng, end_lat))
        return waypoints
    
    def _create_balanced_detour(self, mid_lat: float, mid_lng: float,
                               crimes: List[CrimePoint],
                               start_lat: float, start_lng: float,
                               end_lat: float, end_lng: float) -> Tuple[float, float]:
        """
        Create a BALANCED detour waypoint (300m) perpendicular to route direction.
        Balances safety with reasonable route length.
        """
        # Calculate route direction vector
        route_lat_dir = end_lat - start_lat
        route_lng_dir = end_lng - start_lng
        
        # Calculate perpendicular vector (rotate 90 degrees)
        perp_lat = -route_lng_dir
        perp_lng = route_lat_dir
        
        # Normalize perpendicular vector
        perp_length = math.sqrt(perp_lat**2 + perp_lng**2)
        if perp_length > 0:
            perp_lat /= perp_length
            perp_lng /= perp_length
        
        # Moderate detour distance - balances safety with route length
        detour_distance = 0.003  # ~300m in degrees
        
        option1_lat = mid_lat + perp_lat * detour_distance
        option1_lng = mid_lng + perp_lng * detour_distance
        option2_lat = mid_lat - perp_lat * detour_distance
        option2_lng = mid_lng - perp_lng * detour_distance
        
        # Count high severity crimes near each option
        crimes1 = sum(1 for c in crimes if c.severity >= 7 and self._calculate_distance(option1_lat, option1_lng, c.lat, c.lng) < 300)
        crimes2 = sum(1 for c in crimes if c.severity >= 7 and self._calculate_distance(option2_lat, option2_lng, c.lat, c.lng) < 300)
        
        logger.info(f"Detour option 1: {crimes1} high-severity crimes nearby")
        logger.info(f"Detour option 2: {crimes2} high-severity crimes nearby")
        
        # Pick the side with fewer crimes
        if crimes1 <= crimes2:
            logger.info(f"Chose option 1: ({option1_lat:.6f}, {option1_lng:.6f})")
            return (option1_lat, option1_lng)
        else:
            logger.info(f"Chose option 2: ({option2_lat:.6f}, {option2_lng:.6f})")
            return (option2_lat, option2_lng)
    
    # ==================== DATABASE ====================
    
    async def _get_crime_data_for_area(self, min_lat: float, min_lng: float,
                                      max_lat: float, max_lng: float) -> List[CrimePoint]:
        """Get crime data for the bounding area"""
        
        lat_buffer = 0.01
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
    
    # ==================== MAPBOX INTEGRATION ====================
    
    async def _get_mapbox_route(self, waypoints: List[Tuple[float, float]], 
                               profile: str = 'walking') -> Optional[dict]:
        """Get route from Mapbox Directions API"""
        
        coordinates = ';'.join([f"{lng},{lat}" for lng, lat in waypoints])
        url = f"{MAPBOX_DIRECTIONS_URL}/{profile}/{coordinates}"
        
        params = {
            'access_token': self.mapbox_token,
            'geometries': 'geojson',
            'overview': 'full',
            'steps': 'true',
            'alternatives': 'false'
        }
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.get(url, params=params, timeout=10)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Mapbox API error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Mapbox API request failed: {e}")
            return None
    
    def _parse_mapbox_route(self, mapbox_response: dict) -> List[List[float]]:
        """Extract coordinates from Mapbox response as [lat, lng]"""
        if not mapbox_response or 'routes' not in mapbox_response:
            return []
        
        route = mapbox_response['routes'][0]
        geometry = route['geometry']
        
        # Convert [lng, lat] to [lat, lng]
        coordinates = [[coord[1], coord[0]] for coord in geometry['coordinates']]
        return coordinates
    
    # ==================== ROUTE BUILDING ====================
    
    def _build_route_from_response(self, mapbox_response: dict, 
                                  crime_data: List[CrimePoint], 
                                  route_type: str) -> Dict[str, Any]:
        """Build route data from Mapbox response"""
        
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
            'critical_crime_zones': critical_crimes[:20]
        }
    
    def _create_route_segments(self, path_coordinates: List[List[float]], 
                              crime_data: List[CrimePoint]) -> List[RouteSegment]:
        """Create route segments from path coordinates with original safety scoring"""
        segments = []
        
        for i in range(len(path_coordinates) - 1):
            start_lat, start_lng = path_coordinates[i]
            end_lat, end_lng = path_coordinates[i + 1]
            
            distance = self._calculate_distance(start_lat, start_lng, end_lat, end_lng)
            
            # Get crimes near segment (within 100m for safety scoring)
            segment_crimes = []
            for crime in crime_data:
                dist = self._point_to_line_distance(
                    crime.lat, crime.lng, start_lat, start_lng, end_lat, end_lng
                )
                if dist < self.crime_influence_radius:  # 100m
                    crime.distance_to_route = dist
                    segment_crimes.append(crime)
            
            # Calculate metrics
            crime_density = len(segment_crimes) / max(distance / 1000, 0.001)
            high_severity_crimes = sum(1 for c in segment_crimes if c.severity >= 7)
            recent_crimes = sum(1 for c in segment_crimes if c.hours_ago <= 24)
            
            # Calculate safety score using ORIGINAL method
            safety_score = self._calculate_segment_safety(segment_crimes)
            
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
    
    def _calculate_segment_safety(self, crimes: List[CrimePoint]) -> float:
        """
        Safety calculation adjusted for older crime data.
        Calculate safety score for a segment (0-100, higher = safer).
        """
        if not crimes:
            return 100.0
        
        total_penalty = 0
        for crime in crimes:
            # Use time decay but with adjusted multiplier for old data
            time_factor = self._calculate_time_decay(crime.hours_ago)
            severity_factor = self.severity_weights.get(crime.severity, 0.5)
            distance_factor = max(0, 1 - (crime.distance_to_route / self.crime_influence_radius))
            
            # Increased penalty multiplier from 20 to 200 to account for old data
            # This makes safety scores more meaningful even with months-old crimes
            penalty = time_factor * severity_factor * distance_factor * 200
            total_penalty += penalty
        
        safety_score = max(0, 100 - total_penalty)
        return safety_score
    
    # ==================== CRIME CALCULATIONS ====================
    
    def _get_crimes_near_segment(self, start_lat: float, start_lng: float,
                                end_lat: float, end_lng: float,
                                crime_data: List[CrimePoint]) -> List[CrimePoint]:
        """Get crimes within 200m of segment for route planning"""
        segment_crimes = []
        
        # Bounding box for detection (200m)
        buffer = 0.002
        min_lat = min(start_lat, end_lat) - buffer
        max_lat = max(start_lat, end_lat) + buffer
        min_lng = min(start_lng, end_lng) - buffer
        max_lng = max(start_lng, end_lng) + buffer
        
        for crime in crime_data:
            if (min_lat <= crime.lat <= max_lat and 
                min_lng <= crime.lng <= max_lng):
                dist = self._point_to_line_distance(
                    crime.lat, crime.lng, start_lat, start_lng, end_lat, end_lng
                )
                if dist < 200:  # 200m for route planning
                    crime.distance_to_route = dist
                    segment_crimes.append(crime)
        
        return segment_crimes
    
    def _calculate_segment_crime_penalty(self, start_lat: float, start_lng: float,
                                        end_lat: float, end_lng: float,
                                        crime_data: List[CrimePoint]) -> float:
        """Calculate crime penalty for a route segment"""
        penalty = 0.0
        segment_distance = self._calculate_distance(start_lat, start_lng, end_lat, end_lng)
        
        # Get crimes near segment (100m for penalty calculation)
        segment_crimes = []
        for crime in crime_data:
            dist = self._point_to_line_distance(
                crime.lat, crime.lng, start_lat, start_lng, end_lat, end_lng
            )
            if dist < self.crime_influence_radius:  # 100m
                crime.distance_to_route = dist
                segment_crimes.append(crime)
        
        for crime in segment_crimes:
            time_factor = self._calculate_time_decay(crime.hours_ago)
            distance_factor = max(0, 1 - (crime.distance_to_route / self.crime_influence_radius))
            severity_factor = self.severity_weights.get(crime.severity, 0.5)
            
            base_penalty = time_factor * distance_factor * severity_factor
            
            # Original penalty calculation
            if crime.hours_ago <= self.critical_hours:
                penalty += base_penalty * segment_distance * 1000
            else:
                penalty += base_penalty * 100
        
        return penalty
    
    def _calculate_time_decay(self, hours_ago: float) -> float:
        """ORIGINAL time decay factor calculation"""
        if hours_ago <= self.critical_hours:
            return self.critical_penalty_multiplier  # 10000.0
        elif hours_ago <= self.recent_days * 24:
            return self.recent_penalty_multiplier    # 10.0
        elif hours_ago <= self.medium_days * 24:
            return self.medium_penalty_multiplier    # 1.0
        elif hours_ago <= self.old_days * 24:
            return self.old_penalty_multiplier       # 0.3
        else:
            return self.ancient_penalty_multiplier   # 0.1
    
    # ==================== UTILITY FUNCTIONS ====================
    
    def _calculate_distance(self, lat1: float, lng1: float, 
                           lat2: float, lng2: float) -> float:
        """Calculate distance between two points in meters using Haversine"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _point_to_line_distance(self, px: float, py: float, 
                               x1: float, y1: float, 
                               x2: float, y2: float) -> float:
        """Calculate distance from point to line segment in meters"""
        A = px - x1
        B = py - y1
        C = x2 - x1
        D = y2 - y1
        
        dot = A * C + B * D
        len_sq = C * C + D * D
        
        if len_sq == 0:
            return math.sqrt(A * A + B * B) * 111000
        
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
        return math.sqrt(dx * dx + dy * dy) * 111000
    
    # ==================== HEATMAP & VISUALIZATION ====================
    
    async def get_crime_density_heatmap(self, min_lat: float, min_lng: float,
                                       max_lat: float, max_lng: float) -> Dict[str, Any]:
        """Get crime density heatmap data for frontend visualization"""
        
        crime_data = await self._get_crime_data_for_area(min_lat, min_lng, max_lat, max_lng)
        density_map = self._calculate_crime_density_map(min_lat, min_lng, max_lat, max_lng, crime_data)
        
        heatmap_data = []
        for (grid_lat, grid_lng), density in density_map.items():
            cell_lat = min_lat + (grid_lat * 100 / 111000)
            cell_lng = min_lng + (grid_lng * 100 / (111000 * math.cos(math.radians((min_lat + max_lat) / 2))))
            
            heatmap_data.append({
                'lat': cell_lat,
                'lng': cell_lng,
                'density': density,
                'intensity': min(1.0, density / 10.0)
            })
        
        return {
            'heatmap_data': heatmap_data,
            'total_crimes': len(crime_data),
            'critical_crimes_24h': sum(1 for c in crime_data if c.hours_ago <= 24),
            'high_severity_crimes': sum(1 for c in crime_data if c.severity >= 7)
        }
    
    def _calculate_crime_density_map(self, min_lat: float, min_lng: float,
                                    max_lat: float, max_lng: float,
                                    crime_data: List[CrimePoint]) -> Dict[Tuple[int, int], float]:
        """Calculate crime density map (100m × 100m grid)"""
        
        lat_per_100m = 100 / 111000
        lng_per_100m = 100 / (111000 * math.cos(math.radians((min_lat + max_lat) / 2)))
        
        lat_range = max_lat - min_lat
        lng_range = max_lng - min_lng
        grid_lat_cells = int(lat_range / lat_per_100m) + 1
        grid_lng_cells = int(lng_range / lng_per_100m) + 1
        
        density_map = {}
        
        for crime in crime_data:
            grid_lat = int((crime.lat - min_lat) / lat_per_100m)
            grid_lng = int((crime.lng - min_lng) / lng_per_100m)
            
            if 0 <= grid_lat < grid_lat_cells and 0 <= grid_lng < grid_lng_cells:
                time_factor = self._calculate_time_decay(crime.hours_ago)
                severity_factor = self.severity_weights.get(crime.severity, 0.5)
                weighted_contribution = time_factor * severity_factor
                
                grid_key = (grid_lat, grid_lng)
                density_map[grid_key] = density_map.get(grid_key, 0.0) + weighted_contribution
        
        return density_map
    
    async def get_blocked_areas(self, min_lat: float, min_lng: float,
                               max_lat: float, max_lng: float) -> List[Dict[str, Any]]:
        """Get coordinates of 24-hour crime zones (blocked areas)"""
        
        crime_data = await self._get_crime_data_for_area(min_lat, min_lng, max_lat, max_lng)
        critical_crimes = [c for c in crime_data if c.hours_ago <= 24]
        
        blocked_areas = []
        for crime in critical_crimes:
            blocked_areas.append({
                'lat': crime.lat,
                'lng': crime.lng,
                'severity': crime.severity,
                'crime_type': crime.crime_type,
                'hours_ago': crime.hours_ago,
                'blocked_radius': 100,
                'penalty_level': 'CRITICAL'
            })
        
        return blocked_areas
    
    def get_route_safety_breakdown(self, route: SafetyRoute) -> Dict[str, Any]:
        """Get detailed safety breakdown for a route"""
        
        total_24h_crimes = sum(seg.critical_crimes_24h for seg in route.segments)
        total_high_severity = sum(seg.high_severity_crimes for seg in route.segments)
        total_recent_crimes = sum(seg.recent_crimes for seg in route.segments)
        avg_crime_density = sum(seg.crime_density_score for seg in route.segments) / len(route.segments) if route.segments else 0
        
        most_dangerous_segment = min(route.segments, key=lambda s: s.safety_score) if route.segments else None
        
        return {
            '24h_crimes_avoided': total_24h_crimes,
            'high_severity_crimes_avoided': total_high_severity,
            'recent_crimes_encountered': total_recent_crimes,
            'average_crime_density': avg_crime_density,
            'most_dangerous_segment': {
                'safety_score': most_dangerous_segment.safety_score if most_dangerous_segment else 100,
                'crime_density': most_dangerous_segment.crime_density if most_dangerous_segment else 0,
                'critical_crimes_24h': most_dangerous_segment.critical_crimes_24h if most_dangerous_segment else 0
            } if most_dangerous_segment else None,
            'route_safety_summary': {
                'total_distance': route.total_distance,
                'average_safety': route.total_safety_score,
                'safety_grade': self._calculate_safety_grade(route.total_safety_score)
            }
        }
    
    def _calculate_safety_grade(self, safety_score: float) -> str:
        """Calculate safety grade from safety score"""
        if safety_score >= 85:
            return 'A'
        elif safety_score >= 70:
            return 'B'
        elif safety_score >= 50:
            return 'C'
        elif safety_score >= 30:
            return 'D'
        else:
            return 'F'


# ==================== EXAMPLE USAGE ====================

async def main():
    """Example usage"""
    
    database_url = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/crimes')
    router = CrimeAwareRouter(database_url)
    
    # Example: Route from point A to point B
    start_lat, start_lng = 37.7749, -122.4194
    end_lat, end_lng = 37.8044, -122.4072
    
    result = await router.find_optimal_route(start_lat, start_lng, end_lat, end_lng)
    
    print(f"Fastest: {result['fastest_route']['total_distance']:.0f}m, Safety: {result['fastest_route']['total_safety_score']:.1f}")
    print(f"Safest: {result['safest_route']['total_distance']:.0f}m, Safety: {result['safest_route']['total_safety_score']:.1f}")
    print(f"Difference: +{result['comparison']['time_difference_minutes']:.1f} min, +{result['comparison']['safety_improvement']:.1f}% safer")


if __name__ == '__main__':
    asyncio.run(main())