#!/usr/bin/env python3
"""
Enhanced Safe Router with Dijkstra's Algorithm and Crime Obstacles
Implements modified Dijkstra's algorithm that avoids recent crime locations
"""

import math
import heapq
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_sqlite import db_manager
from sqlalchemy import text

@dataclass
class GraphNode:
    """Node in the routing graph"""
    lat: float
    lng: float
    node_id: str
    is_obstacle: bool = False
    obstacle_radius: float = 0.0  # meters
    obstacle_severity: float = 0.0  # 0-1, how dangerous this obstacle is

@dataclass
class Edge:
    """Edge between two nodes"""
    from_node: str
    to_node: str
    distance: float  # meters
    base_cost: float  # base routing cost
    safety_cost: float  # additional cost due to safety concerns
    total_cost: float  # combined cost

@dataclass
class RouteResult:
    """Result of route calculation"""
    path: List[Tuple[float, float]]  # List of (lat, lng) coordinates
    total_distance: float  # meters
    total_cost: float
    avoided_obstacles: int  # Number of obstacles avoided
    safety_score: float  # 0-100
    route_type: str

class ObstacleRouter:
    """Router that uses Dijkstra's algorithm with crime obstacles"""
    
    def __init__(self):
        self.db_manager = db_manager
        self.obstacle_radius = 100  # meters - radius around crime locations to avoid
        self.recent_hours = 24  # hours - crimes within this time are obstacles
        self.graph_nodes: Dict[str, GraphNode] = {}
        self.graph_edges: Dict[str, List[Edge]] = {}
        
    def get_recent_crime_obstacles(self, bounds: Dict[str, float]) -> List[GraphNode]:
        """Get recent crime locations as obstacles"""
        try:
            with self.db_manager.engine.connect() as conn:
                # Get crimes from last 24 hours within bounds
                recent_time = datetime.utcnow() - timedelta(hours=self.recent_hours)
                
                query = text("""
                    SELECT lat, lng, severity, crime_type, occurred_at
                    FROM crimes 
                    WHERE occurred_at >= :recent_time
                    AND lat BETWEEN :min_lat AND :max_lat
                    AND lng BETWEEN :min_lng AND :max_lng
                    AND lat IS NOT NULL AND lng IS NOT NULL
                """)
                
                result = conn.execute(query, {
                    'recent_time': recent_time,
                    'min_lat': bounds['min_lat'],
                    'max_lat': bounds['max_lat'],
                    'min_lng': bounds['min_lng'],
                    'max_lng': bounds['max_lng']
                })
                
                obstacles = []
                for row in result:
                    lat, lng, severity, crime_type, occurred_at = row
                    
                    # Calculate obstacle severity (0-1)
                    severity_factor = min(severity / 10.0, 1.0)
                    
                    # Time decay factor (more recent = more dangerous)
                    hours_ago = (datetime.utcnow() - occurred_at).total_seconds() / 3600
                    time_factor = max(0, 1.0 - (hours_ago / self.recent_hours))
                    
                    obstacle_severity = severity_factor * time_factor
                    
                    node_id = f"obstacle_{lat}_{lng}"
                    obstacle = GraphNode(
                        lat=lat,
                        lng=lng,
                        node_id=node_id,
                        is_obstacle=True,
                        obstacle_radius=self.obstacle_radius,
                        obstacle_severity=obstacle_severity
                    )
                    obstacles.append(obstacle)
                
                print(f"Found {len(obstacles)} recent crime obstacles")
                return obstacles
                
        except Exception as e:
            print(f"Error getting crime obstacles: {e}")
            return []
    
    def build_routing_graph(self, start_lat: float, start_lng: float, 
                           end_lat: float, end_lng: float, 
                           grid_resolution: float = 0.001) -> None:
        """Build a routing graph with obstacles"""
        
        # Calculate bounds with padding
        padding = 0.01  # ~1km padding
        bounds = {
            'min_lat': min(start_lat, end_lat) - padding,
            'max_lat': max(start_lat, end_lat) + padding,
            'min_lng': min(start_lng, end_lng) - padding,
            'max_lng': max(start_lng, end_lng) + padding
        }
        
        # Get crime obstacles
        obstacles = self.get_recent_crime_obstacles(bounds)
        
        # Create grid nodes
        self.graph_nodes = {}
        self.graph_edges = {}
        
        # Generate grid points
        lat_step = grid_resolution
        lng_step = grid_resolution
        
        current_lat = bounds['min_lat']
        while current_lat <= bounds['max_lat']:
            current_lng = bounds['min_lng']
            while current_lng <= bounds['max_lng']:
                node_id = f"grid_{current_lat}_{current_lng}"
                
                # Check if this point is near an obstacle
                is_obstacle = False
                obstacle_severity = 0.0
                
                for obstacle in obstacles:
                    distance = self._calculate_distance(
                        current_lat, current_lng, 
                        obstacle.lat, obstacle.lng
                    )
                    
                    if distance <= obstacle.obstacle_radius:
                        is_obstacle = True
                        obstacle_severity = max(obstacle_severity, obstacle.obstacle_severity)
                
                node = GraphNode(
                    lat=current_lat,
                    lng=current_lng,
                    node_id=node_id,
                    is_obstacle=is_obstacle,
                    obstacle_radius=0,
                    obstacle_severity=obstacle_severity
                )
                
                self.graph_nodes[node_id] = node
                current_lng += lng_step
            current_lat += lat_step
        
        # Create edges between adjacent nodes
        self._create_graph_edges()
        
        print(f"Built routing graph with {len(self.graph_nodes)} nodes and {sum(len(edges) for edges in self.graph_edges.values())} edges")
    
    def _create_graph_edges(self):
        """Create edges between adjacent nodes in the grid"""
        for node_id, node in self.graph_nodes.items():
            self.graph_edges[node_id] = []
            
            # Check all other nodes for adjacency
            for other_id, other_node in self.graph_nodes.items():
                if node_id == other_id:
                    continue
                
                distance = self._calculate_distance(
                    node.lat, node.lng, other_node.lat, other_node.lng
                )
                
                # Only connect to nearby nodes (within reasonable distance)
                if distance <= 200:  # 200 meters max edge length
                    # Calculate costs
                    base_cost = distance
                    safety_cost = 0
                    
                    # Add safety cost if either node is near an obstacle
                    if node.is_obstacle or other_node.is_obstacle:
                        max_severity = max(node.obstacle_severity, other_node.obstacle_severity)
                        safety_cost = distance * max_severity * 10  # 10x cost for obstacles
                    
                    total_cost = base_cost + safety_cost
                    
                    edge = Edge(
                        from_node=node_id,
                        to_node=other_id,
                        distance=distance,
                        base_cost=base_cost,
                        safety_cost=safety_cost,
                        total_cost=total_cost
                    )
                    
                    self.graph_edges[node_id].append(edge)
    
    def find_route_with_obstacles(self, start_lat: float, start_lng: float,
                               end_lat: float, end_lng: float) -> RouteResult:
        """Find route using Dijkstra's algorithm with obstacles"""
        
        # Build the routing graph
        self.build_routing_graph(start_lat, start_lng, end_lat, end_lng)
        
        # Find closest nodes to start and end points
        start_node_id = self._find_closest_node(start_lat, start_lng)
        end_node_id = self._find_closest_node(end_lat, end_lng)
        
        if not start_node_id or not end_node_id:
            raise ValueError("Could not find start or end nodes in graph")
        
        # Run Dijkstra's algorithm
        path, total_cost, avoided_obstacles = self._dijkstra(start_node_id, end_node_id)
        
        # Convert path to coordinates
        route_coords = []
        for node_id in path:
            node = self.graph_nodes[node_id]
            route_coords.append((node.lat, node.lng))
        
        # Calculate total distance
        total_distance = 0
        for i in range(len(route_coords) - 1):
            total_distance += self._calculate_distance(
                route_coords[i][0], route_coords[i][1],
                route_coords[i+1][0], route_coords[i+1][1]
            )
        
        # Calculate safety score
        safety_score = self._calculate_route_safety_score(route_coords)
        
        return RouteResult(
            path=route_coords,
            total_distance=total_distance,
            total_cost=total_cost,
            avoided_obstacles=avoided_obstacles,
            safety_score=safety_score,
            route_type="obstacle_avoiding"
        )
    
    def _dijkstra(self, start_node_id: str, end_node_id: str) -> Tuple[List[str], float, int]:
        """Dijkstra's algorithm implementation"""
        
        # Initialize distances and previous nodes
        distances = {node_id: float('inf') for node_id in self.graph_nodes}
        previous = {node_id: None for node_id in self.graph_nodes}
        distances[start_node_id] = 0
        
        # Priority queue: (distance, node_id)
        pq = [(0, start_node_id)]
        visited = set()
        avoided_obstacles = 0
        
        while pq:
            current_distance, current_node = heapq.heappop(pq)
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            # Count obstacles avoided
            if self.graph_nodes[current_node].is_obstacle:
                avoided_obstacles += 1
            
            # If we reached the end, reconstruct path
            if current_node == end_node_id:
                path = []
                node = end_node_id
                while node is not None:
                    path.append(node)
                    node = previous[node]
                path.reverse()
                return path, current_distance, avoided_obstacles
            
            # Check all neighbors
            for edge in self.graph_edges.get(current_node, []):
                neighbor = edge.to_node
                if neighbor in visited:
                    continue
                
                new_distance = current_distance + edge.total_cost
                
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current_node
                    heapq.heappush(pq, (new_distance, neighbor))
        
        # No path found
        return [], float('inf'), 0
    
    def _find_closest_node(self, lat: float, lng: float) -> Optional[str]:
        """Find the closest node to given coordinates"""
        closest_node = None
        closest_distance = float('inf')
        
        for node_id, node in self.graph_nodes.items():
            distance = self._calculate_distance(lat, lng, node.lat, node.lng)
            if distance < closest_distance:
                closest_distance = distance
                closest_node = node_id
        
        return closest_node
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in meters"""
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
    
    def _calculate_route_safety_score(self, route_coords: List[Tuple[float, float]]) -> float:
        """Calculate overall safety score for the route"""
        if not route_coords:
            return 0
        
        total_safety = 0
        for lat, lng in route_coords:
            # Simple safety calculation based on distance from obstacles
            min_obstacle_distance = float('inf')
            for node in self.graph_nodes.values():
                if node.is_obstacle:
                    distance = self._calculate_distance(lat, lng, node.lat, node.lng)
                    min_obstacle_distance = min(min_obstacle_distance, distance)
            
            # Safety score based on distance from nearest obstacle
            if min_obstacle_distance == float('inf'):
                safety = 100  # No obstacles nearby
            else:
                safety = max(0, 100 - (100 / (min_obstacle_distance / 50)))  # Decay over 50m
            
            total_safety += safety
        
        return total_safety / len(route_coords)

# API wrapper for the obstacle router
class ObstacleRouterAPI:
    """API wrapper for the obstacle router"""
    
    def __init__(self):
        self.router = ObstacleRouter()
    
    def get_route(self, start_lat: float, start_lng: float, 
                  end_lat: float, end_lng: float) -> Dict:
        """Get route avoiding recent crime obstacles"""
        try:
            result = self.router.find_route_with_obstacles(
                start_lat, start_lng, end_lat, end_lng
            )
            
            return {
                "route_type": "obstacle_avoiding",
                "total_distance_km": result.total_distance / 1000,
                "total_cost": result.total_cost,
                "avoided_obstacles": result.avoided_obstacles,
                "safety_score": result.safety_score,
                "points": [
                    {"lat": lat, "lng": lng} 
                    for lat, lng in result.path
                ],
                "success": True
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }

if __name__ == "__main__":
    # Test the obstacle router
    router_api = ObstacleRouterAPI()
    
    # Test route from SF to nearby location
    result = router_api.get_route(
        37.7749, -122.4194,  # San Francisco
        37.7849, -122.4094   # Nearby location
    )
    
    print("Route result:", result)
