#!/usr/bin/env python3
"""
Data management service for SAFEPATH
Handles data fetching, storage, and synchronization
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sf_police_storage import sf_police_storage
from database_sqlite import db_manager, DataSource, DataSyncLog

class DataManager:
    """Manages data fetching, storage, and synchronization"""
    
    def __init__(self):
        self.sf_police_storage = sf_police_storage
        self.db_manager = db_manager
        
    async def sync_all_data(self, limit: int = None) -> Dict:
        """Sync all data sources"""
        print("Starting data synchronization...")
        
        results = {
            'sf_police': await self.sync_sf_police_data(limit)
        }
        
        # Calculate totals
        total_processed = sum(r.get('records_processed', 0) for r in results.values())
        total_added = sum(r.get('records_added', 0) for r in results.values())
        total_updated = sum(r.get('records_updated', 0) for r in results.values())
        
        print(f"Data sync completed:")
        print(f"  Total processed: {total_processed}")
        print(f"  Total added: {total_added}")
        print(f"  Total updated: {total_updated}")
        
        return {
            'success': True,
            'total_processed': total_processed,
            'total_added': total_added,
            'total_updated': total_updated,
            'sources': results
        }
    
    async def sync_sf_police_data(self, limit: int = None) -> Dict:
        """Sync San Francisco Police data"""
        print("Syncing SF Police data...")
        return await self.sf_police_storage.fetch_and_store_data(limit)
    
    def get_data_statistics(self) -> Dict:
        """Get comprehensive data statistics"""
        stats = {
            'sf_police': self.sf_police_storage.get_crime_statistics()
        }
        
        # Calculate totals
        total_crimes = sum(s.get('total_crimes', 0) for s in stats.values())
        total_recent = sum(s.get('recent_crimes', 0) for s in stats.values())
        
        return {
            'total_crimes': total_crimes,
            'total_recent_crimes': total_recent,
            'sources': stats,
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def get_crimes_in_area(self, min_lat: float, max_lat: float, 
                          min_lng: float, max_lng: float) -> List[Dict]:
        """Get all crimes in a geographic area"""
        return self.sf_police_storage.get_crimes_in_bounds(min_lat, max_lat, min_lng, max_lng)
    
    def get_crimes_near_location(self, lat: float, lng: float, 
                                radius_meters: float = 100) -> List[Dict]:
        """Get crimes near a specific location"""
        return self.sf_police_storage.get_crimes_near_point(lat, lng, radius_meters)
    
    def get_crime_heatmap_data(self, min_lat: float, max_lat: float, 
                              min_lng: float, max_lng: float, 
                              grid_size: int = 50) -> List[Dict]:
        """Generate crime heatmap data for visualization"""
        crimes = self.get_crimes_in_area(min_lat, max_lat, min_lng, max_lng)
        
        # Create grid
        lat_step = (max_lat - min_lat) / grid_size
        lng_step = (max_lng - min_lng) / grid_size
        
        grid = {}
        for crime in crimes:
            if crime.get('lat') and crime.get('lng'):
                # Calculate grid cell
                grid_lat = int((crime['lat'] - min_lat) / lat_step)
                grid_lng = int((crime['lng'] - min_lng) / lng_step)
                
                if 0 <= grid_lat < grid_size and 0 <= grid_lng < grid_size:
                    key = f"{grid_lat}_{grid_lng}"
                    if key not in grid:
                        grid[key] = {
                            'lat': min_lat + (grid_lat + 0.5) * lat_step,
                            'lng': min_lng + (grid_lng + 0.5) * lng_step,
                            'count': 0,
                            'severity_sum': 0
                        }
                    
                    grid[key]['count'] += 1
                    grid[key]['severity_sum'] += crime.get('severity', 5)
        
        # Convert to list and calculate average severity
        heatmap_data = []
        for cell in grid.values():
            cell['avg_severity'] = cell['severity_sum'] / cell['count'] if cell['count'] > 0 else 0
            heatmap_data.append(cell)
        
        return heatmap_data
    
    def get_crime_trends(self, days: int = 30) -> Dict:
        """Get crime trends over time"""
        with self.db_manager.get_session() as session:
            from database_sqlite import CrimeReport
            
            # Get crimes from last N days
            start_date = datetime.utcnow() - timedelta(days=days)
            
            crimes = session.query(CrimeReport).filter(
                CrimeReport.source == 'sf_police',
                CrimeReport.occurred_at >= start_date,
                CrimeReport.is_duplicate == False
            ).all()
            
            # Group by date
            daily_counts = {}
            for crime in crimes:
                date_key = crime.occurred_at.date().isoformat()
                if date_key not in daily_counts:
                    daily_counts[date_key] = 0
                daily_counts[date_key] += 1
            
            # Group by crime type
            crime_type_counts = {}
            for crime in crimes:
                crime_type = crime.crime_type
                if crime_type not in crime_type_counts:
                    crime_type_counts[crime_type] = 0
                crime_type_counts[crime_type] += 1
            
            return {
                'daily_counts': daily_counts,
                'crime_type_counts': crime_type_counts,
                'total_crimes': len(crimes),
                'period_days': days
            }
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> Dict:
        """Clean up old data to keep database size manageable"""
        with self.db_manager.get_session() as session:
            from database_sqlite import CrimeReport
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Count records to be deleted
            old_records = session.query(CrimeReport).filter(
                CrimeReport.occurred_at < cutoff_date
            ).count()
            
            # Delete old records
            session.query(CrimeReport).filter(
                CrimeReport.occurred_at < cutoff_date
            ).delete()
            
            session.commit()
            
            return {
                'deleted_records': old_records,
                'cutoff_date': cutoff_date.isoformat(),
                'days_kept': days_to_keep
            }

# Initialize data manager
data_manager = DataManager()
