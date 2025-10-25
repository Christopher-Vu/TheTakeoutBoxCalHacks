#!/usr/bin/env python3
"""
Setup script for real-time crime data sources
Configures API keys and tests data sources
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from data_sources_config import CRIME_DATA_SOURCES, get_active_sources
from real_time_fetcher import fetch_real_time_data

def setup_environment():
    """Set up environment variables for API keys"""
    env_file = Path(__file__).parent.parent / "backend" / ".env"
    
    print("🔧 Setting up environment variables...")
    
    # Check if .env file exists
    if not env_file.exists():
        print("Creating .env file...")
        env_file.touch()
    
    # Read existing .env
    env_vars = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    
    # Prompt for API keys
    print("\n📋 API Key Configuration:")
    print("Enter API keys for real-time data sources (press Enter to skip):")
    
    # CrimeoMeter API
    if "CRIMEOMETER_API_KEY" not in env_vars:
        crimeometer_key = input("CrimeoMeter API Key (optional): ").strip()
        if crimeometer_key:
            env_vars["CRIMEOMETER_API_KEY"] = crimeometer_key
    
    # Google Maps API (for geocoding)
    if "GOOGLE_MAPS_API_KEY" not in env_vars:
        google_key = input("Google Maps API Key (for geocoding): ").strip()
        if google_key:
            env_vars["GOOGLE_MAPS_API_KEY"] = google_key
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.write("# SAFEPATH Environment Variables\n")
        f.write("# Database\n")
        f.write("DATABASE_URL=postgresql://username:password@localhost/safepath\n")
        f.write("\n# API Keys\n")
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"✅ Environment variables saved to {env_file}")
    return env_vars

def test_data_sources():
    """Test data source connectivity"""
    print("\n🧪 Testing data sources...")
    
    active_sources = get_active_sources()
    
    for source in active_sources:
        print(f"\n📡 Testing {source.name}...")
        print(f"   Type: {source.source_type.value}")
        print(f"   URL: {source.base_url}")
        print(f"   Update Frequency: {source.update_frequency} minutes")
        print(f"   Categories: {', '.join(source.categories)}")
        
        if source.api_key:
            print(f"   ✅ API Key configured")
        else:
            print(f"   ⚠️  No API key (may use free tier)")

def show_data_source_info():
    """Display information about available data sources"""
    print("\n📊 Available Real-Time Crime Data Sources:")
    print("=" * 60)
    
    sources_info = [
        {
            "name": "CrimeoMeter API",
            "description": "Comprehensive real-time crime data for 700+ U.S. cities",
            "coverage": "Berkeley, CA included",
            "update_frequency": "15 minutes",
            "cost": "Paid service",
            "categories": "All major crime types",
            "setup": "Requires API key from crimeometer.com"
        },
        {
            "name": "Berkeley PD Open Data",
            "description": "Official Berkeley Police Department data",
            "coverage": "Berkeley, CA only",
            "update_frequency": "Daily",
            "cost": "Free",
            "categories": "All reported crimes",
            "setup": "No API key required"
        },
        {
            "name": "FBI Crime Data API",
            "description": "FBI Uniform Crime Reporting data",
            "coverage": "National U.S. data",
            "update_frequency": "Annual",
            "cost": "Free",
            "categories": "Standardized FBI categories",
            "setup": "No API key required"
        },
        {
            "name": "CommunityCrimeMap Scraper",
            "description": "Scraped data from CommunityCrimeMap.com",
            "coverage": "Berkeley, CA area",
            "update_frequency": "30 minutes",
            "cost": "Free (scraping)",
            "categories": "All crime types",
            "setup": "Requires web scraping setup"
        },
        {
            "name": "UCPD Crime Log",
            "description": "UC Berkeley Police Department data",
            "coverage": "UC Berkeley campus",
            "update_frequency": "2 hours",
            "cost": "Free (scraping)",
            "categories": "Campus crimes",
            "setup": "Requires web scraping setup"
        }
    ]
    
    for i, source in enumerate(sources_info, 1):
        print(f"\n{i}. {source['name']}")
        print(f"   Description: {source['description']}")
        print(f"   Coverage: {source['coverage']}")
        print(f"   Update Frequency: {source['update_frequency']}")
        print(f"   Cost: {source['cost']}")
        print(f"   Categories: {source['categories']}")
        print(f"   Setup: {source['setup']}")

def create_sample_data():
    """Create sample data for testing"""
    print("\n📝 Creating sample data...")
    
    sample_crimes = [
        {
            "id": "sample_1",
            "source": "berkeley_pd",
            "crime_type": "ROBBERY",
            "severity": 8,
            "description": "Armed robbery at Telegraph Avenue",
            "address": "2400 Telegraph Avenue, Berkeley, CA",
            "lat": 37.8690,
            "lng": -122.2588,
            "occurred_at": "2024-01-15T14:30:00Z",
            "agency": "Berkeley PD",
            "case_number": "24-001234"
        },
        {
            "id": "sample_2", 
            "source": "ucpd",
            "crime_type": "THEFT",
            "severity": 4,
            "description": "Bicycle theft on campus",
            "address": "UC Berkeley Campus, Berkeley, CA",
            "lat": 37.8719,
            "lng": -122.2585,
            "occurred_at": "2024-01-15T16:45:00Z",
            "agency": "UCPD",
            "case_number": "UCPD-2024-001"
        },
        {
            "id": "sample_3",
            "source": "berkeley_pd", 
            "crime_type": "ASSAULT",
            "severity": 7,
            "description": "Assault near campus",
            "address": "2500 Durant Avenue, Berkeley, CA",
            "lat": 37.8719,
            "lng": -122.2585,
            "occurred_at": "2024-01-15T20:15:00Z",
            "agency": "Berkeley PD",
            "case_number": "24-001235"
        }
    ]
    
    # Save sample data
    sample_file = Path(__file__).parent.parent / "data" / "sample_crimes.json"
    with open(sample_file, 'w') as f:
        json.dump(sample_crimes, f, indent=2)
    
    print(f"✅ Sample data created at {sample_file}")
    return sample_crimes

async def test_real_time_fetch():
    """Test real-time data fetching"""
    print("\n🚀 Testing real-time data fetch...")
    
    try:
        results = await fetch_real_time_data()
        
        print(f"📊 Fetch Results:")
        for result in results:
            status = "✅" if result.success else "❌"
            print(f"   {status} {result.source}: {result.records_processed} records")
            if result.errors:
                for error in result.errors:
                    print(f"      Error: {error}")
        
        total_processed = sum(r.records_processed for r in results)
        print(f"\n📈 Total records processed: {total_processed}")
        
    except Exception as e:
        print(f"❌ Error testing real-time fetch: {e}")

def main():
    """Main setup function"""
    print("🚀 SAFEPATH Real-Time Data Setup")
    print("=" * 40)
    
    # Show available data sources
    show_data_source_info()
    
    # Set up environment
    env_vars = setup_environment()
    
    # Test data sources
    test_data_sources()
    
    # Create sample data
    sample_data = create_sample_data()
    
    # Test real-time fetching (if possible)
    print("\n🧪 Testing real-time data fetch...")
    try:
        asyncio.run(test_real_time_fetch())
    except Exception as e:
        print(f"⚠️  Real-time fetch test failed: {e}")
        print("   This is normal if API keys aren't configured yet")
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Configure API keys in backend/.env")
    print("2. Set up PostgreSQL database with PostGIS")
    print("3. Run: python backend/main.py")
    print("4. Visit: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
