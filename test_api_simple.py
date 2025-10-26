"""
Simple API test using only built-in Python modules
"""
import urllib.request
import urllib.parse
import json

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check ===")
    try:
        req = urllib.request.Request(f"{BASE_URL}/")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            print(f"✅ Status: {response.status}")
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
    except urllib.error.URLError as e:
        print(f"❌ Connection Error: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_crime_aware_route():
    """Test the crime-aware routing endpoint"""
    print("\n=== Testing Crime-Aware Route ===")

    # Sample coordinates (San Francisco area)
    params = {
        "start_lat": "37.7749",
        "start_lng": "-122.4194",
        "end_lat": "37.7849",
        "end_lng": "-122.4094",
        "route_type": "balanced"
    }

    print(f"Request parameters:")
    print(f"  Start: ({params['start_lat']}, {params['start_lng']})")
    print(f"  End: ({params['end_lat']}, {params['end_lng']})")
    print(f"  Type: {params['route_type']}")

    query_string = urllib.parse.urlencode(params)
    url = f"{BASE_URL}/route/crime-aware?{query_string}"

    try:
        req = urllib.request.Request(url, method='POST')
        print(f"\nSending POST request to: {url}")

        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())

            print(f"\n✅ Status: {response.status}")
            print(f"\nRoute found:")
            print(f"  Route Type: {data.get('route_type')}")
            print(f"  Total Distance: {data.get('total_distance', 0):.2f} meters")
            print(f"  Safety Score: {data.get('total_safety_score', 0):.2f}/100")
            print(f"  Crime Penalty: {data.get('total_crime_penalty', 0):.2f}")
            print(f"  Path Points: {len(data.get('path_coordinates', []))} coordinates")
            print(f"  Segments: {len(data.get('segments', []))} route segments")

            # Show crime zone info
            crime_zones = data.get('critical_crime_zones', [])
            print(f"  Critical Crime Zones (24h): {len(crime_zones)}")

            if crime_zones:
                print(f"\n  Sample Crime Zone:")
                zone = crime_zones[0]
                print(f"    Location: ({zone.get('lat')}, {zone.get('lng')})")
                print(f"    Type: {zone.get('crime_type')}")
                print(f"    Severity: {zone.get('severity')}/10")
                print(f"    Hours Ago: {zone.get('hours_ago'):.1f}")

            # Show first segment details
            if data.get('segments'):
                seg = data['segments'][0]
                print(f"\n  First Segment Details:")
                print(f"    Distance: {seg.get('distance', 0):.2f}m")
                print(f"    Safety Score: {seg.get('safety_score', 0):.2f}/100")
                print(f"    Crime Density: {seg.get('crime_density', 0)}")
                print(f"    24h Crimes: {seg.get('critical_crimes_24h', 0)}")
                print(f"    Recent Crimes: {seg.get('recent_crimes', 0)}")

            # Show safety breakdown
            if data.get('route_safety_breakdown'):
                breakdown = data['route_safety_breakdown']
                print(f"\n  Safety Breakdown:")
                print(f"    24h Crimes Encountered: {breakdown.get('24h_crimes_avoided', 0)}")
                print(f"    High Severity Crimes: {breakdown.get('high_severity_crimes_avoided', 0)}")
                print(f"    Average Crime Density: {breakdown.get('average_crime_density', 0):.2f}")

                summary = breakdown.get('route_safety_summary', {})
                print(f"    Safety Grade: {summary.get('safety_grade', 'N/A')}")

            return True

    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        error_body = e.read().decode()
        try:
            error_data = json.loads(error_body)
            print(f"   Detail: {error_data.get('detail', error_body)}")
        except:
            print(f"   Body: {error_body}")
        return False
    except urllib.error.URLError as e:
        print(f"❌ Connection Error: {e.reason}")
        print("   Is the backend server running?")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print(" Crime-Aware Routing API Test Suite")
    print("=" * 70)

    # Run tests
    health_ok = test_health_check()

    if health_ok:
        print("\n" + "-" * 70)
        route_ok = test_crime_aware_route()
    else:
        print("\n⚠️  Skipping route tests - health check failed")
        print("   The server may not be running or the database may not be connected")

    print("\n" + "=" * 70)
    print(" Test Complete")
    print("=" * 70)
