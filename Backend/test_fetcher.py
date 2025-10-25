#!/usr/bin/env python3
"""
Test the updated San Francisco Police data fetcher
"""

import asyncio
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from real_time_fetcher import RealTimeFetcher
from data_sources_config import CRIME_DATA_SOURCES

async def test_fetcher():
    """Test the SF Police data fetcher"""
    
    print("Testing San Francisco Police Data Fetcher...")
    print("=" * 60)
    
    # Create fetcher instance
    fetcher = RealTimeFetcher()
    
    # Get SF Police configuration
    sf_config = CRIME_DATA_SOURCES["sf_police"]
    print(f"Source: {sf_config.name}")
    print(f"Base URL: {sf_config.base_url}")
    print()
    
    try:
        # Test fetching data
        print("Fetching data from SF Police API...")
        data = await fetcher._fetch_sf_police(sf_config)
        
        print(f"Successfully fetched {len(data)} records")
        print()
        
        if data:
            print("SAMPLE RECORDS:")
            print("=" * 40)
            
            for i, record in enumerate(data[:5]):
                print(f"\nRecord {i+1}:")
                print(f"  ID: {record.get('id', 'N/A')}")
                print(f"  Type: {record.get('type', 'N/A')}")
                print(f"  Subcategory: {record.get('subcategory', 'N/A')}")
                print(f"  Description: {record.get('description', 'N/A')}")
                print(f"  Address: {record.get('address', 'N/A')}")
                print(f"  Location: ({record.get('lat', 'N/A')}, {record.get('lng', 'N/A')})")
                print(f"  Date: {record.get('date', 'N/A')}")
                print(f"  Time: {record.get('time', 'N/A')}")
                print(f"  Police District: {record.get('police_district', 'N/A')}")
                print(f"  Neighborhood: {record.get('neighborhood', 'N/A')}")
                print(f"  Resolution: {record.get('resolution', 'N/A')}")
            
            print()
            print("DATA QUALITY ANALYSIS:")
            print("=" * 40)
            
            # Analyze data quality
            total_records = len(data)
            records_with_location = sum(1 for r in data if r.get('lat') and r.get('lng'))
            records_with_address = sum(1 for r in data if r.get('address'))
            records_with_description = sum(1 for r in data if r.get('description'))
            
            print(f"Total Records: {total_records}")
            print(f"Records with Location: {records_with_location} ({records_with_location/total_records*100:.1f}%)")
            print(f"Records with Address: {records_with_address} ({records_with_address/total_records*100:.1f}%)")
            print(f"Records with Description: {records_with_description} ({records_with_description/total_records*100:.1f}%)")
            
            # Analyze crime types
            crime_types = {}
            for record in data:
                crime_type = record.get('type', 'Unknown')
                crime_types[crime_type] = crime_types.get(crime_type, 0) + 1
            
            print()
            print("CRIME TYPES DISTRIBUTION:")
            print("=" * 40)
            for crime_type, count in sorted(crime_types.items(), key=lambda x: x[1], reverse=True)[:10]:
                percentage = (count / total_records) * 100
                print(f"  {crime_type}: {count} ({percentage:.1f}%)")
            
            # Analyze police districts
            districts = {}
            for record in data:
                district = record.get('police_district', 'Unknown')
                districts[district] = districts.get(district, 0) + 1
            
            print()
            print("POLICE DISTRICTS DISTRIBUTION:")
            print("=" * 40)
            for district, count in sorted(districts.items(), key=lambda x: x[1], reverse=True)[:10]:
                percentage = (count / total_records) * 100
                print(f"  {district}: {count} ({percentage:.1f}%)")
            
        else:
            print("No data fetched")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function"""
    print("San Francisco Police Data Fetcher Test")
    print("=" * 60)
    
    await test_fetcher()
    
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(main())
