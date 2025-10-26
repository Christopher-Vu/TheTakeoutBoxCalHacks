"""
Test script for the crime-aware routing API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check ===")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return False

def test_crime_aware_route():
    """Test the crime-aware routing endpoint"""
    print("\n=== Testing Crime-Aware Route ===")

    # Sample coordinates (San Francisco area)
    params = {
        "start_lat": 37.7749,
        "start_lng": -122.4194,
        "end_lat": 37.7849,
        "end_lng": -122.4094,
        "route_type": "balanced"
    }

    print(f"Request parameters:")
    print(f"  Start: ({params['start_lat']}, {params['start_lng']})")
    print(f"  End: ({params['end_lat']}, {params['end_lng']})")
    print(f"  Type: {params['route_type']}")

    try:
        response = requests.post(
            f"{BASE_URL}/route/crime-aware",
            params=params,
            timeout=30
        )

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success! Route found:")
            print(f"  Route Type: {data.get('route_type')}")
            print(f"  Total Distance: {data.get('total_distance', 0):.2f} meters")
            print(f"  Safety Score: {data.get('total_safety_score', 0):.2f}/100")
            print(f"  Crime Penalty: {data.get('total_crime_penalty', 0):.2f}")
            print(f"  Path Points: {len(data.get('path_coordinates', []))} coordinates")
            print(f"  Segments: {len(data.get('segments', []))} route segments")

            # Show crime zone info
            crime_zones = data.get('critical_crime_zones', [])
            print(f"  Critical Crime Zones (24h): {len(crime_zones)}")

            # Show first segment details
            if data.get('segments'):
                seg = data['segments'][0]
                print(f"\n  First Segment Sample:")
                print(f"    Distance: {seg.get('distance', 0):.2f}m")
                print(f"    Safety Score: {seg.get('safety_score', 0):.2f}")
                print(f"    Crime Density: {seg.get('crime_density', 0)}")
                print(f"    24h Crimes: {seg.get('critical_crimes_24h', 0)}")

            return True
        elif response.status_code == 503:
            print(f"❌ Service Unavailable: {response.json().get('detail')}")
            return False
        else:
            print(f"❌ Error: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Request timed out (>30s)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_route_compare():
    """Test the route comparison endpoint"""
    print("\n=== Testing Route Comparison ===")

    params = {
        "start_lat": 37.7749,
        "start_lng": -122.4194,
        "end_lat": 37.7849,
        "end_lng": -122.4094
    }

    try:
        response = requests.post(
            f"{BASE_URL}/route/crime-aware/compare",
            params=params,
            timeout=60
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success! Got {len(data)} route options:")

            for route_name, route_data in data.items():
                print(f"\n  {route_name}:")
                print(f"    Distance: {route_data.get('total_distance', 0):.2f}m")
                print(f"    Safety: {route_data.get('total_safety_score', 0):.2f}/100")
                print(f"    Type: {route_data.get('route_type')}")

            return True
        else:
            print(f"❌ Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Crime-Aware Routing API Test Suite")
    print("=" * 60)

    # Run tests
    health_ok = test_health_check()

    if health_ok:
        route_ok = test_crime_aware_route()
        # compare_ok = test_route_compare()  # Uncomment to test comparison
    else:
        print("\n⚠️  Skipping route tests - health check failed")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
