#!/usr/bin/env python3
"""
Analyze San Francisco Police crime data structure
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def analyze_crime_data():
    """Analyze the San Francisco Police crime data structure"""
    
    print("Analyzing San Francisco Police Crime Data...")
    print("=" * 60)
    
    # Use the working endpoint
    url = "https://data.sfgov.org/api/views/wg3w-h783/rows.json"
    
    try:
        async with aiohttp.ClientSession() as session:
            print("Fetching crime data...")
            async with session.get(url) as response:
                print(f"Response Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Get the data
                    records = data["data"]
                    print(f"Total Records: {len(records)}")
                    print()
                    
                    # Get column names
                    columns = []
                    if "meta" in data and "view" in data["meta"] and "columns" in data["meta"]["view"]:
                        columns = [col["name"] for col in data["meta"]["view"]["columns"]]
                    
                    print("CRIME DATA FEATURES (COLUMNS):")
                    print("=" * 50)
                    for i, col in enumerate(columns):
                        print(f"{i:2d}. {col}")
                    print()
                    
                    # Analyze crime categories
                    print("CRIME CATEGORIES ANALYSIS:")
                    print("=" * 40)
                    
                    # Get unique crime categories
                    crime_categories = set()
                    crime_subcategories = set()
                    crime_descriptions = set()
                    
                    for record in records[:1000]:  # Analyze first 1000 records
                        if len(record) > 22:  # Incident Category is field 22
                            category = record[22] if record[22] else "Unknown"
                            crime_categories.add(category)
                        
                        if len(record) > 23:  # Incident Subcategory is field 23
                            subcategory = record[23] if record[23] else "Unknown"
                            crime_subcategories.add(subcategory)
                        
                        if len(record) > 24:  # Incident Description is field 24
                            description = record[24] if record[24] else "Unknown"
                            crime_descriptions.add(description)
                    
                    print("CRIME CATEGORIES:")
                    for category in sorted(crime_categories):
                        print(f"  - {category}")
                    print()
                    
                    print("CRIME SUBCATEGORIES:")
                    for subcategory in sorted(crime_subcategories):
                        print(f"  - {subcategory}")
                    print()
                    
                    print("SAMPLE CRIME DESCRIPTIONS:")
                    for i, description in enumerate(sorted(crime_descriptions)[:20]):
                        print(f"  {i+1:2d}. {description}")
                    if len(crime_descriptions) > 20:
                        print(f"  ... and {len(crime_descriptions) - 20} more descriptions")
                    print()
                    
                    # Analyze location data
                    print("LOCATION DATA ANALYSIS:")
                    print("=" * 40)
                    
                    lat_count = 0
                    lng_count = 0
                    address_count = 0
                    
                    for record in records[:1000]:
                        if len(record) > 31:  # Latitude is field 31
                            if record[31] and str(record[31]).replace('.', '').replace('-', '').isdigit():
                                lat_count += 1
                        
                        if len(record) > 32:  # Longitude is field 32
                            if record[32] and str(record[32]).replace('.', '').replace('-', '').isdigit():
                                lng_count += 1
                        
                        if len(record) > 26:  # Intersection is field 26
                            if record[26] and str(record[26]).strip():
                                address_count += 1
                    
                    print(f"Records with Latitude: {lat_count}/1000")
                    print(f"Records with Longitude: {lng_count}/1000")
                    print(f"Records with Address: {address_count}/1000")
                    print()
                    
                    # Show sample records
                    print("SAMPLE CRIME RECORDS:")
                    print("=" * 40)
                    
                    for i, record in enumerate(records[:5]):
                        print(f"\nRecord {i+1}:")
                        print(f"  Incident ID: {record[15] if len(record) > 15 else 'N/A'}")
                        print(f"  Date: {record[9] if len(record) > 9 else 'N/A'}")
                        print(f"  Time: {record[10] if len(record) > 10 else 'N/A'}")
                        print(f"  Category: {record[22] if len(record) > 22 else 'N/A'}")
                        print(f"  Subcategory: {record[23] if len(record) > 23 else 'N/A'}")
                        print(f"  Description: {record[24] if len(record) > 24 else 'N/A'}")
                        print(f"  Address: {record[26] if len(record) > 26 else 'N/A'}")
                        print(f"  Latitude: {record[31] if len(record) > 31 else 'N/A'}")
                        print(f"  Longitude: {record[32] if len(record) > 32 else 'N/A'}")
                        print(f"  Police District: {record[28] if len(record) > 28 else 'N/A'}")
                        print(f"  Neighborhood: {record[29] if len(record) > 29 else 'N/A'}")
                    
                    print()
                    print("DATA QUALITY SUMMARY:")
                    print("=" * 40)
                    print(f"Total Records: {len(records):,}")
                    print(f"Records with Location: {lat_count:,} ({lat_count/1000*100:.1f}%)")
                    print(f"Records with Address: {address_count:,} ({address_count/1000*100:.1f}%)")
                    print(f"Unique Categories: {len(crime_categories)}")
                    print(f"Unique Subcategories: {len(crime_subcategories)}")
                    print(f"Unique Descriptions: {len(crime_descriptions)}")
                    
                else:
                    print(f"API Error: {response.status}")
                    error_text = await response.text()
                    print(f"Error Response: {error_text[:500]}")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main analysis function"""
    print("San Francisco Police Crime Data Analysis")
    print("=" * 60)
    
    await analyze_crime_data()
    
    print("\nAnalysis completed!")

if __name__ == "__main__":
    asyncio.run(main())
