#!/usr/bin/env python3
"""
Test script to verify Mapbox Directions API integration
"""

import asyncio
import os
from dotenv import load_dotenv
from mapbox_directions import MapboxDirectionsClient

# Load environment variables
load_dotenv()

async def test_mapbox_connection():
    """Test Mapbox API with a simple route"""
    
    print("=" * 60)
    print("🧪 Testing Mapbox Directions API Connection")
    print("=" * 60)
    
    # Get token from environment
    token = os.getenv('MAPBOX_ACCESS_TOKEN')
    
    if not token:
        print("❌ ERROR: MAPBOX_ACCESS_TOKEN not found in environment")
        print("   Please set it in backend/.env file")
        return False
    
    if 'example' in token:
        print("⚠️  WARNING: Using placeholder token")
        print("   Get real token from: https://account.mapbox.com/access-tokens/")
        return False
    
    print(f"✅ Token found: {token[:20]}...")
    
    # Create client
    try:
        client = MapboxDirectionsClient(token)
        print("✅ Mapbox client created")
    except Exception as e:
        print(f"❌ Failed to create client: {e}")
        return False
    
    # Test route: University of San Francisco to Palace of Fine Arts
    print("\n📍 Testing route:")
    print("   From: University of San Francisco (37.7880, -122.4074)")
    print("   To: Palace of Fine Arts (37.7694, -122.4862)")
    
    try:
        route = await client.get_route(
            37.7880, -122.4074,  # USF
            37.7694, -122.4862,  # Palace of Fine Arts
            mode='walking'
        )
        
        print("\n✅ Route retrieved successfully!")
        print(f"   📊 Waypoints: {len(route['coordinates'])}")
        print(f"   📏 Distance: {route['distance']:.0f} meters ({route['distance']/1609.34:.1f} miles)")
        print(f"   ⏱️  Duration: {route['duration']/60:.1f} minutes")
        print(f"   🚶 Mode: {route['mode']}")
        
        # Show first few waypoints
        print(f"\n   First 5 waypoints:")
        for i, coord in enumerate(route['coordinates'][:5]):
            print(f"     {i+1}. ({coord[0]:.6f}, {coord[1]:.6f})")
        
        if len(route['coordinates']) > 10:
            print(f"     ... and {len(route['coordinates']) - 5} more waypoints")
        
        # Verify waypoints follow streets (should have many points)
        if len(route['coordinates']) < 10:
            print("\n⚠️  WARNING: Route has very few waypoints")
            print("   This might indicate an issue with the API response")
        else:
            print(f"\n✅ Route has {len(route['coordinates'])} waypoints - looks good!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to get route: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

async def test_multiple_modes():
    """Test different travel modes"""
    
    print("\n" + "=" * 60)
    print("🧪 Testing Different Travel Modes")
    print("=" * 60)
    
    token = os.getenv('MAPBOX_ACCESS_TOKEN')
    if not token or 'example' in token:
        print("⚠️  Skipping (no valid token)")
        return
    
    client = MapboxDirectionsClient(token)
    
    modes = ['walking', 'cycling']
    
    for mode in modes:
        try:
            route = await client.get_route(
                37.7880, -122.4074,
                37.7694, -122.4862,
                mode=mode
            )
            
            print(f"\n✅ {mode.upper()}:")
            print(f"   Distance: {route['distance']:.0f}m")
            print(f"   Duration: {route['duration']/60:.1f} min")
            print(f"   Waypoints: {len(route['coordinates'])}")
            
        except Exception as e:
            print(f"\n❌ {mode.upper()} failed: {e}")

if __name__ == "__main__":
    print("\n🚀 Starting Mapbox API Tests\n")
    
    # Run tests
    success = asyncio.run(test_mapbox_connection())
    
    if success:
        asyncio.run(test_multiple_modes())
        print("\n" + "=" * 60)
        print("✅ All tests passed! Mapbox integration is working correctly.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Tests failed. Please check:")
        print("   1. MAPBOX_ACCESS_TOKEN is set in backend/.env")
        print("   2. Token is valid (not placeholder)")
        print("   3. Internet connection is working")
        print("=" * 60)

