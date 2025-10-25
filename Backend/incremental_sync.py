#!/usr/bin/env python3
"""
Incremental data synchronization for SAFEPATH
Only fetches new records that aren't already in the database
"""

import asyncio
import aiohttp
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_sqlite import db_manager, CrimeReport
from data_sources_config import API_ENDPOINTS

class IncrementalSync:
    """Handles incremental data synchronization"""
    
    def __init__(self):
        self.db_manager = db_manager
        self.source_id = "sf_police"
        self.agency = "San Francisco Police Department"
        
    async def sync_new_data(self) -> Dict:
        """Sync only new data that isn't already in the database"""
        print("Starting incremental data sync...")
        print("=" * 50)
        
        try:
            # Get existing record IDs to avoid duplicates
            existing_ids = self._get_existing_record_ids()
            print(f"Existing records in database: {len(existing_ids)}")
            
            # Fetch recent data from API (last 7 days to catch any updates)
            recent_data = await self._fetch_recent_data()
            print(f"Fetched {len(recent_data)} records from API")
            
            # Filter out records that already exist
            new_records = self._filter_new_records(recent_data, existing_ids)
            print(f"New records to add: {len(new_records)}")
            
            if not new_records:
                print("No new records found. Database is up to date!")
                return {
                    'success': True,
                    'records_processed': len(recent_data),
                    'records_added': 0,
                    'records_skipped': len(recent_data),
                    'message': 'No new data available'
                }
            
            # Process and store new records
            results = await self._process_and_store_new_records(new_records)
            
            print(f"Sync completed:")
            print(f"  Records processed: {len(recent_data)}")
            print(f"  New records added: {results['added']}")
            print(f"  Records skipped (already exist): {len(recent_data) - len(new_records)}")
            
            return {
                'success': True,
                'records_processed': len(recent_data),
                'records_added': results['added'],
                'records_skipped': len(recent_data) - len(new_records),
                'new_records': new_records[:5] if new_records else []  # Show first 5 new records
            }
            
        except Exception as e:
            print(f"Error during incremental sync: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_existing_record_ids(self) -> Set[str]:
        """Get all existing record IDs from the database"""
        with self.db_manager.get_session() as session:
            existing_records = session.query(CrimeReport).filter(
                CrimeReport.source == self.source_id
            ).all()
            
            # Return set of source IDs for quick lookup
            return {record.source_id for record in existing_records}
    
    async def _fetch_recent_data(self, days_back: int = 7) -> List[Dict]:
        """Fetch recent data from SF Police API"""
        url = f"https://data.sfgov.org{API_ENDPOINTS['sf_police']['incidents']}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    records = data.get("data", [])
                    
                    # Filter to recent records only
                    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                    recent_records = []
                    
                    for record in records:
                        if len(record) >= 35:
                            try:
                                # Parse incident datetime
                                incident_datetime = record[9]  # Incident Datetime
                                if incident_datetime:
                                    record_date = datetime.fromisoformat(
                                        incident_datetime.replace('T', ' ').replace('Z', '')
                                    )
                                    if record_date >= cutoff_date:
                                        recent_records.append(record)
                            except:
                                # If date parsing fails, include the record anyway
                                recent_records.append(record)
                    
                    return recent_records
                else:
                    raise Exception(f"API request failed with status {response.status}")
    
    def _filter_new_records(self, api_records: List[Dict], existing_ids: Set[str]) -> List[Dict]:
        """Filter out records that already exist in the database"""
        new_records = []
        
        for record in api_records:
            if len(record) >= 35:
                incident_id = record[15] if record[15] else None  # Incident ID
                if incident_id and str(incident_id) not in existing_ids:
                    new_records.append(record)
        
        return new_records
    
    async def _process_and_store_new_records(self, new_records: List[Dict]) -> Dict:
        """Process and store only new records"""
        added = 0
        errors = 0
        
        with self.db_manager.get_session() as session:
            for record in new_records:
                try:
                    # Process the record
                    processed_record = self._process_sf_police_record(record)
                    
                    if processed_record:
                        # Add new record
                        crime_report = CrimeReport(**processed_record)
                        session.add(crime_report)
                        added += 1
                        
                except Exception as e:
                    print(f"Error processing record: {e}")
                    errors += 1
                    continue
            
            try:
                session.commit()
            except Exception as e:
                print(f"Error committing to database: {e}")
                session.rollback()
                return {'added': 0, 'errors': len(new_records)}
        
        return {
            'added': added,
            'errors': errors
        }
    
    def _process_sf_police_record(self, record: List) -> Optional[Dict]:
        """Process a single SF Police record into our database format"""
        try:
            if len(record) < 35:
                return None
            
            # Extract fields based on our analysis
            incident_id = record[15] if record[15] else None
            if not incident_id:
                return None
            
            # Parse datetime
            occurred_at = None
            if record[9]:  # Incident Datetime
                try:
                    occurred_at = datetime.fromisoformat(record[9].replace('T', ' ').replace('Z', ''))
                except:
                    occurred_at = datetime.utcnow()
            
            # Parse coordinates
            lat = None
            lng = None
            if record[32] and record[33]:  # Latitude and Longitude
                try:
                    lat = float(record[32])
                    lng = float(record[33])
                except:
                    pass
            
            # Determine severity based on crime type
            severity = self._calculate_severity(record[22], record[23])  # Category and Subcategory
            
            # Create processed record
            processed_record = {
                'id': f"sf_{incident_id}",
                'source_id': str(incident_id),
                'source': self.source_id,
                'crime_type': record[22] if record[22] else 'Unknown',
                'severity': severity,
                'description': record[24] if record[24] else '',
                'address': record[26] if record[26] else '',
                'lat': lat,
                'lng': lng,
                'block_address': record[26] if record[26] else '',
                'occurred_at': occurred_at or datetime.utcnow(),
                'reported_at': occurred_at or datetime.utcnow(),
                'agency': self.agency,
                'case_number': record[16] if record[16] else None,
                'is_duplicate': False,
                'confidence_score': 0.9,  # High confidence for official police data
                'raw_data': {
                    'incident_id': incident_id,
                    'category': record[22],
                    'subcategory': record[23],
                    'description': record[24],
                    'address': record[26],
                    'police_district': record[28],
                    'neighborhood': record[29],
                    'resolution': record[25],
                    'incident_datetime': record[9],
                    'incident_time': record[11],
                    'latitude': record[32],
                    'longitude': record[33]
                },
                'tags': {
                    'police_district': record[28] if record[28] else None,
                    'neighborhood': record[29] if record[29] else None,
                    'resolution': record[25] if record[25] else None,
                    'subcategory': record[23] if record[23] else None
                }
            }
            
            return processed_record
            
        except Exception as e:
            print(f"Error processing SF Police record: {e}")
            return None
    
    def _calculate_severity(self, category: str, subcategory: str) -> int:
        """Calculate severity score (1-10) based on crime type"""
        if not category:
            return 5
        
        # High severity crimes
        if category in ['Homicide', 'Rape', 'Robbery']:
            return 9
        elif category in ['Assault'] and subcategory and 'Aggravated' in subcategory:
            return 8
        elif category in ['Burglary']:
            return 7
        elif category in ['Motor Vehicle Theft']:
            return 6
        elif category in ['Larceny Theft']:
            return 4
        elif category in ['Vandalism', 'Malicious Mischief']:
            return 3
        elif category in ['Drug Offense', 'Drug Violation']:
            return 5
        elif category in ['Fraud']:
            return 4
        elif category in ['Non-Criminal', 'Lost Property', 'Recovered Vehicle']:
            return 1
        else:
            return 5  # Default medium severity
    
    def get_sync_statistics(self) -> Dict:
        """Get statistics about the last sync"""
        with self.db_manager.get_session() as session:
            total_records = session.query(CrimeReport).filter(
                CrimeReport.source == self.source_id
            ).count()
            
            # Get records added in last 24 hours
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            recent_records = session.query(CrimeReport).filter(
                CrimeReport.source == self.source_id,
                CrimeReport.created_at >= twenty_four_hours_ago
            ).count()
            
            # Get oldest and newest records
            oldest = session.query(CrimeReport).filter(
                CrimeReport.source == self.source_id
            ).order_by(CrimeReport.occurred_at.asc()).first()
            
            newest = session.query(CrimeReport).filter(
                CrimeReport.source == self.source_id
            ).order_by(CrimeReport.occurred_at.desc()).first()
            
            return {
                'total_records': total_records,
                'recent_records_24h': recent_records,
                'oldest_record': oldest.occurred_at.isoformat() if oldest else None,
                'newest_record': newest.occurred_at.isoformat() if newest else None,
                'last_sync': datetime.utcnow().isoformat()
            }

# Initialize incremental sync
incremental_sync = IncrementalSync()
