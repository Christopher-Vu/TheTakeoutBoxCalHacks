#!/usr/bin/env python3
"""
Test San Francisco Police API without authentication
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_sf_police_api_no_auth():
    """Test the San Francisco Police API without authentication"""
    
    print("Testing San Francisco Police API (No Auth)...")
    print("=" * 50)
    
    # Try different endpoints
    base_url = "https://data.sfgov.org"
    endpoints = [
        "/api/v3/views/wg3w-h783/query.json",
        "/api/views/wg3w-h783/rows.json",
        "/api/views/wg3w-h783.json"
    ]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\nTrying endpoint: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Try without any parameters first
                async with session.get(url) as response:
                    print(f"Response Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print("SUCCESS! Got data without authentication")
                        
                        # Analyze the response structure
                        print("\nAPI Response Analysis:")
                        print("=" * 30)
                        
                        # Check if we have data
                        if "data" in data:
                            records = data["data"]
                            print(f"Total Records: {len(records)}")
                            
                            if len(records) > 0:
                                # Analyze first record structure
                                first_record = records[0]
                                print(f"First Record Fields: {len(first_record)}")
                                print()
                                
                                # Show column names and sample data
                                print("Column Analysis:")
                                print("-" * 40)
                                
                                # Get column names from meta section if available
                                columns = []
                                if "meta" in data and "view" in data["meta"] and "columns" in data["meta"]["view"]:
                                    columns = [col["name"] for col in data["meta"]["view"]["columns"]]
                                    print(f"Column Names ({len(columns)}):")
                                    for i, col in enumerate(columns):
                                        print(f"  {i:2d}. {col}")
                                else:
                                    print("Column Names (from data structure):")
                                    for i, field in enumerate(first_record):
                                        print(f"  {i:2d}. Field_{i}: {type(field).__name__}")
                                
                                print()
                                print("Sample Data (First Record):")
                                print("-" * 40)
                                
                                # Show sample data for each field
                                for i, value in enumerate(first_record[:15]):  # Show first 15 fields
                                    col_name = columns[i] if i < len(columns) else f"Field_{i}"
                                    print(f"  {col_name}: {value}")
                                
                                if len(first_record) > 15:
                                    print(f"  ... and {len(first_record) - 15} more fields")
                                
                                print()
                                print("Data Quality Analysis:")
                                print("-" * 40)
                                
                                # Analyze data quality
                                non_null_counts = {}
                                for record in records[:100]:  # Analyze first 100 records
                                    for i, value in enumerate(record):
                                        if value is not None and str(value).strip() != "":
                                            non_null_counts[i] = non_null_counts.get(i, 0) + 1
                                
                                print("Non-null values per field (first 100 records):")
                                for i, count in sorted(non_null_counts.items()):
                                    col_name = columns[i] if i < len(columns) else f"Field_{i}"
                                    percentage = (count / min(100, len(records))) * 100
                                    print(f"  {col_name}: {count}/100 ({percentage:.1f}%)")
                                
                                print()
                                print("Crime Types Found:")
                                print("-" * 40)
                                
                                # Look for crime type field (usually field 1 or 2)
                                crime_types = set()
                                for record in records[:50]:  # Check first 50 records
                                    if len(record) > 1:
                                        crime_type = record[1] if record[1] else "Unknown"
                                        crime_types.add(crime_type)
                                
                                for crime_type in sorted(crime_types):
                                    print(f"  - {crime_type}")
                                
                                print()
                                print("Location Data Analysis:")
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
                                
                                print(f"  Records with Lat: {lat_count}/50")
                                print(f"  Records with Lng: {lng_count}/50")
                                
                                # Show some sample addresses
                                print()
                                print("Sample Addresses:")
                                print("-" * 40)
                                for i, record in enumerate(records[:10]):
                                    if len(record) > 3 and record[3]:
                                        print(f"  {i+1}. {record[3]}")
                                
                                return True  # Success!
                                
                            else:
                                print("No records found")
                        else:
                            print("No 'data' field in response")
                            print("Response keys:", list(data.keys()))
                            
                    else:
                        print(f"API Error: {response.status}")
                        error_text = await response.text()
                        print(f"Error Response: {error_text[:200]}")
                        
        except Exception as e:
            print(f"Error: {e}")
    
    return False

async def main():
    """Main test function"""
    print("San Francisco Police API Test (No Authentication)")
    print("=" * 60)
    
    # Test API connection
    success = await test_sf_police_api_no_auth()
    
    if success:
        print("\nSUCCESS: API is working without authentication!")
    else:
        print("\nFAILED: API requires authentication or has other issues")
    
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(main())
