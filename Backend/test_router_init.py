#!/usr/bin/env python3
"""
Test script to debug CrimeAwareRouter initialization
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_router_initialization():
    """Test CrimeAwareRouter initialization with different databases"""
    
    print("=" * 60)
    print("🧪 Testing CrimeAwareRouter Initialization")
    print("=" * 60)
    
    # Test 1: Try SQLite
    print("\n1. Testing SQLite database...")
    try:
        from crime_aware_router import CrimeAwareRouter
        sqlite_url = "sqlite:///./safepath.db"
        mapbox_token = os.getenv('MAPBOX_ACCESS_TOKEN')
        
        print(f"   Database URL: {sqlite_url}")
        print(f"   Mapbox token: {mapbox_token[:20] if mapbox_token else 'None'}...")
        
        router = CrimeAwareRouter(sqlite_url, mapbox_token=mapbox_token)
        print("   ✅ SQLite CrimeAwareRouter created successfully!")
        
        # Test if we can query the database
        print("   Testing database query...")
        from sqlalchemy import text
        with router.engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as count FROM crimes LIMIT 1"))
            count = result.fetchone()[0]
            print(f"   ✅ Database query successful! Found {count} crimes")
        
        return True
        
    except Exception as e:
        print(f"   ❌ SQLite test failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def test_mapbox_client():
    """Test Mapbox client separately"""
    
    print("\n2. Testing Mapbox client...")
    try:
        from mapbox_directions import MapboxDirectionsClient
        token = os.getenv('MAPBOX_ACCESS_TOKEN')
        
        if not token:
            print("   ⚠️ No Mapbox token found")
            return False
            
        client = MapboxDirectionsClient(token)
        print("   ✅ Mapbox client created successfully!")
        return True
        
    except Exception as e:
        print(f"   ❌ Mapbox client test failed: {e}")
        return False

def test_database_connection():
    """Test database connection directly"""
    
    print("\n3. Testing database connection...")
    try:
        from sqlalchemy import create_engine, text
        sqlite_url = "sqlite:///./safepath.db"
        
        engine = create_engine(sqlite_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as count FROM crimes"))
            count = result.fetchone()[0]
            print(f"   ✅ Database connection successful! Found {count} crimes")
            return True
            
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("\n🚀 Starting CrimeAwareRouter Debug Tests\n")
    
    # Run tests
    db_test = test_database_connection()
    mapbox_test = test_mapbox_client()
    router_test = test_router_initialization()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   Database Connection: {'✅ PASS' if db_test else '❌ FAIL'}")
    print(f"   Mapbox Client: {'✅ PASS' if mapbox_test else '❌ FAIL'}")
    print(f"   Router Initialization: {'✅ PASS' if router_test else '❌ FAIL'}")
    print("=" * 60)
    
    if all([db_test, mapbox_test, router_test]):
        print("🎉 All tests passed! CrimeAwareRouter should work.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
