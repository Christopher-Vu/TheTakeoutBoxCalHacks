#!/usr/bin/env python3
"""
Check address availability in SF Police data
"""

import requests

def check_addresses():
    r = requests.get('https://data.sfgov.org/resource/wg3w-h783.json')
    data = r.json()
    
    print("Sample addresses from first 10 records:")
    
    for i in range(min(10, len(data))):
        address = data[i].get('intersection', '')
        lat = data[i].get('latitude')
        lng = data[i].get('longitude')
        
        print(f"Record {i}:")
        print(f"  Address: '{address}'")
        print(f"  Has coordinates: {lat is not None and lng is not None}")
        print()

if __name__ == "__main__":
    check_addresses()
