#!/usr/bin/env python3
"""
Database maintenance utilities for SAFEPATH
Handles data cleanup, filtering, and optimization
"""

import sys
import os
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_sqlite import db_manager, CrimeReport

class DatabaseMaintenance:
    """Handles database maintenance operations"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    def filter_by_date_range(self, days_to_keep: int = 365):
        """Filter database to keep only records within specified days"""
        print(f"Filtering database to keep last {days_to_keep} days...")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        with self.db_manager.get_session() as session:
            # Count records to be deleted
            old_records = session.query(CrimeReport).filter(
                CrimeReport.occurred_at < cutoff_date
            ).count()
            
            if old_records == 0:
                print("No old records found. Database is already up to date!")
                return {
                    'deleted': 0,
                    'remaining': session.query(CrimeReport).count(),
                    'cutoff_date': cutoff_date.isoformat()
                }
            
            # Delete old records
            deleted_count = session.query(CrimeReport).filter(
                CrimeReport.occurred_at < cutoff_date
            ).delete()
            
            session.commit()
            
            remaining = session.query(CrimeReport).count()
            
            print(f"Deleted {deleted_count} old records")
            print(f"Remaining records: {remaining}")
            
            return {
                'deleted': deleted_count,
                'remaining': remaining,
                'cutoff_date': cutoff_date.isoformat()
            }
    
    def remove_duplicates(self):
        """Remove duplicate records based on source_id and source"""
        print("Removing duplicate records...")
        
        with self.db_manager.get_session() as session:
            # Find duplicates
            duplicates = session.query(CrimeReport).filter(
                CrimeReport.is_duplicate == True
            ).all()
            
            duplicate_count = len(duplicates)
            
            if duplicate_count == 0:
                print("No duplicate records found.")
                return {'removed': 0}
            
            # Delete duplicates
            session.query(CrimeReport).filter(
                CrimeReport.is_duplicate == True
            ).delete()
            
            session.commit()
            
            print(f"Removed {duplicate_count} duplicate records")
            
            return {'removed': duplicate_count}
    
    def clean_invalid_data(self):
        """Remove records with invalid or missing critical data"""
        print("Cleaning invalid data...")
        
        with self.db_manager.get_session() as session:
            # Remove records with missing critical data
            invalid_records = session.query(CrimeReport).filter(
                CrimeReport.occurred_at.is_(None)
            ).count()
            
            if invalid_records > 0:
                session.query(CrimeReport).filter(
                    CrimeReport.occurred_at.is_(None)
                ).delete()
                session.commit()
                print(f"Removed {invalid_records} records with missing dates")
            
            return {'cleaned': invalid_records}
    
    def optimize_database(self):
        """Optimize database by running VACUUM and ANALYZE"""
        print("Optimizing database...")
        
        with self.db_manager.get_session() as session:
            from sqlalchemy import text
            # SQLite VACUUM to reclaim space
            session.execute(text("VACUUM"))
            session.execute(text("ANALYZE"))
            session.commit()
            
            print("Database optimization completed")
    
    def get_database_stats(self):
        """Get comprehensive database statistics"""
        with self.db_manager.get_session() as session:
            total_records = session.query(CrimeReport).count()
            
            if total_records == 0:
                return {
                    'total_records': 0,
                    'message': 'Database is empty'
                }
            
            # Date range
            oldest = session.query(CrimeReport).order_by(CrimeReport.occurred_at.asc()).first()
            newest = session.query(CrimeReport).order_by(CrimeReport.occurred_at.desc()).first()
            
            # Records with coordinates
            with_coords = session.query(CrimeReport).filter(
                CrimeReport.lat.isnot(None),
                CrimeReport.lng.isnot(None)
            ).count()
            
            # Recent records (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent = session.query(CrimeReport).filter(
                CrimeReport.occurred_at >= thirty_days_ago
            ).count()
            
            # Duplicates
            duplicates = session.query(CrimeReport).filter(
                CrimeReport.is_duplicate == True
            ).count()
            
            # Crime types
            crime_types = {}
            for record in session.query(CrimeReport).all():
                crime_type = record.crime_type
                crime_types[crime_type] = crime_types.get(crime_type, 0) + 1
            
            return {
                'total_records': total_records,
                'oldest_record': oldest.occurred_at.isoformat() if oldest else None,
                'newest_record': newest.occurred_at.isoformat() if newest else None,
                'records_with_coordinates': with_coords,
                'coordinate_percentage': (with_coords / total_records * 100) if total_records > 0 else 0,
                'recent_records_30_days': recent,
                'duplicate_records': duplicates,
                'top_crime_types': dict(sorted(crime_types.items(), key=lambda x: x[1], reverse=True)[:10])
            }
    
    def full_maintenance(self, days_to_keep: int = 365):
        """Perform full database maintenance"""
        print("Starting full database maintenance...")
        print("=" * 50)
        
        # Get initial stats
        initial_stats = self.get_database_stats()
        print(f"Initial records: {initial_stats['total_records']}")
        
        # Filter by date
        filter_result = self.filter_by_date_range(days_to_keep)
        
        # Remove duplicates
        duplicate_result = self.remove_duplicates()
        
        # Clean invalid data
        clean_result = self.clean_invalid_data()
        
        # Optimize database
        self.optimize_database()
        
        # Get final stats
        final_stats = self.get_database_stats()
        
        print("\nMaintenance Summary:")
        print("=" * 30)
        print(f"Records deleted (old): {filter_result['deleted']}")
        print(f"Duplicates removed: {duplicate_result['removed']}")
        print(f"Invalid records cleaned: {clean_result['cleaned']}")
        print(f"Final records: {final_stats['total_records']}")
        print(f"Data quality: {final_stats['coordinate_percentage']:.1f}%")
        
        return {
            'initial_records': initial_stats['total_records'],
            'final_records': final_stats['total_records'],
            'deleted_old': filter_result['deleted'],
            'removed_duplicates': duplicate_result['removed'],
            'cleaned_invalid': clean_result['cleaned']
        }

def main():
    """Main function for database maintenance"""
    print("SAFEPATH Database Maintenance Tool")
    print("=" * 50)
    
    maintenance = DatabaseMaintenance()
    
    # Show current statistics
    print("Current Database Statistics:")
    stats = maintenance.get_database_stats()
    print(f"  Total records: {stats['total_records']}")
    if stats['total_records'] > 0:
        print(f"  Date range: {stats['oldest_record']} to {stats['newest_record']}")
        print(f"  Records with coordinates: {stats['records_with_coordinates']} ({stats['coordinate_percentage']:.1f}%)")
        print(f"  Recent records (30 days): {stats['recent_records_30_days']}")
        print(f"  Duplicate records: {stats['duplicate_records']}")
    
    print()
    
    # Perform maintenance
    result = maintenance.full_maintenance(days_to_keep=365)
    
    print()
    print("Maintenance completed successfully!")
    print("=" * 50)

if __name__ == "__main__":
    main()
