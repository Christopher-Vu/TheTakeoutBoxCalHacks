#!/usr/bin/env python3
"""
Simple test for San Francisco Police data fetcher
"""

import asyncio
import aiohttp
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_sources_config import CRIME_DATA_SOURCES, API_ENDPOINTS

async def test_sf_police_fetcher():
    """Test the SF Police data fetcher directly"""
    
    print("Testing San Francisco Police Data Fetcher...")
    print("=" * 60)
    
    # Get SF Police configuration
    sf_config = CRIME_DATA_SOURCES["sf_police"]
    print(f"Source: {sf_config.name}")
    print(f"Base URL: {sf_config.base_url}")
    print()
    
    # Build API URL
    url = f"{sf_config.base_url}{API_ENDPOINTS['sf_police']['incidents']}"
    print(f"API Endpoint: {url}")
    print()
    
    try:
        async with aiohttp.ClientSession() as session:
            print("Fetching data from SF Police API...")
            async with session.get(url) as response:
                print(f"Response Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    records = data.get("data", [])
                    
                    print(f"Successfully fetched {len(records)} records")
                    print()
                    
                    if records:
                        print("SAMPLE RECORDS (First 3):")
                        print("=" * 40)
                        
                        for i, record in enumerate(records[:3]):
                            print(f"\nRecord {i+1}:")
                            print(f"  Incident ID: {record[15] if len(record) > 15 else 'N/A'}")
                            print(f"  Category: {record[22] if len(record) > 22 else 'N/A'}")
                            print(f"  Subcategory: {record[23] if len(record) > 23 else 'N/A'}")
                            print(f"  Description: {record[24] if len(record) > 24 else 'N/A'}")
                            print(f"  Address: {record[26] if len(record) > 26 else 'N/A'}")
                            print(f"  Latitude: {record[32] if len(record) > 32 else 'N/A'}")
                            print(f"  Longitude: {record[33] if len(record) > 33 else 'N/A'}")
                            print(f"  Date: {record[9] if len(record) > 9 else 'N/A'}")
                            print(f"  Time: {record[11] if len(record) > 11 else 'N/A'}")
                            print(f"  Police District: {record[28] if len(record) > 28 else 'N/A'}")
                            print(f"  Neighborhood: {record[29] if len(record) > 29 else 'N/A'}")
                            print(f"  Resolution: {record[25] if len(record) > 25 else 'N/A'}")
                        
                        print()
                        print("DATA QUALITY ANALYSIS:")
                        print("=" * 40)
                        
                        # Analyze data quality
                        total_records = len(records)
                        records_with_location = sum(1 for r in records if len(r) > 32 and r[32] and len(r) > 33 and r[33])
                        records_with_address = sum(1 for r in records if len(r) > 26 and r[26])
                        records_with_description = sum(1 for r in records if len(r) > 24 and r[24])
                        
                        print(f"Total Records: {total_records:,}")
                        print(f"Records with Location: {records_with_location:,} ({records_with_location/total_records*100:.1f}%)")
                        print(f"Records with Address: {records_with_address:,} ({records_with_address/total_records*100:.1f}%)")
                        print(f"Records with Description: {records_with_description:,} ({records_with_description/total_records*100:.1f}%)")
                        
                        # Analyze crime types
                        crime_types = {}
                        for record in records:
                            if len(record) > 22 and record[22]:
                                crime_type = record[22]
                                crime_types[crime_type] = crime_types.get(crime_type, 0) + 1
                        
                        print()
                        print("CRIME TYPES DISTRIBUTION (Top 10):")
                        print("=" * 40)
                        for crime_type, count in sorted(crime_types.items(), key=lambda x: x[1], reverse=True)[:10]:
                            percentage = (count / total_records) * 100
                            print(f"  {crime_type}: {count:,} ({percentage:.1f}%)")
                        
                        # Analyze police districts
                        districts = {}
                        for record in records:
                            if len(record) > 28 and record[28]:
                                district = record[28]
                                districts[district] = districts.get(district, 0) + 1
                        
                        print()
                        print("POLICE DISTRICTS DISTRIBUTION (Top 10):")
                        print("=" * 40)
                        for district, count in sorted(districts.items(), key=lambda x: x[1], reverse=True)[:10]:
                            percentage = (count / total_records) * 100
                            print(f"  {district}: {count:,} ({percentage:.1f}%)")
                        
                        print()
                        print("SUCCESS: SF Police API is working correctly!")
                        print("=" * 50)
                        print("FEATURES (COLUMNS) AVAILABLE:")
                        print("=" * 50)
                        print("1. Incident ID - Unique identifier")
                        print("2. Incident Category - Crime type (Assault, Burglary, etc.)")
                        print("3. Incident Subcategory - Specific crime type")
                        print("4. Incident Description - Detailed description")
                        print("5. Address/Intersection - Location information")
                        print("6. Latitude/Longitude - GPS coordinates")
                        print("7. Incident Date/Time - When crime occurred")
                        print("8. Police District - SFPD district")
                        print("9. Neighborhood - Analysis neighborhood")
                        print("10. Resolution - Case resolution status")
                        print("11. Case Number - Police case number")
                        print("12. Report Type - Type of police report")
                        print("13. Filed Online - Whether report was filed online")
                        print("14. Supervisor District - City supervisor district")
                        print("15. Data Quality - Timestamps and metadata")
                        
                    else:
                        print("No records found")
                        
                else:
                    print(f"API Error: {response.status}")
                    error_text = await response.text()
                    print(f"Error Response: {error_text[:500]}")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function"""
    print("San Francisco Police Data Fetcher Test")
    print("=" * 60)
    
    await test_sf_police_fetcher()
    
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(main())
