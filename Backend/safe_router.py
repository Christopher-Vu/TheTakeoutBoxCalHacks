#!/usr/bin/env python3
"""
Safe Router - Optimizes routes based on distance vs safety
"""

import math
import heapq
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from safety_analyzer import SafetyAnalyzer, SafetyScore

@dataclass
class RoutePoint:
    """Point along a route"""
    lat: float
    lng: float
    safety_score: float
    distance_from_start: float
    cumulative_safety_penalty: float

@dataclass
class Route:
    """Complete route with safety and distance metrics"""
    points: List[RoutePoint]
    total_distance: float
    average_safety: float
    safety_penalty: float
    route_score: float  # Combined score (higher = better)
    route_type: str  # 'safest', 'balanced', 'fastest'

class SafeRouter:
    """Router that optimizes for safety vs distance"""
    
    def __init__(self, safety_analyzer: SafetyAnalyzer):
        self.safety_analyzer = safety_analyzer
        self.safety_weight = 0.6  # Weight for safety in optimization
        self.distance_weight = 0.4  # Weight for distance in optimization
        
    def find_safe_route(self, start_lat: float, start_lng: float, 
                        end_lat: float, end_lng: float,
                        route_type: str = 'balanced') -> Route:
        """Find the optimal route considering safety and distance"""
        
        if route_type == 'safest':
            return self._find_safest_route(start_lat, start_lng, end_lat, end_lng)
        elif route_type == 'fastest':
            return self._find_fastest_route(start_lat, start_lng, end_lat, end_lng)
        else:  # balanced
            return self._find_balanced_route(start_lat, start_lng, end_lat, end_lng)
    
    def _find_safest_route(self, start_lat: float, start_lng: float, 
                          end_lat: float, end_lng: float) -> Route:
        """Find the safest route (prioritizes safety over distance)"""
        # Generate waypoints along the direct route
        waypoints = self._generate_waypoints(start_lat, start_lng, end_lat, end_lng, num_points=20)
        
        # Analyze safety for each waypoint
        route_points = []
        total_distance = 0
        cumulative_safety_penalty = 0
        
        for i, (lat, lng) in enumerate(waypoints):
            safety_score = self.safety_analyzer.analyze_point_safety(lat, lng)
            
            # Calculate distance from start
            if i == 0:
                distance_from_start = 0
            else:
                distance_from_start = self._calculate_distance(
                    start_lat, start_lng, lat, lng
                )
            
            # Safety penalty (lower safety = higher penalty)
            safety_penalty = (100 - safety_score.safety_percentage) / 100.0
            cumulative_safety_penalty += safety_penalty
            
            route_point = RoutePoint(
                lat=lat,
                lng=lng,
                safety_score=safety_score.safety_percentage,
                distance_from_start=distance_from_start,
                cumulative_safety_penalty=cumulative_safety_penalty
            )
            route_points.append(route_point)
        
        # Calculate total distance
        total_distance = self._calculate_distance(start_lat, start_lng, end_lat, end_lng)
        
        # Calculate average safety
        average_safety = sum(point.safety_score for point in route_points) / len(route_points)
        
        # Calculate route score (higher = better)
        route_score = self._calculate_route_score(total_distance, average_safety, route_type='safest')
        
        return Route(
            points=route_points,
            total_distance=total_distance,
            average_safety=average_safety,
            safety_penalty=cumulative_safety_penalty,
            route_score=route_score,
            route_type='safest'
        )
    
    def _find_fastest_route(self, start_lat: float, start_lng: float, 
                           end_lat: float, end_lng: float) -> Route:
        """Find the fastest route (prioritizes distance over safety)"""
        # Direct route (shortest distance)
        waypoints = self._generate_waypoints(start_lat, start_lng, end_lat, end_lng, num_points=10)
        
        route_points = []
        total_distance = 0
        cumulative_safety_penalty = 0
        
        for i, (lat, lng) in enumerate(waypoints):
            safety_score = self.safety_analyzer.analyze_point_safety(lat, lng)
            
            if i == 0:
                distance_from_start = 0
            else:
                distance_from_start = self._calculate_distance(start_lat, start_lng, lat, lng)
            
            safety_penalty = (100 - safety_score.safety_percentage) / 100.0
            cumulative_safety_penalty += safety_penalty
            
            route_point = RoutePoint(
                lat=lat,
                lng=lng,
                safety_score=safety_score.safety_percentage,
                distance_from_start=distance_from_start,
                cumulative_safety_penalty=cumulative_safety_penalty
            )
            route_points.append(route_point)
        
        total_distance = self._calculate_distance(start_lat, start_lng, end_lat, end_lng)
        average_safety = sum(point.safety_score for point in route_points) / len(route_points)
        route_score = self._calculate_route_score(total_distance, average_safety, route_type='fastest')
        
        return Route(
            points=route_points,
            total_distance=total_distance,
            average_safety=average_safety,
            safety_penalty=cumulative_safety_penalty,
            route_score=route_score,
            route_type='fastest'
        )
    
    def _find_balanced_route(self, start_lat: float, start_lng: float, 
                           end_lat: float, end_lng: float) -> Route:
        """Find a balanced route (considers both safety and distance)"""
        # Generate multiple route options
        route_options = []
        
        # Option 1: Direct route
        direct_route = self._find_fastest_route(start_lat, start_lng, end_lat, end_lng)
        route_options.append(direct_route)
        
        # Option 2: Slightly detoured route (try to avoid high-crime areas)
        detoured_route = self._find_detoured_route(start_lat, start_lng, end_lat, end_lng)
        route_options.append(detoured_route)
        
        # Option 3: Safety-optimized route
        safety_route = self._find_safest_route(start_lat, start_lng, end_lat, end_lng)
        route_options.append(safety_route)
        
        # Choose the best balanced route
        best_route = max(route_options, key=lambda r: r.route_score)
        best_route.route_type = 'balanced'
        
        return best_route
    
    def _find_detoured_route(self, start_lat: float, start_lng: float, 
                            end_lat: float, end_lng: float) -> Route:
        """Find a detoured route that avoids high-crime areas"""
        # Create waypoints that avoid the most dangerous areas
        waypoints = self._generate_safe_waypoints(start_lat, start_lng, end_lat, end_lng)
        
        route_points = []
        total_distance = 0
        cumulative_safety_penalty = 0
        
        for i, (lat, lng) in enumerate(waypoints):
            safety_score = self.safety_analyzer.analyze_point_safety(lat, lng)
            
            if i == 0:
                distance_from_start = 0
            else:
                distance_from_start = self._calculate_distance(start_lat, start_lng, lat, lng)
            
            safety_penalty = (100 - safety_score.safety_percentage) / 100.0
            cumulative_safety_penalty += safety_penalty
            
            route_point = RoutePoint(
                lat=lat,
                lng=lng,
                safety_score=safety_score.safety_percentage,
                distance_from_start=distance_from_start,
                cumulative_safety_penalty=cumulative_safety_penalty
            )
            route_points.append(route_point)
        
        # Calculate total distance (sum of segments)
        total_distance = 0
        for i in range(1, len(route_points)):
            total_distance += self._calculate_distance(
                route_points[i-1].lat, route_points[i-1].lng,
                route_points[i].lat, route_points[i].lng
            )
        
        average_safety = sum(point.safety_score for point in route_points) / len(route_points)
        route_score = self._calculate_route_score(total_distance, average_safety, route_type='balanced')
        
        return Route(
            points=route_points,
            total_distance=total_distance,
            average_safety=average_safety,
            safety_penalty=cumulative_safety_penalty,
            route_score=route_score,
            route_type='detoured'
        )
    
    def _generate_waypoints(self, start_lat: float, start_lng: float, 
                           end_lat: float, end_lng: float, num_points: int = 10) -> List[Tuple[float, float]]:
        """Generate waypoints along a direct route"""
        waypoints = []
        
        for i in range(num_points):
            t = i / (num_points - 1)  # Interpolation parameter
            lat = start_lat + (end_lat - start_lat) * t
            lng = start_lng + (end_lng - start_lng) * t
            waypoints.append((lat, lng))
        
        return waypoints
    
    def _generate_safe_waypoints(self, start_lat: float, start_lng: float, 
                               end_lat: float, end_lng: float) -> List[Tuple[float, float]]:
        """Generate waypoints that avoid high-crime areas"""
        # Start with direct route
        direct_waypoints = self._generate_waypoints(start_lat, start_lng, end_lat, end_lng, num_points=15)
        
        # Adjust waypoints to avoid high-crime areas
        safe_waypoints = []
        
        for i, (lat, lng) in enumerate(direct_waypoints):
            safety_score = self.safety_analyzer.analyze_point_safety(lat, lng)
            
            # If safety is low, try to find a nearby safer point
            if safety_score.safety_percentage < 50:
                safer_point = self._find_safer_nearby_point(lat, lng)
                safe_waypoints.append(safer_point)
            else:
                safe_waypoints.append((lat, lng))
        
        return safe_waypoints
    
    def _find_safer_nearby_point(self, lat: float, lng: float, 
                               search_radius: float = 0.1) -> Tuple[float, float]:
        """Find a safer point near the given coordinates"""
        # Search in a small grid around the point
        best_lat, best_lng = lat, lng
        best_safety = 0
        
        # Search grid
        for offset_lat in [-search_radius, 0, search_radius]:
            for offset_lng in [-search_radius, 0, search_radius]:
                test_lat = lat + offset_lat
                test_lng = lng + offset_lng
                
                safety_score = self.safety_analyzer.analyze_point_safety(test_lat, test_lng)
                
                if safety_score.safety_percentage > best_safety:
                    best_safety = safety_score.safety_percentage
                    best_lat, best_lng = test_lat, test_lng
        
        return (best_lat, best_lng)
    
    def _calculate_route_score(self, total_distance: float, average_safety: float, 
                              route_type: str) -> float:
        """Calculate overall route score"""
        if route_type == 'safest':
            # Prioritize safety
            safety_score = average_safety / 100.0
            distance_penalty = min(0.3, total_distance / 50.0)  # Penalty for long routes
            return safety_score - distance_penalty
            
        elif route_type == 'fastest':
            # Prioritize distance
            distance_score = max(0, 1.0 - (total_distance / 20.0))  # Penalty for long routes
            safety_bonus = (average_safety - 50) / 100.0  # Bonus for good safety
            return distance_score + safety_bonus
            
        else:  # balanced
            # Balance safety and distance
            safety_score = (average_safety / 100.0) * self.safety_weight
            distance_score = (1.0 - min(1.0, total_distance / 30.0)) * self.distance_weight
            return safety_score + distance_score
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in km"""
        R = 6371  # Earth's radius in km
        
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlng/2) * math.sin(dlng/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance

class SafeRouterAPI:
    """API wrapper for safe routing"""
    
    def __init__(self):
        self.safety_analyzer = SafetyAnalyzer()
        self.router = SafeRouter(self.safety_analyzer)
    
    def get_route(self, start_lat: float, start_lng: float, 
                  end_lat: float, end_lng: float, 
                  route_type: str = 'balanced') -> Dict:
        """Get a safe route between two points"""
        route = self.router.find_safe_route(start_lat, start_lng, end_lat, end_lng, route_type)
        
        return {
            'route_type': route.route_type,
            'total_distance_km': round(route.total_distance, 2),
            'average_safety_percentage': round(route.average_safety, 1),
            'safety_penalty': round(route.safety_penalty, 2),
            'route_score': round(route.route_score, 3),
            'points': [
                {
                    'lat': point.lat,
                    'lng': point.lng,
                    'safety_score': round(point.safety_score, 1),
                    'distance_from_start_km': round(point.distance_from_start, 2),
                    'cumulative_safety_penalty': round(point.cumulative_safety_penalty, 2)
                }
                for point in route.points
            ]
        }
    
    def compare_routes(self, start_lat: float, start_lng: float, 
                      end_lat: float, end_lng: float) -> Dict:
        """Compare different route options"""
        routes = {}
        
        for route_type in ['safest', 'balanced', 'fastest']:
            route = self.router.find_safe_route(start_lat, start_lng, end_lat, end_lng, route_type)
            routes[route_type] = {
                'total_distance_km': round(route.total_distance, 2),
                'average_safety_percentage': round(route.average_safety, 1),
                'route_score': round(route.route_score, 3),
                'num_points': len(route.points)
            }
        
        return routes

# Test the safe router
if __name__ == "__main__":
    router_api = SafeRouterAPI()
    
    # Test route in San Francisco
    start_lat, start_lng = 37.7749, -122.4194  # Union Square
    end_lat, end_lng = 37.7849, -122.4094  # Nearby point
    
    print("Testing Safe Router")
    print("=" * 40)
    
    # Test balanced route
    route = router_api.get_route(start_lat, start_lng, end_lat, end_lng, 'balanced')
    
    print(f"Route Type: {route['route_type']}")
    print(f"Total Distance: {route['total_distance_km']} km")
    print(f"Average Safety: {route['average_safety_percentage']}%")
    print(f"Route Score: {route['route_score']}")
    print(f"Number of Points: {len(route['points'])}")
    
    # Compare all route types
    print("\nComparing Route Options:")
    comparison = router_api.compare_routes(start_lat, start_lng, end_lat, end_lng)
    
    for route_type, metrics in comparison.items():
        print(f"{route_type.capitalize()}: {metrics['total_distance_km']}km, "
              f"{metrics['average_safety_percentage']}% safety, "
              f"score: {metrics['route_score']}")
