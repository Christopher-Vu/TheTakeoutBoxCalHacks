#!/usr/bin/env python3
"""
Scheduled data synchronization for SAFEPATH
Runs incremental sync every 24 hours
"""

import asyncio
import schedule
import time
import sys
import os
from datetime import datetime
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from incremental_sync import incremental_sync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScheduledSync:
    """Handles scheduled data synchronization"""
    
    def __init__(self):
        self.incremental_sync = incremental_sync
        self.is_running = False
        
    async def run_sync(self):
        """Run the incremental sync process"""
        if self.is_running:
            logger.warning("Sync already running, skipping this cycle")
            return
        
        self.is_running = True
        logger.info("Starting scheduled incremental sync...")
        
        try:
            result = await self.incremental_sync.sync_new_data()
            
            if result['success']:
                logger.info(f"Sync completed successfully:")
                logger.info(f"  Records processed: {result['records_processed']}")
                logger.info(f"  Records added: {result['records_added']}")
                logger.info(f"  Records skipped: {result['records_skipped']}")
                
                # Log new records if any
                if result.get('new_records'):
                    logger.info("New records added:")
                    for record in result['new_records']:
                        logger.info(f"  - {record.get('crime_type', 'Unknown')} at {record.get('address', 'Unknown location')}")
            else:
                logger.error(f"Sync failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error during scheduled sync: {e}")
        finally:
            self.is_running = False
            logger.info("Scheduled sync completed")
    
    def sync_wrapper(self):
        """Wrapper to run async sync in sync context"""
        asyncio.run(self.run_sync())
    
    def start_scheduler(self):
        """Start the scheduled sync process"""
        logger.info("Starting SAFEPATH scheduled sync service...")
        logger.info("Sync will run every 24 hours at 2:00 AM")
        
        # Schedule sync to run every day at 2:00 AM
        schedule.every().day.at("02:00").do(self.sync_wrapper)
        
        # Also run immediately on startup (for testing)
        logger.info("Running initial sync...")
        self.sync_wrapper()
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def run_manual_sync(self):
        """Run a manual sync (for testing)"""
        logger.info("Running manual sync...")
        self.sync_wrapper()
    
    def get_sync_status(self):
        """Get current sync status"""
        stats = self.incremental_sync.get_sync_statistics()
        return {
            'is_running': self.is_running,
            'next_sync': schedule.next_run().isoformat() if schedule.jobs else None,
            'statistics': stats
        }

def main():
    """Main function for scheduled sync"""
    print("SAFEPATH Scheduled Sync Service")
    print("=" * 50)
    
    sync_service = ScheduledSync()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "manual":
            print("Running manual sync...")
            sync_service.run_manual_sync()
        elif sys.argv[1] == "status":
            status = sync_service.get_sync_status()
            print(f"Sync Status:")
            print(f"  Running: {status['is_running']}")
            print(f"  Next sync: {status['next_sync']}")
            print(f"  Total records: {status['statistics']['total_records']}")
            print(f"  Recent records (24h): {status['statistics']['recent_records_24h']}")
        else:
            print("Usage: python scheduled_sync.py [manual|status]")
    else:
        print("Starting scheduled sync service...")
        print("Press Ctrl+C to stop")
        try:
            sync_service.start_scheduler()
        except KeyboardInterrupt:
            print("\nStopping scheduled sync service...")
            logger.info("Scheduled sync service stopped by user")

if __name__ == "__main__":
    main()
