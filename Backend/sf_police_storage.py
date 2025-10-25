#!/usr/bin/env python3
"""
San Francisco Police data storage service
Handles storing and retrieving SF Police crime data
"""

import asyncio
import aiohttp
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_sqlite import db_manager, CrimeReport, DataSource, DataSyncLog
from data_sources_config import CRIME_DATA_SOURCES, API_ENDPOINTS

class SFPoliceStorage:
    """Handles storage and retrieval of San Francisco Police crime data"""
    
    def __init__(self):
        self.db_manager = db_manager
        self.source_id = "sf_police"
        self.agency = "San Francisco Police Department"
        
    async def fetch_and_store_data(self, limit: int = None) -> Dict:
        """Fetch data from SF Police API and store in database"""
        print("Starting SF Police data fetch and storage...")
        
        # Create sync log
        sync_id = str(uuid.uuid4())
        sync_log = DataSyncLog(
            id=sync_id,
            source_id=self.source_id,
            sync_started=datetime.utcnow(),
            status='running'
        )
        
        try:
            # Fetch data from API
            print("Fetching data from SF Police API...")
            raw_data = await self._fetch_sf_police_data(limit)
            print(f"Fetched {len(raw_data)} records from API")
            
            # Process and store data
            print("Processing and storing data...")
            results = await self._process_and_store_data(raw_data, sync_id)
            
            # Update sync log
            sync_log.sync_completed = datetime.utcnow()
            sync_log.records_processed = len(raw_data)
            sync_log.records_added = results['added']
            sync_log.records_updated = results['updated']
            sync_log.records_duplicated = results['duplicates']
            sync_log.status = 'success'
            
            print(f"Storage completed: {results['added']} added, {results['updated']} updated, {results['duplicates']} duplicates")
            
            return {
                'success': True,
                'records_processed': len(raw_data),
                'records_added': results['added'],
                'records_updated': results['updated'],
                'records_duplicated': results['duplicates'],
                'sync_id': sync_id
            }
            
        except Exception as e:
            print(f"Error during data fetch and storage: {e}")
            sync_log.sync_completed = datetime.utcnow()
            sync_log.status = 'failed'
            sync_log.errors = [str(e)]
            
            return {
                'success': False,
                'error': str(e),
                'sync_id': sync_id
            }
    
    async def _fetch_sf_police_data(self, limit: int = None) -> List[Dict]:
        """Fetch raw data from SF Police API"""
        url = f"https://data.sfgov.org{API_ENDPOINTS['sf_police']['incidents']}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    records = data.get("data", [])
                    
                    if limit:
                        records = records[:limit]
                    
                    return records
                else:
                    raise Exception(f"API request failed with status {response.status}")
    
    async def _process_and_store_data(self, raw_data: List[Dict], sync_id: str) -> Dict:
        """Process raw data and store in database"""
        added = 0
        updated = 0
        duplicates = 0
        
        with self.db_manager.get_session() as session:
            for record in raw_data:
                try:
                    # Process the record
                    processed_record = self._process_sf_police_record(record)
                    
                    if processed_record:
                        # Check if record already exists by ID
                        existing = session.query(CrimeReport).filter(
                            CrimeReport.id == processed_record['id']
                        ).first()
                        
                        if existing:
                            # Update existing record
                            self._update_crime_report(existing, processed_record)
                            updated += 1
                        else:
                            # Add new record
                            crime_report = CrimeReport(**processed_record)
                            session.add(crime_report)
                            added += 1
                            
                except Exception as e:
                    print(f"Error processing record: {e}")
                    continue
            
            try:
                session.commit()
            except Exception as e:
                print(f"Error committing to database: {e}")
                session.rollback()
                # Try to handle duplicates by updating instead of inserting
                for record in raw_data:
                    try:
                        processed_record = self._process_sf_police_record(record)
                        if processed_record:
                            existing = session.query(CrimeReport).filter(
                                CrimeReport.id == processed_record['id']
                            ).first()
                            
                            if existing:
                                self._update_crime_report(existing, processed_record)
                                updated += 1
                            else:
                                # Try to insert with a different ID
                                processed_record['id'] = f"{processed_record['id']}_{added}"
                                crime_report = CrimeReport(**processed_record)
                                session.add(crime_report)
                                added += 1
                    except:
                        continue
                
                session.commit()
        
        return {
            'added': added,
            'updated': updated,
            'duplicates': duplicates
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
    
    def _update_crime_report(self, existing: CrimeReport, new_data: Dict):
        """Update existing crime report with new data"""
        existing.crime_type = new_data['crime_type']
        existing.severity = new_data['severity']
        existing.description = new_data['description']
        existing.address = new_data['address']
        existing.lat = new_data['lat']
        existing.lng = new_data['lng']
        existing.occurred_at = new_data['occurred_at']
        existing.raw_data = new_data['raw_data']
        existing.tags = new_data['tags']
        existing.updated_at = datetime.utcnow()
    
    def get_crimes_in_bounds(self, min_lat: float, max_lat: float, 
                           min_lng: float, max_lng: float) -> List[Dict]:
        """Get SF Police crimes within geographic bounds"""
        return self.db_manager.get_crimes_in_bounds(min_lat, max_lat, min_lng, max_lng)
    
    def get_crimes_near_point(self, lat: float, lng: float, radius_meters: float = 100) -> List[Dict]:
        """Get SF Police crimes near a point"""
        return self.db_manager.get_crimes_near_point(lat, lng, radius_meters)
    
    def get_crime_statistics(self) -> Dict:
        """Get statistics about stored SF Police data"""
        with self.db_manager.get_session() as session:
            # Total crimes
            total_crimes = session.query(CrimeReport).filter(
                CrimeReport.source == self.source_id,
                CrimeReport.is_duplicate == False
            ).count()
            
            # Crimes by type
            crime_types = {}
            for crime in session.query(CrimeReport).filter(
                CrimeReport.source == self.source_id,
                CrimeReport.is_duplicate == False
            ).all():
                crime_type = crime.crime_type
                crime_types[crime_type] = crime_types.get(crime_type, 0) + 1
            
            # Recent crimes (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_crimes = session.query(CrimeReport).filter(
                CrimeReport.source == self.source_id,
                CrimeReport.is_duplicate == False,
                CrimeReport.occurred_at >= thirty_days_ago
            ).count()
            
            return {
                'total_crimes': total_crimes,
                'recent_crimes': recent_crimes,
                'crime_types': crime_types,
                'last_updated': datetime.utcnow().isoformat()
            }

# Initialize storage service
sf_police_storage = SFPoliceStorage()
