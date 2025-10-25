"""
Real-time crime data fetcher for multiple sources
Handles API calls, rate limiting, and data standardization
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import time
from dataclasses import dataclass

from data_sources_config import CRIME_DATA_SOURCES, API_ENDPOINTS, RATE_LIMITS
from database import db_manager
from data_cleaner import data_cleaner

logger = logging.getLogger(__name__)

@dataclass
class FetchResult:
    """Result of a data fetch operation"""
    source: str
    success: bool
    records_fetched: int
    records_processed: int
    errors: List[str]
    fetch_time: datetime
    next_fetch: datetime

class RealTimeFetcher:
    """Fetches real-time crime data from multiple sources"""
    
    def __init__(self):
        self.session = None
        self.rate_limits = {}
        self.last_fetch = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_all_sources(self) -> List[FetchResult]:
        """Fetch data from all active sources"""
        results = []
        
        for source_name, config in CRIME_DATA_SOURCES.items():
            if not config.is_active:
                continue
                
            try:
                result = await self.fetch_source(source_name, config)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to fetch from {source_name}: {e}")
                results.append(FetchResult(
                    source=source_name,
                    success=False,
                    records_fetched=0,
                    records_processed=0,
                    errors=[str(e)],
                    fetch_time=datetime.utcnow(),
                    next_fetch=datetime.utcnow() + timedelta(minutes=config.update_frequency)
                ))
        
        return results
    
    async def fetch_source(self, source_name: str, config) -> FetchResult:
        """Fetch data from a specific source"""
        start_time = datetime.utcnow()
        
        # Check rate limiting
        if not self._can_fetch(source_name, config):
            return FetchResult(
                source=source_name,
                success=False,
                records_fetched=0,
                records_processed=0,
                errors=["Rate limit exceeded"],
                fetch_time=start_time,
                next_fetch=datetime.utcnow() + timedelta(minutes=config.update_frequency)
            )
        
        try:
            # Fetch data from San Francisco Police Department
            if source_name == "sf_police":
                data = await self._fetch_sf_police(config)
            else:
                raise ValueError(f"Unknown source: {source_name}")
            
            # Process and clean data
            cleaned_data = data_cleaner.clean_crime_data(data, source_name)
            
            # Store in database
            stored_count = 0
            for crime in cleaned_data:
                if not crime.is_duplicate:
                    crime_dict = {
                        'id': f"{source_name}_{crime.source_id}",
                        'source_id': crime.source_id,
                        'source': source_name,
                        'crime_type': crime.crime_type,
                        'severity': crime.severity,
                        'description': crime.description,
                        'address': crime.address,
                        'lat': crime.lat,
                        'lng': crime.lng,
                        'occurred_at': crime.occurred_at,
                        'agency': crime.agency,
                        'case_number': crime.case_number,
                        'raw_data': data[0] if data else {}
                    }
                    
                    try:
                        db_manager.add_crime_report(crime_dict)
                        stored_count += 1
                    except Exception as e:
                        logger.error(f"Failed to store crime record: {e}")
            
            # Update rate limiting
            self._update_rate_limit(source_name, config)
            
            return FetchResult(
                source=source_name,
                success=True,
                records_fetched=len(data),
                records_processed=stored_count,
                errors=[],
                fetch_time=start_time,
                next_fetch=datetime.utcnow() + timedelta(minutes=config.update_frequency)
            )
            
        except Exception as e:
            logger.error(f"Error fetching from {source_name}: {e}")
            return FetchResult(
                source=source_name,
                success=False,
                records_fetched=0,
                records_processed=0,
                errors=[str(e)],
                fetch_time=start_time,
                next_fetch=datetime.utcnow() + timedelta(minutes=config.update_frequency)
            )
    
    
    async def _fetch_sf_police(self, config) -> List[Dict]:
        """Fetch data from San Francisco Police Department API"""
        url = f"{config.base_url}{API_ENDPOINTS['sf_police']['incidents']}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                # Process SF Police data format
                processed_data = []
                for record in data.get("data", []):
                    if len(record) >= 35:  # Ensure we have enough fields
                        # Extract relevant fields based on the analysis
                        processed_data.append({
                            "id": record[15] if record[15] else f"sf_{len(processed_data)}",  # Incident ID
                            "type": record[22] if record[22] else "Unknown",  # Incident Category
                            "subcategory": record[23] if record[23] else "Unknown",  # Incident Subcategory
                            "description": record[24] if record[24] else "",  # Incident Description
                            "address": record[26] if record[26] else "",  # Intersection
                            "lat": float(record[32]) if record[32] and str(record[32]).replace('.', '').replace('-', '').isdigit() else None,  # Latitude
                            "lng": float(record[33]) if record[33] and str(record[33]).replace('.', '').replace('-', '').isdigit() else None,  # Longitude
                            "date": record[9] if record[9] else "",  # Incident Datetime
                            "time": record[11] if record[11] else "",  # Incident Time
                            "agency": "San Francisco Police Department",
                            "case_number": record[16] if record[16] else None,  # Incident Number
                            "police_district": record[28] if record[28] else None,  # Police District
                            "neighborhood": record[29] if record[29] else None,  # Analysis Neighborhood
                            "resolution": record[25] if record[25] else None,  # Resolution
                            "raw_data": record
                        })
                return processed_data
            else:
                logger.error(f"SF Police API error: {response.status}")
                return []
    
    def _can_fetch(self, source_name: str, config) -> bool:
        """Check if we can fetch from this source (rate limiting)"""
        if source_name not in self.rate_limits:
            return True
        
        last_fetch = self.rate_limits[source_name].get("last_fetch")
        if not last_fetch:
            return True
        
        # Check if enough time has passed
        time_since_last = datetime.utcnow() - last_fetch
        required_interval = timedelta(minutes=config.update_frequency)
        
        return time_since_last >= required_interval
    
    def _update_rate_limit(self, source_name: str, config):
        """Update rate limiting information"""
        if source_name not in self.rate_limits:
            self.rate_limits[source_name] = {}
        
        self.rate_limits[source_name]["last_fetch"] = datetime.utcnow()
        self.rate_limits[source_name]["request_count"] = self.rate_limits[source_name].get("request_count", 0) + 1

# Global fetcher instance
fetcher = RealTimeFetcher()

async def fetch_real_time_data():
    """Main function to fetch real-time data from all sources"""
    async with RealTimeFetcher() as fetcher:
        results = await fetcher.fetch_all_sources()
        
        # Log results
        for result in results:
            if result.success:
                logger.info(f"Successfully fetched {result.records_processed} records from {result.source}")
            else:
                logger.error(f"Failed to fetch from {result.source}: {result.errors}")
        
        return results

# Scheduled fetching function
async def scheduled_fetch():
    """Scheduled function to run data fetching"""
    while True:
        try:
            logger.info("Starting scheduled data fetch...")
            results = await fetch_real_time_data()
            
            # Log summary
            total_processed = sum(r.records_processed for r in results)
            successful_sources = sum(1 for r in results if r.success)
            
            logger.info(f"Fetch completed: {total_processed} records from {successful_sources} sources")
            
        except Exception as e:
            logger.error(f"Scheduled fetch error: {e}")
        
        # Wait before next fetch (check most frequent source)
        min_interval = min(config.update_frequency for config in CRIME_DATA_SOURCES.values() if config.is_active)
        await asyncio.sleep(min_interval * 60)  # Convert to seconds

if __name__ == "__main__":
    # Run scheduled fetching
    asyncio.run(scheduled_fetch())
