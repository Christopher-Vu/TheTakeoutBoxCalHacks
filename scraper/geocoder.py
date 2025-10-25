"""
Enhanced geocoding service for multi-source crime data
Handles various address formats and provides fallback options
"""

import requests
import time
import logging
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class GeocodingResult:
    lat: float
    lng: float
    confidence: float
    source: str
    formatted_address: str
    raw_response: Dict

class GeocodingService:
    """Multi-provider geocoding service with fallbacks"""
    
    def __init__(self):
        self.providers = [
            self._geocode_google,
            self._geocode_nominatim,
            self._geocode_berkeley_specific
        ]
        self.cache = {}  # Simple in-memory cache
        
    def geocode(self, address: str, use_cache: bool = True) -> Optional[GeocodingResult]:
        """Geocode an address using multiple providers with fallback"""
        
        # Check cache first
        if use_cache and address in self.cache:
            return self.cache[address]
        
        # Clean and standardize address
        cleaned_address = self._clean_address(address)
        
        # Try each provider in order
        for provider in self.providers:
            try:
                result = provider(cleaned_address)
                if result and result.confidence > 0.5:
                    if use_cache:
                        self.cache[address] = result
                    return result
            except Exception as e:
                logger.warning(f"Geocoding failed with {provider.__name__}: {e}")
                continue
        
        logger.error(f"All geocoding providers failed for address: {address}")
        return None
    
    def _clean_address(self, address: str) -> str:
        """Clean and standardize address format"""
        if not address:
            return ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', address.strip())
        
        # Add Berkeley, CA if not present
        if 'berkeley' not in cleaned.lower() and 'ca' not in cleaned.lower():
            cleaned += ', Berkeley, CA'
        
        # Standardize common abbreviations
        cleaned = re.sub(r'\bST\b', 'Street', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bAVE\b', 'Avenue', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bBLVD\b', 'Boulevard', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\bDR\b', 'Drive', cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    def _geocode_google(self, address: str) -> Optional[GeocodingResult]:
        """Geocode using Google Maps API"""
        # Note: Requires Google Maps API key
        api_key = "YOUR_GOOGLE_MAPS_API_KEY"  # Set in environment
        
        if not api_key or api_key == "YOUR_GOOGLE_MAPS_API_KEY":
            return None
            
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'key': api_key,
            'region': 'us-ca'  # Bias towards California
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            result = data['results'][0]
            location = result['geometry']['location']
            
            return GeocodingResult(
                lat=location['lat'],
                lng=location['lng'],
                confidence=result['geometry'].get('location_type', 'ROOFTOP') == 'ROOFTOP',
                source='google',
                formatted_address=result['formatted_address'],
                raw_response=data
            )
        
        return None
    
    def _geocode_nominatim(self, address: str) -> Optional[GeocodingResult]:
        """Geocode using OpenStreetMap Nominatim (free)"""
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'us',
            'state': 'California',
            'city': 'Berkeley'
        }
        
        # Be respectful with rate limiting
        time.sleep(1)
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data:
            result = data[0]
            return GeocodingResult(
                lat=float(result['lat']),
                lng=float(result['lon']),
                confidence=float(result.get('importance', 0.5)),
                source='nominatim',
                formatted_address=result['display_name'],
                raw_response=data
            )
        
        return None
    
    def _geocode_berkeley_specific(self, address: str) -> Optional[GeocodingResult]:
        """Berkeley-specific geocoding using known locations"""
        # Known Berkeley locations for common addresses
        berkeley_locations = {
            'uc berkeley': (37.8719, -122.2585),
            'berkeley campus': (37.8719, -122.2585),
            'sproul plaza': (37.8719, -122.2585),
            'downtown berkeley': (37.8703, -122.2705),
            'telegraph avenue': (37.8690, -122.2588),
            'durant avenue': (37.8719, -122.2585),
            'bancroft way': (37.8719, -122.2585),
            'shattuck avenue': (37.8703, -122.2705),
            'college avenue': (37.8690, -122.2588),
            'oxford street': (37.8703, -122.2705),
            'martin luther king jr way': (37.8703, -122.2705),
            'san pablo avenue': (37.8690, -122.2588)
        }
        
        address_lower = address.lower()
        for location, coords in berkeley_locations.items():
            if location in address_lower:
                return GeocodingResult(
                    lat=coords[0],
                    lng=coords[1],
                    confidence=0.8,
                    source='berkeley_locations',
                    formatted_address=address,
                    raw_response={'berkeley_location': location}
                )
        
        return None
    
    def batch_geocode(self, addresses: List[str]) -> List[Optional[GeocodingResult]]:
        """Geocode multiple addresses with rate limiting"""
        results = []
        
        for i, address in enumerate(addresses):
            result = self.geocode(address)
            results.append(result)
            
            # Rate limiting for free APIs
            if i % 10 == 0 and i > 0:
                time.sleep(2)
        
        return results
    
    def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """Reverse geocode coordinates to address"""
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': lat,
            'lon': lng,
            'format': 'json',
            'zoom': 18
        }
        
        time.sleep(1)  # Rate limiting
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'display_name' in data:
            return data['display_name']
        
        return None

# Initialize geocoding service
geocoder = GeocodingService()
