#!/usr/bin/env python3
"""
Safety Analysis System
Analyzes crime density and calculates safety scores for areas
"""

import math
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_sqlite import db_manager, CrimeReport

@dataclass
class SafetyScore:
    """Safety score for a specific area"""
    lat: float
    lng: float
    safety_percentage: float  # 0-100 (100 = safest)
    crime_density: float
    recent_crimes: int
    high_severity_crimes: int
    confidence_level: float  # 0-1 (1 = highest confidence)
    analysis_date: datetime
    area_type: str  # 'point', 'route_segment', 'area'

@dataclass
class CrimeDensity:
    """Crime density analysis for an area"""
    total_crimes: int
    recent_crimes: int  # Last 30 days
    high_severity_crimes: int  # Severity >= 7
    density_per_sq_km: float
    severity_weighted_density: float
    time_weighted_density: float

class SafetyAnalyzer:
    """Main safety analysis system"""
    
    def __init__(self):
        self.db_manager = db_manager
        self.analysis_radius_km = 0.5  # 500m radius for analysis
        self.recent_days = 30  # Days to consider for recent crimes
        self.high_severity_threshold = 7  # Severity threshold for high-risk crimes
        
    def analyze_point_safety(self, lat: float, lng: float, radius_km: float = None) -> SafetyScore:
        """Analyze safety for a specific point"""
        if radius_km is None:
            radius_km = self.analysis_radius_km
            
        # Get crimes in radius
        crimes = self._get_crimes_in_radius(lat, lng, radius_km)
        
        # Calculate crime density
        density = self._calculate_crime_density(crimes, radius_km)
        
        # Calculate safety score
        safety_percentage = self._calculate_safety_percentage(density)
        
        # Calculate confidence level
        confidence = self._calculate_confidence_level(crimes, density)
        
        return SafetyScore(
            lat=lat,
            lng=lng,
            safety_percentage=safety_percentage,
            crime_density=density.density_per_sq_km,
            recent_crimes=density.recent_crimes,
            high_severity_crimes=density.high_severity_crimes,
            confidence_level=confidence,
            analysis_date=datetime.utcnow(),
            area_type='point'
        )
    
    def analyze_route_safety(self, route_points: List[Tuple[float, float]], 
                           segment_length_km: float = 0.1) -> List[SafetyScore]:
        """Analyze safety along a route"""
        safety_scores = []
        
        for i, (lat, lng) in enumerate(route_points):
            # Analyze each point along the route
            safety_score = self.analyze_point_safety(lat, lng, segment_length_km)
            safety_scores.append(safety_score)
        
        return safety_scores
    
    def analyze_area_safety(self, bounds: Dict[str, float]) -> Dict[str, SafetyScore]:
        """Analyze safety for a rectangular area"""
        # bounds = {'north': float, 'south': float, 'east': float, 'west': float}
        
        # Create grid of analysis points
        grid_points = self._create_analysis_grid(bounds)
        
        area_scores = {}
        for point in grid_points:
            lat, lng = point
            safety_score = self.analyze_point_safety(lat, lng)
            area_scores[f"{lat:.4f},{lng:.4f}"] = safety_score
        
        return area_scores
    
    def get_safety_heatmap_data(self, bounds: Dict[str, float], 
                              grid_size: int = 20) -> List[Dict]:
        """Generate heatmap data for safety visualization"""
        # Create grid
        lat_step = (bounds['north'] - bounds['south']) / grid_size
        lng_step = (bounds['east'] - bounds['west']) / grid_size
        
        heatmap_data = []
        
        for i in range(grid_size):
            for j in range(grid_size):
                lat = bounds['south'] + (i * lat_step)
                lng = bounds['west'] + (j * lng_step)
                
                safety_score = self.analyze_point_safety(lat, lng)
                
                heatmap_data.append({
                    'lat': lat,
                    'lng': lng,
                    'safety_percentage': safety_score.safety_percentage,
                    'crime_density': safety_score.crime_density,
                    'confidence': safety_score.confidence_level
                })
        
        return heatmap_data
    
    def get_high_risk_areas(self, bounds: Dict[str, float], 
                           safety_threshold: float = 30.0) -> List[Dict]:
        """Get areas with safety percentage below threshold"""
        heatmap_data = self.get_safety_heatmap_data(bounds)
        
        high_risk_areas = []
        for point in heatmap_data:
            if point['safety_percentage'] < safety_threshold:
                high_risk_areas.append({
                    'lat': point['lat'],
                    'lng': point['lng'],
                    'safety_percentage': point['safety_percentage'],
                    'crime_density': point['crime_density'],
                    'risk_level': self._get_risk_level(point['safety_percentage'])
                })
        
        return high_risk_areas
    
    def _get_crimes_in_radius(self, lat: float, lng: float, radius_km: float) -> List[CrimeReport]:
        """Get crimes within radius of a point"""
        with self.db_manager.get_session() as session:
            # Simple bounding box approximation for SQLite
            # Convert km to degrees (approximate)
            lat_delta = radius_km / 111.0  # 1 degree latitude ≈ 111 km
            lng_delta = radius_km / (111.0 * math.cos(math.radians(lat)))
            
            crimes = session.query(CrimeReport).filter(
                CrimeReport.lat.isnot(None),
                CrimeReport.lng.isnot(None),
                CrimeReport.lat >= lat - lat_delta,
                CrimeReport.lat <= lat + lat_delta,
                CrimeReport.lng >= lng - lng_delta,
                CrimeReport.lng <= lng + lng_delta
            ).all()
            
            # Filter by actual distance
            filtered_crimes = []
            for crime in crimes:
                distance = self._calculate_distance(lat, lng, crime.lat, crime.lng)
                if distance <= radius_km:
                    filtered_crimes.append(crime)
            
            return filtered_crimes
    
    def _calculate_crime_density(self, crimes: List[CrimeReport], radius_km: float) -> CrimeDensity:
        """Calculate crime density metrics"""
        total_crimes = len(crimes)
        
        # Recent crimes (last 30 days)
        recent_cutoff = datetime.utcnow() - timedelta(days=self.recent_days)
        recent_crimes = [c for c in crimes if c.occurred_at >= recent_cutoff]
        
        # High severity crimes
        high_severity_crimes = [c for c in crimes if c.severity >= self.high_severity_threshold]
        
        # Calculate densities
        area_sq_km = math.pi * (radius_km ** 2)
        density_per_sq_km = total_crimes / area_sq_km if area_sq_km > 0 else 0
        
        # Severity-weighted density
        severity_weight = sum(c.severity for c in crimes) / len(crimes) if crimes else 0
        severity_weighted_density = density_per_sq_km * severity_weight
        
        # Time-weighted density (recent crimes weighted more)
        time_weighted_crimes = 0
        for crime in crimes:
            days_ago = (datetime.utcnow() - crime.occurred_at).days
            weight = max(0, 1 - (days_ago / 365))  # Linear decay over year
            time_weighted_crimes += weight
        
        time_weighted_density = time_weighted_crimes / area_sq_km if area_sq_km > 0 else 0
        
        return CrimeDensity(
            total_crimes=total_crimes,
            recent_crimes=len(recent_crimes),
            high_severity_crimes=len(high_severity_crimes),
            density_per_sq_km=density_per_sq_km,
            severity_weighted_density=severity_weighted_density,
            time_weighted_density=time_weighted_density
        )
    
    def _calculate_safety_percentage(self, density: CrimeDensity) -> float:
        """Calculate safety percentage (0-100, 100 = safest)"""
        # Base safety score
        base_safety = 100.0
        
        # Penalty for total crime density
        density_penalty = min(50.0, density.density_per_sq_km * 2.0)
        
        # Penalty for recent crimes
        recent_penalty = min(30.0, density.recent_crimes * 3.0)
        
        # Penalty for high severity crimes
        severity_penalty = min(40.0, density.high_severity_crimes * 8.0)
        
        # Penalty for severity-weighted density
        severity_weighted_penalty = min(20.0, density.severity_weighted_density * 1.5)
        
        # Calculate final safety percentage
        safety_percentage = base_safety - density_penalty - recent_penalty - severity_penalty - severity_weighted_penalty
        
        return max(0.0, min(100.0, safety_percentage))
    
    def _calculate_confidence_level(self, crimes: List[CrimeReport], density: CrimeDensity) -> float:
        """Calculate confidence level in safety analysis"""
        # More crimes = higher confidence
        crime_confidence = min(1.0, len(crimes) / 50.0)
        
        # Recent data = higher confidence
        recent_confidence = min(1.0, density.recent_crimes / 10.0)
        
        # Geographic spread = higher confidence
        if len(crimes) > 1:
            lats = [c.lat for c in crimes if c.lat]
            lngs = [c.lng for c in crimes if c.lng]
            if lats and lngs:
                lat_spread = max(lats) - min(lats)
                lng_spread = max(lngs) - min(lngs)
                spread_confidence = min(1.0, (lat_spread + lng_spread) * 1000)  # Convert to km
            else:
                spread_confidence = 0.5
        else:
            spread_confidence = 0.3
        
        # Combine confidence factors
        confidence = (crime_confidence * 0.4 + recent_confidence * 0.3 + spread_confidence * 0.3)
        
        return max(0.1, min(1.0, confidence))
    
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
    
    def _create_analysis_grid(self, bounds: Dict[str, float], grid_size: int = 10) -> List[Tuple[float, float]]:
        """Create grid of analysis points for area analysis"""
        lat_step = (bounds['north'] - bounds['south']) / grid_size
        lng_step = (bounds['east'] - bounds['west']) / grid_size
        
        points = []
        for i in range(grid_size):
            for j in range(grid_size):
                lat = bounds['south'] + (i * lat_step)
                lng = bounds['west'] + (j * lng_step)
                points.append((lat, lng))
        
        return points
    
    def _get_risk_level(self, safety_percentage: float) -> str:
        """Get risk level description"""
        if safety_percentage >= 80:
            return "Low Risk"
        elif safety_percentage >= 60:
            return "Moderate Risk"
        elif safety_percentage >= 40:
            return "High Risk"
        else:
            return "Very High Risk"

class SafetyAnalyzerAPI:
    """API wrapper for safety analysis"""
    
    def __init__(self):
        self.analyzer = SafetyAnalyzer()
    
    def get_point_safety(self, lat: float, lng: float) -> Dict:
        """Get safety analysis for a point"""
        safety_score = self.analyzer.analyze_point_safety(lat, lng)
        
        return {
            'lat': safety_score.lat,
            'lng': safety_score.lng,
            'safety_percentage': round(safety_score.safety_percentage, 1),
            'crime_density': round(safety_score.crime_density, 2),
            'recent_crimes': safety_score.recent_crimes,
            'high_severity_crimes': safety_score.high_severity_crimes,
            'confidence_level': round(safety_score.confidence_level, 2),
            'risk_level': self.analyzer._get_risk_level(safety_score.safety_percentage),
            'analysis_date': safety_score.analysis_date.isoformat()
        }
    
    def get_route_safety(self, route_points: List[Dict]) -> List[Dict]:
        """Get safety analysis for a route"""
        points = [(point['lat'], point['lng']) for point in route_points]
        safety_scores = self.analyzer.analyze_route_safety(points)
        
        return [self.get_point_safety(score.lat, score.lng) for score in safety_scores]
    
    def get_heatmap_data(self, bounds: Dict[str, float]) -> List[Dict]:
        """Get heatmap data for visualization"""
        return self.analyzer.get_safety_heatmap_data(bounds)
    
    def get_high_risk_areas(self, bounds: Dict[str, float]) -> List[Dict]:
        """Get high-risk areas"""
        return self.analyzer.get_high_risk_areas(bounds)

# Test the safety analyzer
if __name__ == "__main__":
    analyzer = SafetyAnalyzer()
    
    # Test with a point in San Francisco
    test_lat = 37.7749
    test_lng = -122.4194
    
    print("Testing Safety Analyzer")
    print("=" * 40)
    
    safety_score = analyzer.analyze_point_safety(test_lat, test_lng)
    
    print(f"Location: {test_lat}, {test_lng}")
    print(f"Safety Percentage: {safety_score.safety_percentage:.1f}%")
    print(f"Crime Density: {safety_score.crime_density:.2f} crimes/km²")
    print(f"Recent Crimes (30 days): {safety_score.recent_crimes}")
    print(f"High Severity Crimes: {safety_score.high_severity_crimes}")
    print(f"Confidence Level: {safety_score.confidence_level:.2f}")
    print(f"Risk Level: {analyzer._get_risk_level(safety_score.safety_percentage)}")
