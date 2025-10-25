#!/usr/bin/env python3
"""
Real-time Alerts System
Monitors new crime data and generates alerts for restricted paths
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_sqlite import db_manager, CrimeReport
from safety_analyzer import SafetyAnalyzer
from safe_router import SafeRouter

class AlertType(Enum):
    """Types of alerts"""
    HIGH_CRIME_AREA = "high_crime_area"
    RECENT_INCIDENT = "recent_incident"
    SEVERITY_INCREASE = "severity_increase"
    ROUTE_BLOCKED = "route_blocked"
    SAFETY_DECLINE = "safety_decline"

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Alert:
    """Real-time alert"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    lat: float
    lng: float
    radius_km: float
    created_at: datetime
    expires_at: Optional[datetime]
    affected_routes: List[str]
    safety_impact: float  # 0-100, how much this affects safety

@dataclass
class AlertZone:
    """Zone affected by an alert"""
    lat: float
    lng: float
    radius_km: float
    alert_types: List[AlertType]
    severity: AlertSeverity
    is_active: bool

class RealTimeAlerts:
    """Real-time alerts system"""
    
    def __init__(self):
        self.db_manager = db_manager
        self.safety_analyzer = SafetyAnalyzer()
        self.alert_radius_km = 0.2  # 200m radius for alerts
        self.recent_hours = 24  # Hours to consider for recent incidents
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_zones: List[AlertZone] = []
        
    async def check_for_new_alerts(self) -> List[Alert]:
        """Check for new alerts based on recent crime data"""
        new_alerts = []
        
        # Get recent crimes (last 24 hours)
        recent_crimes = await self._get_recent_crimes()
        
        # Check for different types of alerts
        new_alerts.extend(await self._check_high_crime_areas(recent_crimes))
        new_alerts.extend(await self._check_severity_increases(recent_crimes))
        new_alerts.extend(await self._check_safety_declines(recent_crimes))
        new_alerts.extend(await self._check_route_blockages(recent_crimes))
        
        # Add new alerts to active alerts
        for alert in new_alerts:
            self.active_alerts[alert.alert_id] = alert
        
        # Update alert zones
        await self._update_alert_zones()
        
        return new_alerts
    
    async def get_active_alerts(self, lat: float, lng: float, 
                               radius_km: float = 1.0) -> List[Alert]:
        """Get active alerts in a specific area"""
        relevant_alerts = []
        
        for alert in self.active_alerts.values():
            if self._is_alert_in_range(alert, lat, lng, radius_km):
                relevant_alerts.append(alert)
        
        return relevant_alerts
    
    async def get_alert_zones(self, bounds: Dict[str, float]) -> List[AlertZone]:
        """Get alert zones in a specific area"""
        relevant_zones = []
        
        for zone in self.alert_zones:
            if self._is_zone_in_bounds(zone, bounds):
                relevant_zones.append(zone)
        
        return relevant_zones
    
    async def check_route_safety(self, route_points: List[Dict]) -> Dict:
        """Check if a route is affected by any alerts"""
        route_alerts = []
        blocked_segments = []
        
        for i, point in enumerate(route_points):
            lat, lng = point['lat'], point['lng']
            
            # Check for alerts at this point
            point_alerts = await self.get_active_alerts(lat, lng, self.alert_radius_km)
            
            if point_alerts:
                route_alerts.extend(point_alerts)
                
                # Check if this segment should be blocked
                if any(alert.alert_type == AlertType.ROUTE_BLOCKED for alert in point_alerts):
                    blocked_segments.append({
                        'start_index': max(0, i-1),
                        'end_index': min(len(route_points)-1, i+1),
                        'reason': 'Route blocked due to recent incident'
                    })
        
        return {
            'has_alerts': len(route_alerts) > 0,
            'alerts': [
                {
                    'type': alert.alert_type.value,
                    'severity': alert.severity.value,
                    'title': alert.title,
                    'description': alert.description,
                    'lat': alert.lat,
                    'lng': alert.lng,
                    'radius_km': alert.radius_km
                }
                for alert in route_alerts
            ],
            'blocked_segments': blocked_segments,
            'safety_recommendation': self._get_safety_recommendation(route_alerts)
        }
    
    async def _get_recent_crimes(self) -> List[CrimeReport]:
        """Get crimes from the last 24 hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.recent_hours)
        
        with self.db_manager.get_session() as session:
            crimes = session.query(CrimeReport).filter(
                CrimeReport.occurred_at >= cutoff_time
            ).all()
            
            return crimes
    
    async def _check_high_crime_areas(self, recent_crimes: List[CrimeReport]) -> List[Alert]:
        """Check for high crime areas"""
        alerts = []
        
        # Group crimes by location
        crime_groups = self._group_crimes_by_location(recent_crimes)
        
        for location, crimes in crime_groups.items():
            if len(crimes) >= 3:  # 3+ crimes in same area
                lat, lng = location
                
                # Calculate severity
                severity = self._calculate_alert_severity(crimes)
                
                alert = Alert(
                    alert_id=f"high_crime_{lat}_{lng}_{datetime.utcnow().timestamp()}",
                    alert_type=AlertType.HIGH_CRIME_AREA,
                    severity=severity,
                    title=f"High Crime Activity",
                    description=f"{len(crimes)} incidents reported in this area in the last {self.recent_hours} hours",
                    lat=lat,
                    lng=lng,
                    radius_km=self.alert_radius_km,
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(hours=6),
                    affected_routes=[],
                    safety_impact=min(50, len(crimes) * 10)
                )
                
                alerts.append(alert)
        
        return alerts
    
    async def _check_severity_increases(self, recent_crimes: List[CrimeReport]) -> List[Alert]:
        """Check for increases in crime severity"""
        alerts = []
        
        # Get high severity crimes (severity >= 7)
        high_severity_crimes = [c for c in recent_crimes if c.severity >= 7]
        
        for crime in high_severity_crimes:
            if crime.lat and crime.lng:
                severity = AlertSeverity.HIGH if crime.severity >= 9 else AlertSeverity.MEDIUM
                
                alert = Alert(
                    alert_id=f"severity_{crime.id}_{datetime.utcnow().timestamp()}",
                    alert_type=AlertType.SEVERITY_INCREASE,
                    severity=severity,
                    title=f"High Severity Incident",
                    description=f"{crime.crime_type} reported with severity {crime.severity}/10",
                    lat=crime.lat,
                    lng=crime.lng,
                    radius_km=self.alert_radius_km,
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(hours=12),
                    affected_routes=[],
                    safety_impact=crime.severity * 10
                )
                
                alerts.append(alert)
        
        return alerts
    
    async def _check_safety_declines(self, recent_crimes: List[CrimeReport]) -> List[Alert]:
        """Check for areas with declining safety"""
        alerts = []
        
        # Group crimes by location
        crime_groups = self._group_crimes_by_location(recent_crimes)
        
        for location, crimes in crime_groups.items():
            lat, lng = location
            
            # Analyze current safety
            current_safety = self.safety_analyzer.analyze_point_safety(lat, lng)
            
            # If safety is very low, create alert
            if current_safety.safety_percentage < 30:
                severity = AlertSeverity.HIGH if current_safety.safety_percentage < 20 else AlertSeverity.MEDIUM
                
                alert = Alert(
                    alert_id=f"safety_decline_{lat}_{lng}_{datetime.utcnow().timestamp()}",
                    alert_type=AlertType.SAFETY_DECLINE,
                    severity=severity,
                    title=f"Low Safety Area",
                    description=f"Safety level: {current_safety.safety_percentage:.1f}% - Exercise caution",
                    lat=lat,
                    lng=lng,
                    radius_km=self.alert_radius_km,
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(hours=8),
                    affected_routes=[],
                    safety_impact=100 - current_safety.safety_percentage
                )
                
                alerts.append(alert)
        
        return alerts
    
    async def _check_route_blockages(self, recent_crimes: List[CrimeReport]) -> List[Alert]:
        """Check for crimes that might block routes"""
        alerts = []
        
        # Look for crimes that might block major routes
        for crime in recent_crimes:
            if crime.lat and crime.lng:
                # Check if this is a high-impact crime that might block routes
                if (crime.severity >= 8 or 
                    crime.crime_type in ['Robbery', 'Assault', 'Motor Vehicle Theft']):
                    
                    severity = AlertSeverity.CRITICAL if crime.severity >= 9 else AlertSeverity.HIGH
                    
                    alert = Alert(
                        alert_id=f"route_block_{crime.id}_{datetime.utcnow().timestamp()}",
                        alert_type=AlertType.ROUTE_BLOCKED,
                        severity=severity,
                        title=f"Route May Be Blocked",
                        description=f"Recent {crime.crime_type} may affect nearby routes",
                        lat=crime.lat,
                        lng=crime.lng,
                        radius_km=self.alert_radius_km * 2,  # Larger radius for route blocks
                        created_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(hours=4),
                        affected_routes=[],
                        safety_impact=crime.severity * 15
                    )
                    
                    alerts.append(alert)
        
        return alerts
    
    def _group_crimes_by_location(self, crimes: List[CrimeReport], 
                                 precision: float = 0.001) -> Dict[Tuple[float, float], List[CrimeReport]]:
        """Group crimes by location (rounded to precision)"""
        groups = {}
        
        for crime in crimes:
            if crime.lat and crime.lng:
                # Round coordinates to group nearby crimes
                rounded_lat = round(crime.lat / precision) * precision
                rounded_lng = round(crime.lng / precision) * precision
                location = (rounded_lat, rounded_lng)
                
                if location not in groups:
                    groups[location] = []
                groups[location].append(crime)
        
        return groups
    
    def _calculate_alert_severity(self, crimes: List[CrimeReport]) -> AlertSeverity:
        """Calculate alert severity based on crimes"""
        if not crimes:
            return AlertSeverity.LOW
        
        # Count high severity crimes
        high_severity_count = sum(1 for c in crimes if c.severity >= 7)
        total_count = len(crimes)
        
        # Calculate severity
        if high_severity_count >= 2 or total_count >= 5:
            return AlertSeverity.CRITICAL
        elif high_severity_count >= 1 or total_count >= 3:
            return AlertSeverity.HIGH
        elif total_count >= 2:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    
    def _is_alert_in_range(self, alert: Alert, lat: float, lng: float, radius_km: float) -> bool:
        """Check if alert is within range of a point"""
        distance = self._calculate_distance(alert.lat, alert.lng, lat, lng)
        return distance <= (alert.radius_km + radius_km)
    
    def _is_zone_in_bounds(self, zone: AlertZone, bounds: Dict[str, float]) -> bool:
        """Check if alert zone is within bounds"""
        return (bounds['south'] <= zone.lat <= bounds['north'] and
                bounds['west'] <= zone.lng <= bounds['east'])
    
    def _get_safety_recommendation(self, alerts: List[Alert]) -> str:
        """Get safety recommendation based on alerts"""
        if not alerts:
            return "Route appears safe"
        
        critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
        high_alerts = [a for a in alerts if a.severity == AlertSeverity.HIGH]
        
        if critical_alerts:
            return "AVOID: Critical safety issues detected"
        elif high_alerts:
            return "CAUTION: High safety concerns - consider alternative route"
        else:
            return "MODERATE: Some safety concerns - proceed with caution"
    
    async def _update_alert_zones(self):
        """Update alert zones based on active alerts"""
        self.alert_zones = []
        
        for alert in self.active_alerts.values():
            if alert.expires_at and alert.expires_at > datetime.utcnow():
                zone = AlertZone(
                    lat=alert.lat,
                    lng=alert.lng,
                    radius_km=alert.radius_km,
                    alert_types=[alert.alert_type],
                    severity=alert.severity,
                    is_active=True
                )
                self.alert_zones.append(zone)
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in km"""
        import math
        
        R = 6371  # Earth's radius in km
        
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlng/2) * math.sin(dlng/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = 6371 * c
        
        return distance

class RealTimeAlertsAPI:
    """API wrapper for real-time alerts"""
    
    def __init__(self):
        self.alerts_system = RealTimeAlerts()
    
    async def check_alerts(self) -> Dict:
        """Check for new alerts"""
        new_alerts = await self.alerts_system.check_for_new_alerts()
        
        return {
            'new_alerts_count': len(new_alerts),
            'alerts': [
                {
                    'id': alert.alert_id,
                    'type': alert.alert_type.value,
                    'severity': alert.severity.value,
                    'title': alert.title,
                    'description': alert.description,
                    'lat': alert.lat,
                    'lng': alert.lng,
                    'radius_km': alert.radius_km,
                    'created_at': alert.created_at.isoformat(),
                    'expires_at': alert.expires_at.isoformat() if alert.expires_at else None
                }
                for alert in new_alerts
            ]
        }
    
    async def get_area_alerts(self, lat: float, lng: float, radius_km: float = 1.0) -> Dict:
        """Get alerts for a specific area"""
        alerts = await self.alerts_system.get_active_alerts(lat, lng, radius_km)
        
        return {
            'alerts_count': len(alerts),
            'alerts': [
                {
                    'id': alert.alert_id,
                    'type': alert.alert_type.value,
                    'severity': alert.severity.value,
                    'title': alert.title,
                    'description': alert.description,
                    'lat': alert.lat,
                    'lng': alert.lng,
                    'radius_km': alert.radius_km,
                    'safety_impact': alert.safety_impact
                }
                for alert in alerts
            ]
        }
    
    async def check_route_safety(self, route_points: List[Dict]) -> Dict:
        """Check route safety for alerts"""
        return await self.alerts_system.check_route_safety(route_points)

# Test the alerts system
if __name__ == "__main__":
    async def test_alerts():
        alerts_api = RealTimeAlertsAPI()
        
        print("Testing Real-time Alerts System")
        print("=" * 40)
        
        # Check for new alerts
        alerts_result = await alerts_api.check_alerts()
        print(f"New alerts: {alerts_result['new_alerts_count']}")
        
        # Check area alerts
        area_alerts = await alerts_api.get_area_alerts(37.7749, -122.4194, 1.0)
        print(f"Area alerts: {area_alerts['alerts_count']}")
        
        # Check route safety
        test_route = [
            {'lat': 37.7749, 'lng': -122.4194},
            {'lat': 37.7849, 'lng': -122.4094}
        ]
        route_safety = await alerts_api.check_route_safety(test_route)
        print(f"Route has alerts: {route_safety['has_alerts']}")
        print(f"Safety recommendation: {route_safety['safety_recommendation']}")
    
    asyncio.run(test_alerts())
