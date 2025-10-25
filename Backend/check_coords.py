#!/usr/bin/env python3
"""
Check coordinate availability in SF Police data
"""

import requests

def check_coordinates():
    r = requests.get('https://data.sfgov.org/resource/wg3w-h783.json')
    data = r.json()
    
    print(f"Total records: {len(data)}")
    print("\nChecking first 10 records for coordinates:")
    
    missing_coords = 0
    has_coords = 0
    
    for i in range(min(10, len(data))):
        lat = data[i].get('latitude')
        lng = data[i].get('longitude')
        
        if lat and lng:
            has_coords += 1
            print(f"Record {i}: ✅ lat={lat}, lng={lng}")
        else:
            missing_coords += 1
            print(f"Record {i}: ❌ lat={lat}, lng={lng}")
    
    print(f"\nSummary:")
    print(f"Records with coordinates: {has_coords}/10")
    print(f"Records missing coordinates: {missing_coords}/10")
    
    # Check overall percentage
    total_with_coords = sum(1 for record in data if record.get('latitude') and record.get('longitude'))
    print(f"\nOverall: {total_with_coords}/{len(data)} records have coordinates ({total_with_coords/len(data)*100:.1f}%)")

if __name__ == "__main__":
    check_coordinates()
