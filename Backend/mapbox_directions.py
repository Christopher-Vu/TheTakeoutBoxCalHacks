#!/usr/bin/env python3
"""
Mapbox Directions API Client
Fetches real street routes from Mapbox Directions API
"""

import aiohttp
import asyncio
from typing import Dict, List, Tuple, Optional
import polyline
import os


class MapboxDirectionsClient:
    """Client for Mapbox Directions API to get real street routes"""
    
    def __init__(self, access_token: str):
        """
        Initialize Mapbox Directions client
        
        Args:
            access_token: Mapbox API access token
        """
        self.access_token = access_token
        self.base_url = "https://api.mapbox.com/directions/v5/mapbox"
        
    async def get_route(
        self, 
        start_lat: float, 
        start_lng: float, 
        end_lat: float, 
        end_lng: float, 
        mode: str = 'walking',
        alternatives: bool = False
    ) -> Dict:
        """
        Get route from Mapbox Directions API
        
        Args:
            start_lat: Starting latitude
            start_lng: Starting longitude
            end_lat: Ending latitude
            end_lng: Ending longitude
            mode: Travel mode ('walking', 'cycling', 'driving')
            alternatives: Whether to request alternative routes
            
        Returns:
            Dict containing:
                - coordinates: List of (lat, lng) tuples along the route
                - distance: Total distance in meters
                - duration: Total duration in seconds
                - steps: List of turn-by-turn instructions
        """
        # Mapbox uses lng,lat order (not lat,lng)
        coordinates = f"{start_lng},{start_lat};{end_lng},{end_lat}"
        
        # Map mode to Mapbox profile
        profile_map = {
            'walking': 'walking',
            'cycling': 'cycling',
            'biking': 'cycling',
            'driving': 'driving'
        }
        profile = profile_map.get(mode, 'walking')
        
        # Build API URL
        url = f"{self.base_url}/{profile}/{coordinates}"
        
        # API parameters
        params = {
            'access_token': self.access_token,
            'geometries': 'geojson',  # Get GeoJSON format
            'overview': 'full',  # Full geometry
            'steps': 'true',  # Turn-by-turn instructions
            'alternatives': 'true' if alternatives else 'false'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Mapbox API error {response.status}: {error_text}")
                    
                    data = await response.json()
                    
                    if 'routes' not in data or len(data['routes']) == 0:
                        raise Exception("No routes found")
                    
                    # Parse the first route
                    route = data['routes'][0]
                    
                    # Extract coordinates from GeoJSON geometry
                    geometry = route['geometry']
                    coordinates_list = geometry['coordinates']  # List of [lng, lat] pairs
                    
                    # Convert to (lat, lng) tuples
                    route_coordinates = [(coord[1], coord[0]) for coord in coordinates_list]
                    
                    # Extract distance and duration
                    distance = route['distance']  # meters
                    duration = route['duration']  # seconds
                    
                    # Extract steps if available
                    steps = []
                    if 'legs' in route and len(route['legs']) > 0:
                        for leg in route['legs']:
                            if 'steps' in leg:
                                for step in leg['steps']:
                                    steps.append({
                                        'instruction': step.get('maneuver', {}).get('instruction', ''),
                                        'distance': step.get('distance', 0),
                                        'duration': step.get('duration', 0)
                                    })
                    
                    return {
                        'coordinates': route_coordinates,
                        'distance': distance,
                        'duration': duration,
                        'steps': steps,
                        'mode': mode
                    }
                    
        except aiohttp.ClientError as e:
            raise Exception(f"Network error calling Mapbox API: {e}")
        except asyncio.TimeoutError:
            raise Exception("Mapbox API request timed out")
        except Exception as e:
            raise Exception(f"Error getting route from Mapbox: {e}")
    
    async def get_multiple_routes(
        self,
        start_lat: float,
        start_lng: float,
        end_lat: float,
        end_lng: float,
        mode: str = 'walking'
    ) -> List[Dict]:
        """
        Get multiple alternative routes from Mapbox
        
        Args:
            start_lat: Starting latitude
            start_lng: Starting longitude
            end_lat: Ending latitude
            end_lng: Ending longitude
            mode: Travel mode
            
        Returns:
            List of route dictionaries
        """
        # Mapbox uses lng,lat order
        coordinates = f"{start_lng},{start_lat};{end_lng},{end_lat}"
        
        profile_map = {
            'walking': 'walking',
            'cycling': 'cycling',
            'biking': 'cycling',
            'driving': 'driving'
        }
        profile = profile_map.get(mode, 'walking')
        
        url = f"{self.base_url}/{profile}/{coordinates}"
        
        params = {
            'access_token': self.access_token,
            'geometries': 'geojson',
            'overview': 'full',
            'steps': 'true',
            'alternatives': 'true',
            'max_alternatives': 3  # Request up to 3 alternatives
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Mapbox API error {response.status}: {error_text}")
                    
                    data = await response.json()
                    
                    if 'routes' not in data or len(data['routes']) == 0:
                        raise Exception("No routes found")
                    
                    # Parse all routes
                    routes = []
                    for route in data['routes']:
                        geometry = route['geometry']
                        coordinates_list = geometry['coordinates']
                        route_coordinates = [(coord[1], coord[0]) for coord in coordinates_list]
                        
                        routes.append({
                            'coordinates': route_coordinates,
                            'distance': route['distance'],
                            'duration': route['duration'],
                            'mode': mode
                        })
                    
                    return routes
                    
        except Exception as e:
            raise Exception(f"Error getting multiple routes from Mapbox: {e}")


# Helper function to create client from environment
def create_mapbox_client() -> Optional[MapboxDirectionsClient]:
    """Create Mapbox client from environment variable"""
    access_token = os.getenv('MAPBOX_ACCESS_TOKEN')
    if not access_token:
        print("Warning: MAPBOX_ACCESS_TOKEN not found in environment")
        return None
    return MapboxDirectionsClient(access_token)

