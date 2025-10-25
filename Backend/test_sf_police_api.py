#!/usr/bin/env python3
"""
Test script for San Francisco Police API
Fetches sample data and analyzes the structure
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_sources_config import CRIME_DATA_SOURCES, API_ENDPOINTS

async def test_sf_police_api():
    """Test the San Francisco Police API and analyze data structure"""
    
    print("Testing San Francisco Police API...")
    print("=" * 50)
    
    # Get SF Police configuration
    sf_config = CRIME_DATA_SOURCES["sf_police"]
    print(f"Source: {sf_config.name}")
    print(f"Base URL: {sf_config.base_url}")
    print(f"Update Frequency: {sf_config.update_frequency} minutes")
    print(f"Rate Limit: {sf_config.rate_limit} requests/hour")
    print()
    
    # Build API URL
    url = f"{sf_config.base_url}{API_ENDPOINTS['sf_police']['incidents']}"
    print(f"API Endpoint: {url}")
    print()
    
    # Get data from last 7 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    # Build query for last 7 days
    query = f"SELECT * WHERE `incident_date` >= '{start_date.strftime('%Y-%m-%d')}' AND `incident_date` < '{end_date.strftime('%Y-%m-%d')}'"
    params = {"query": query}
    
    print(f"Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Query: {query}")
    print()
    
    try:
        async with aiohttp.ClientSession() as session:
            print("Making API request...")
            async with session.get(url, params=params) as response:
                print(f"Response Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Analyze the response structure
                    print("\n📋 API Response Analysis:")
                    print("=" * 30)
                    
                    # Check if we have data
                    if "data" in data:
                        records = data["data"]
                        print(f"📊 Total Records: {len(records)}")
                        
                        if len(records) > 0:
                            # Analyze first record structure
                            first_record = records[0]
                            print(f"📝 First Record Fields: {len(first_record)}")
                            print()
                            
                            # Show column names and sample data
                            print("🏷️  Column Analysis:")
                            print("-" * 40)
                            
                            # Get column names from meta section if available
                            columns = []
                            if "meta" in data and "view" in data["meta"] and "columns" in data["meta"]["view"]:
                                columns = [col["name"] for col in data["meta"]["view"]["columns"]]
                                print(f"📋 Column Names ({len(columns)}):")
                                for i, col in enumerate(columns):
                                    print(f"  {i:2d}. {col}")
                            else:
                                print("📋 Column Names (from data structure):")
                                for i, field in enumerate(first_record):
                                    print(f"  {i:2d}. Field_{i}: {type(field).__name__}")
                            
                            print()
                            print("📊 Sample Data (First Record):")
                            print("-" * 40)
                            
                            # Show sample data for each field
                            for i, value in enumerate(first_record[:10]):  # Show first 10 fields
                                col_name = columns[i] if i < len(columns) else f"Field_{i}"
                                print(f"  {col_name}: {value}")
                            
                            if len(first_record) > 10:
                                print(f"  ... and {len(first_record) - 10} more fields")
                            
                            print()
                            print("🔍 Data Quality Analysis:")
                            print("-" * 40)
                            
                            # Analyze data quality
                            non_null_counts = {}
                            for record in records[:100]:  # Analyze first 100 records
                                for i, value in enumerate(record):
                                    if value is not None and str(value).strip() != "":
                                        non_null_counts[i] = non_null_counts.get(i, 0) + 1
                            
                            print("📈 Non-null values per field (first 100 records):")
                            for i, count in sorted(non_null_counts.items()):
                                col_name = columns[i] if i < len(columns) else f"Field_{i}"
                                percentage = (count / min(100, len(records))) * 100
                                print(f"  {col_name}: {count}/100 ({percentage:.1f}%)")
                            
                            print()
                            print("🎯 Crime Types Found:")
                            print("-" * 40)
                            
                            # Look for crime type field (usually field 1 or 2)
                            crime_types = set()
                            for record in records[:50]:  # Check first 50 records
                                if len(record) > 1:
                                    crime_type = record[1] if record[1] else "Unknown"
                                    crime_types.add(crime_type)
                            
                            for crime_type in sorted(crime_types):
                                print(f"  • {crime_type}")
                            
                            print()
                            print("📍 Location Data Analysis:")
                            print("-" * 40)
                            
                            # Check for lat/lng fields
                            lat_count = 0
                            lng_count = 0
                            for record in records[:50]:
                                if len(record) > 4:
                                    if record[4] and str(record[4]).replace('.', '').replace('-', '').isdigit():
                                        lat_count += 1
                                    if record[5] and str(record[5]).replace('.', '').replace('-', '').isdigit():
                                        lng_count += 1
                            
                            print(f"  📍 Records with Lat: {lat_count}/50")
                            print(f"  📍 Records with Lng: {lng_count}/50")
                            
                        else:
                            print("❌ No records found in the date range")
                    else:
                        print("❌ No 'data' field in response")
                        print("📋 Response keys:", list(data.keys()))
                        
                        # Show raw response structure
                        print("\n📄 Raw Response Structure:")
                        print(json.dumps(data, indent=2)[:1000] + "...")
                
                else:
                    print(f"❌ API Error: {response.status}")
                    error_text = await response.text()
                    print(f"📄 Error Response: {error_text[:500]}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def test_data_processing():
    """Test data processing and cleaning"""
    print("\n🧹 Testing Data Processing...")
    print("=" * 50)
    
    try:
        from data_cleaner import DataCleaner
        from real_time_fetcher import RealTimeFetcher
        
        # Create test data
        test_data = [
            {
                "id": "test_1",
                "type": "ROBBERY",
                "description": "Armed robbery at store",
                "address": "123 Main St, San Francisco, CA",
                "lat": 37.7749,
                "lng": -122.4194,
                "date": "2024-01-15",
                "time": "14:30",
                "agency": "San Francisco Police Department"
            }
        ]
        
        print("📊 Test Data:")
        for record in test_data:
            print(f"  • {record['type']} at {record['address']}")
        
        # Test data cleaning
        cleaner = DataCleaner()
        cleaned_data = cleaner.clean_crime_data(test_data, "sf_police")
        
        print(f"\n✅ Cleaned {len(cleaned_data)} records")
        print("📋 Cleaned Data Sample:")
        for record in cleaned_data:
            print(f"  • {record.get('crime_type', 'Unknown')} - {record.get('description', 'No description')}")
            
    except ImportError as e:
        print(f"⚠️  Data processing modules not available: {e}")
    except Exception as e:
        print(f"❌ Data processing error: {e}")

async def main():
    """Main test function"""
    print("🚀 San Francisco Police API Test")
    print("=" * 50)
    
    # Test API connection
    await test_sf_police_api()
    
    # Test data processing
    await test_data_processing()
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(main())
