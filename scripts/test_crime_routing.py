#!/usr/bin/env python3
"""
Test script for crime-aware routing system.
Tests the backend API endpoints and validates responses.
"""

import requests
import json
import time
from typing import Dict, Any

# Test configuration
BACKEND_URL = "http://localhost:8000"
TEST_COORDINATES = [
    {
        "name": "Union Square to Golden Gate Park",
        "start": {"lat": 37.7880, "lng": -122.4074},
        "end": {"lat": 37.7694, "lng": -122.4862}
    },
    {
        "name": "Mission District to Financial District", 
        "start": {"lat": 37.7599, "lng": -122.4148},
        "end": {"lat": 37.7955, "lng": -122.4009}
    },
    {
        "name": "Tenderloin to Marina District",
        "start": {"lat": 37.7849, "lng": -122.4094},
        "end": {"lat": 37.8026, "lng": -122.4484}
    }
]

def test_backend_health():
    """Test if backend is running and healthy."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend not accessible: {e}")
        return False

def test_crime_aware_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, route_type: str = "balanced") -> Dict[str, Any]:
    """Test crime-aware route calculation."""
    url = f"{BACKEND_URL}/route/crime-aware"
    payload = {
        "start_lat": start_lat,
        "start_lng": start_lng,
        "end_lat": end_lat,
        "end_lng": end_lng,
        "route_type": route_type
    }
    
    try:
        print(f"  Testing {route_type} route...")
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Route calculated successfully")
            print(f"    📊 Distance: {data.get('total_distance', 'N/A')} km")
            print(f"    Time: {data.get('estimated_time', 'N/A')} min")
            print(f"    🛡️ Safety Score: {data.get('safety_score', 'N/A')}")
            
            # Check for required fields
            required_fields = ['route_type', 'total_distance', 'safety_score', 'segments']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print(f"    ⚠️ Missing fields: {missing_fields}")
            
            # Check crime data
            if 'crime_density_map' in data:
                print(f"    🗺️ Crime density map: {len(data['crime_density_map'].get('heatmap_data', []))} points")
            
            if 'critical_crime_zones' in data:
                print(f"    🚨 Critical crime zones: {len(data['critical_crime_zones'])} zones")
            
            if 'route_safety_breakdown' in data:
                breakdown = data['route_safety_breakdown']
                if 'route_safety_summary' in breakdown:
                    grade = breakdown['route_safety_summary'].get('safety_grade', 'N/A')
                    print(f"    📈 Safety Grade: {grade}")
            
            return data
        else:
            print(f"    ❌ Route calculation failed: {response.status_code}")
            print(f"    Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Request failed: {e}")
        return None

def test_route_comparison(start_lat: float, start_lng: float, end_lat: float, end_lng: float):
    """Test route comparison endpoint."""
    url = f"{BACKEND_URL}/route/crime-aware/compare"
    payload = {
        "start_lat": start_lat,
        "start_lng": start_lng,
        "end_lat": end_lat,
        "end_lng": end_lng
    }
    
    try:
        print(f"  Testing route comparison...")
        response = requests.post(url, json=payload, timeout=45)
        
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Route comparison successful")
            
            if 'routes' in data:
                routes = data['routes']
                print(f"    📊 Found {len(routes)} route options:")
                
                for i, route in enumerate(routes):
                    route_type = route.get('route_type', 'Unknown')
                    distance = route.get('total_distance', 'N/A')
                    safety = route.get('safety_score', 'N/A')
                    print(f"      {i+1}. {route_type}: {distance}km, Safety: {safety}")
            
            return data
        else:
            print(f"    ❌ Route comparison failed: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Comparison request failed: {e}")
        return None

def run_comprehensive_test():
    """Run comprehensive test suite."""
    print("🚀 Starting Crime-Aware Routing Test Suite")
    print("=" * 50)
    
    # Test backend health
    if not test_backend_health():
        print("❌ Backend not available. Please start the backend first.")
        return False
    
    print("\n📋 Testing Crime-Aware Routes")
    print("-" * 30)
    
    all_tests_passed = True
    
    for i, test_case in enumerate(TEST_COORDINATES, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   From: ({test_case['start']['lat']}, {test_case['start']['lng']})")
        print(f"   To: ({test_case['end']['lat']}, {test_case['end']['lng']})")
        
        # Test different route types
        route_types = ['safest', 'balanced', 'fastest']
        route_results = {}
        
        for route_type in route_types:
            result = test_crime_aware_route(
                test_case['start']['lat'],
                test_case['start']['lng'],
                test_case['end']['lat'],
                test_case['end']['lng'],
                route_type
            )
            route_results[route_type] = result
            
            if result is None:
                all_tests_passed = False
        
        # Test route comparison
        comparison_result = test_route_comparison(
            test_case['start']['lat'],
            test_case['start']['lng'],
            test_case['end']['lat'],
            test_case['end']['lng']
        )
        
        if comparison_result is None:
            all_tests_passed = False
        
        # Brief analysis
        if route_results['safest'] and route_results['fastest']:
            safest_distance = route_results['safest'].get('total_distance', 0)
            fastest_distance = route_results['fastest'].get('total_distance', 0)
            if safest_distance > fastest_distance:
                print(f"   📊 Safest route is {safest_distance - fastest_distance:.2f}km longer")
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("✅ All tests passed! Crime-aware routing is working correctly.")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    
    return all_tests_passed

def test_specific_scenario():
    """Test a specific scenario with detailed output."""
    print("\n🔍 Detailed Scenario Test")
    print("-" * 25)
    
    # Union Square to Golden Gate Park
    start_lat, start_lng = 37.7880, -122.4074
    end_lat, end_lng = 37.7694, -122.4862
    
    print(f"Testing: Union Square → Golden Gate Park")
    print(f"Coordinates: ({start_lat}, {start_lng}) → ({end_lat}, {end_lng})")
    
    result = test_crime_aware_route(start_lat, start_lng, end_lat, end_lng, "safest")
    
    if result:
        print("\n📊 Detailed Results:")
        print(f"  Route Type: {result.get('route_type')}")
        print(f"  Total Distance: {result.get('total_distance')} km")
        print(f"  Estimated Time: {result.get('estimated_time')} minutes")
        print(f"  Safety Score: {result.get('safety_score')}")
        
        if 'route_safety_breakdown' in result:
            breakdown = result['route_safety_breakdown']
            if 'route_safety_summary' in breakdown:
                summary = breakdown['route_safety_summary']
                print(f"  Safety Grade: {summary.get('safety_grade')}")
                print(f"  Overall Safety: {summary.get('overall_safety_score')}")
        
        if 'segments' in result:
            segments = result['segments']
            print(f"  Route Segments: {len(segments)}")
            
            # Show first few segments
            for i, segment in enumerate(segments[:3]):
                safety = segment.get('safety_score', 'N/A')
                distance = segment.get('distance', 'N/A')
                print(f"    Segment {i+1}: {distance}m, Safety: {safety}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--detailed":
        test_specific_scenario()
    else:
        run_comprehensive_test()
        
    print("\n💡 Tips:")
    print("  - Run with --detailed for in-depth analysis")
    print("  - Check backend logs for any errors")
    print("  - Verify database has crime data")
    print("  - Test frontend at http://localhost:3000")
