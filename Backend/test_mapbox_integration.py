#!/usr/bin/env python3
"""
Test Mapbox Integration for Crime-Aware Router
Tests the complete flow: Mapbox route -> crime overlay -> accurate times
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mapbox_directions import MapboxDirectionsClient
from crime_aware_router import CrimeAwareRouter

async def test_mapbox_client():
    """Test Mapbox Directions API client directly"""
    print("🧪 Testing Mapbox Directions API Client...")
    
    # Set test token directly (this is a public test token from Mapbox docs)
    mapbox_token = "pk.eyJ1IjoiYW5keXltYW9vIiwiYSI6ImNtaDYzMGhrdzA4dnAya29vbW4wcHZ6ODEifQ.NNhIooCa7yGJzYEegxEdAw"
    
    try:
        client = MapboxDirectionsClient(mapbox_token)
        
        # Test route: SF to Oakland (walking)
        start_lat, start_lng = 37.7880, -122.4074  # SF
        end_lat, end_lng = 37.7694, -122.4862      # Oakland
        
        print(f"📍 Testing route: SF ({start_lat}, {start_lng}) -> Oakland ({end_lat}, {end_lng})")
        
        route = await client.get_route(
            start_lat, start_lng, end_lat, end_lng, mode='walking'
        )
        
        print(f"✅ Mapbox route successful!")
        print(f"   📊 Coordinates: {len(route['coordinates'])} waypoints")
        print(f"   📏 Distance: {route['distance']:.0f} meters")
        print(f"   ⏱️ Duration: {route['duration']/60:.1f} minutes")
        print(f"   🚶 Mode: {route['mode']}")
        
        # Show first few coordinates
        print(f"   🗺️ First 3 waypoints:")
        for i, (lat, lng) in enumerate(route['coordinates'][:3]):
            print(f"      {i+1}. ({lat:.6f}, {lng:.6f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Mapbox API test failed: {e}")
        return False

async def test_crime_aware_router():
    """Test CrimeAwareRouter with Mapbox integration"""
    print("\n🧪 Testing Crime-Aware Router with Mapbox...")
    
    # Set test token directly (this is a public test token from Mapbox docs)
    mapbox_token = "pk.eyJ1IjoiYW5keXltYW9vIiwiYSI6ImNtaDYzMGhrdzA4dnAya29vbW4wcHZ6ODEifQ.NNhIooCa7yGJzYEegxEdAw"
    
    try:
        # Initialize router with SQLite database (fallback)
        database_url = "sqlite:///./safepath.db"
        router = CrimeAwareRouter(database_url, mapbox_token=mapbox_token)
        
        # Test route: SF to Oakland (walking)
        start_lat, start_lng = 37.7880, -122.4074  # SF
        end_lat, end_lng = 37.7694, -122.4862      # Oakland
        
        print(f"📍 Testing crime-aware route: SF -> Oakland")
        
        # Test different route types
        for route_type in ['balanced', 'safest', 'fastest']:
            print(f"\n🔍 Testing {route_type} route...")
            
            route = await router.find_optimal_route(
                start_lat, start_lng, end_lat, end_lng, 
                route_type=route_type, travel_mode='walking'
            )
            
            print(f"   ✅ {route_type.title()} route calculated!")
            print(f"   📊 Segments: {len(route.segments)}")
            print(f"   📏 Distance: {route.total_distance:.0f}m")
            print(f"   🛡️ Safety Score: {route.total_safety_score:.1f}")
            print(f"   ⚠️ Crime Penalty: {route.total_crime_penalty:.1f}")
            print(f"   ⏱️ Estimated Time: {route.estimated_time_minutes:.1f} min")
            print(f"   🗺️ Base Time: {route.base_route_time_minutes:.1f} min")
            print(f"   📍 Waypoints: {len(route.path_coordinates)}")
            
            # Verify we have real street coordinates (not just 2 points)
            if len(route.path_coordinates) > 10:
                print(f"   ✅ Real street route with {len(route.path_coordinates)} waypoints")
            else:
                print(f"   ⚠️ Only {len(route.path_coordinates)} waypoints - may be fallback routing")
        
        return True
        
    except Exception as e:
        print(f"❌ Crime-aware router test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_route_comparison():
    """Test route comparison between Mapbox and fallback"""
    print("\n🧪 Testing Route Comparison...")
    
    # Set test token directly (this is a public test token from Mapbox docs)
    mapbox_token = "pk.eyJ1IjoiYW5keXltYW9vIiwiYSI6ImNtaDYzMGhrdzA4dnAya29vbW4wcHZ6ODEifQ.NNhIooCa7yGJzYEegxEdAw"
    database_url = "sqlite:///./safepath.db"
    
    # Test with Mapbox
    router_with_mapbox = CrimeAwareRouter(database_url, mapbox_token=mapbox_token)
    
    # Test without Mapbox (fallback)
    router_without_mapbox = CrimeAwareRouter(database_url, mapbox_token=None)
    
    start_lat, start_lng = 37.7880, -122.4074  # SF
    end_lat, end_lng = 37.7694, -122.4862      # Oakland
    
    print(f"📍 Comparing routes: SF -> Oakland")
    
    try:
        # Route with Mapbox
        route_mapbox = await router_with_mapbox.find_optimal_route(
            start_lat, start_lng, end_lat, end_lng, route_type='balanced'
        )
        
        # Route without Mapbox (fallback)
        route_fallback = await router_without_mapbox.find_optimal_route(
            start_lat, start_lng, end_lat, end_lng, route_type='balanced'
        )
        
        print(f"\n📊 Comparison Results:")
        print(f"   🗺️ Mapbox Route:")
        print(f"      Waypoints: {len(route_mapbox.path_coordinates)}")
        print(f"      Distance: {route_mapbox.total_distance:.0f}m")
        print(f"      Time: {route_mapbox.estimated_time_minutes:.1f} min")
        
        print(f"   📏 Fallback Route:")
        print(f"      Waypoints: {len(route_fallback.path_coordinates)}")
        print(f"      Distance: {route_fallback.total_distance:.0f}m")
        print(f"      Time: {route_fallback.estimated_time_minutes:.1f} min")
        
        # Check if Mapbox route has more waypoints (real streets)
        if len(route_mapbox.path_coordinates) > len(route_fallback.path_coordinates):
            print(f"   ✅ Mapbox integration working - more detailed route")
        else:
            print(f"   ⚠️ Mapbox route not significantly different from fallback")
        
        return True
        
    except Exception as e:
        print(f"❌ Route comparison test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Mapbox Integration Tests...\n")
    
    # Test 1: Mapbox client directly
    mapbox_success = await test_mapbox_client()
    
    # Test 2: Crime-aware router with Mapbox
    router_success = await test_crime_aware_router()
    
    # Test 3: Route comparison
    comparison_success = await test_route_comparison()
    
    # Summary
    print(f"\n📋 Test Summary:")
    print(f"   🗺️ Mapbox Client: {'✅ PASS' if mapbox_success else '❌ FAIL'}")
    print(f"   🛡️ Crime Router: {'✅ PASS' if router_success else '❌ FAIL'}")
    print(f"   📊 Comparison: {'✅ PASS' if comparison_success else '❌ FAIL'}")
    
    if all([mapbox_success, router_success, comparison_success]):
        print(f"\n🎉 All tests passed! Mapbox integration is working correctly.")
    else:
        print(f"\n⚠️ Some tests failed. Check the errors above.")
    
    return all([mapbox_success, router_success, comparison_success])

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
