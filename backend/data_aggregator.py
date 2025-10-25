"""
Multi-source crime data aggregation system
Handles data from multiple sources with deduplication and standardization
"""

import asyncio
import aiohttp
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

from database import db_manager, CrimeReport, DataSource, DataSyncLog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SourceType(Enum):
    COMMUNITY_CRIME_MAP = "communitycrimemap"
    BERKELEY_PD_API = "berkeley_pd"
    UCPD_API = "ucpd"
    MANUAL_ENTRY = "manual"
    NEWS_SCRAPER = "news_scraper"

@dataclass
class CrimeData:
    """Standardized crime data structure"""
    source_id: str
    source: str
    crime_type: str
    severity: int
    description: str
    address: str
    lat: float
    lng: float
    occurred_at: datetime
    agency: str
    case_number: Optional[str] = None
    source_url: Optional[str] = None
    raw_data: Optional[Dict] = None

class CrimeDataAggregator:
    """Main aggregator class for multi-source crime data"""
    
    def __init__(self):
        self.sources = {}
        self.deduplication_rules = {
            'location_threshold': 50,  # meters
            'time_threshold': 3600,   # seconds (1 hour)
            'type_similarity': 0.8    # 0-1 similarity score
        }
        
    async def register_source(self, source_type: SourceType, config: Dict):
        """Register a new data source"""
        source_id = str(uuid.uuid4())
        source = DataSource(
            id=source_id,
            name=config['name'],
            source_type=config['type'],
            base_url=config.get('base_url'),
            api_key=config.get('api_key'),
            sync_frequency=config.get('sync_frequency', 30),
            config=config
        )
        
        with db_manager.get_session() as session:
            session.add(source)
            session.commit()
            
        self.sources[source_type] = source
        logger.info(f"Registered source: {source.name}")
        
    async def sync_all_sources(self) -> Dict[str, Any]:
        """Sync data from all registered sources"""
        results = {}
        
        for source_type, source in self.sources.items():
            try:
                result = await self.sync_source(source_type)
                results[source_type.value] = result
            except Exception as e:
                logger.error(f"Failed to sync {source_type.value}: {e}")
                results[source_type.value] = {'error': str(e)}
                
        return results
    
    async def sync_source(self, source_type: SourceType) -> Dict[str, Any]:
        """Sync data from a specific source"""
        source = self.sources[source_type]
        sync_log = DataSyncLog(
            id=str(uuid.uuid4()),
            source_id=source.id,
            sync_started=datetime.utcnow(),
            status='running'
        )
        
        with db_manager.get_session() as session:
            session.add(sync_log)
            session.commit()
        
        try:
            # Get data from source
            if source_type == SourceType.COMMUNITY_CRIME_MAP:
                crimes = await self._scrape_community_crime_map()
            elif source_type == SourceType.BERKELEY_PD_API:
                crimes = await self._fetch_berkeley_pd_data()
            elif source_type == SourceType.UCPD_API:
                crimes = await self._fetch_ucpd_data()
            else:
                raise ValueError(f"Unknown source type: {source_type}")
            
            # Process and deduplicate
            processed_crimes = await self._process_crimes(crimes, source_type)
            
            # Update sync log
            sync_log.sync_completed = datetime.utcnow()
            sync_log.records_processed = len(crimes)
            sync_log.records_added = len([c for c in processed_crimes if c.get('is_new', True)])
            sync_log.status = 'success'
            
            with db_manager.get_session() as session:
                session.merge(sync_log)
                session.commit()
                
            return {
                'processed': len(crimes),
                'added': len([c for c in processed_crimes if c.get('is_new', True)]),
                'duplicates': len([c for c in processed_crimes if c.get('is_duplicate', False)])
            }
            
        except Exception as e:
            sync_log.sync_completed = datetime.utcnow()
            sync_log.status = 'failed'
            sync_log.errors = {'error': str(e)}
            
            with db_manager.get_session() as session:
                session.merge(sync_log)
                session.commit()
                
            raise e
    
    async def _scrape_community_crime_map(self) -> List[CrimeData]:
        """Scrape data from CommunityCrimeMap"""
        # This would integrate with your existing scraper
        # For now, return mock data structure
        crimes = []
        
        # TODO: Implement actual scraping logic
        # This should call your existing crimemap_scraper.py
        
        return crimes
    
    async def _fetch_berkeley_pd_data(self) -> List[CrimeData]:
        """Fetch data from Berkeley PD API"""
        crimes = []
        
        # Berkeley PD Open Data Portal
        # https://data.cityofberkeley.info/Public-Safety/Berkeley-PD-Calls-for-Service/k2nh-s5h5
        async with aiohttp.ClientSession() as session:
            url = "https://data.cityofberkeley.info/api/views/k2nh-s5h5/rows.json"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Process Berkeley PD data
                    for record in data.get('data', []):
                        crime = self._parse_berkeley_pd_record(record)
                        if crime:
                            crimes.append(crime)
        
        return crimes
    
    async def _fetch_ucpd_data(self) -> List[CrimeData]:
        """Fetch data from UCPD sources"""
        crimes = []
        
        # UCPD Daily Crime Log
        # https://police.berkeley.edu/crime-log/
        # This would require scraping or API access
        
        return crimes
    
    def _parse_berkeley_pd_record(self, record: List) -> Optional[CrimeData]:
        """Parse Berkeley PD API record into standardized format"""
        try:
            # Berkeley PD API structure (adjust based on actual API)
            return CrimeData(
                source_id=record[0] if len(record) > 0 else str(uuid.uuid4()),
                source=SourceType.BERKELEY_PD_API.value,
                crime_type=self._standardize_crime_type(record[1] if len(record) > 1 else ""),
                severity=self._calculate_severity(record[1] if len(record) > 1 else ""),
                description=record[2] if len(record) > 2 else "",
                address=record[3] if len(record) > 3 else "",
                lat=float(record[4]) if len(record) > 4 and record[4] else 0.0,
                lng=float(record[5]) if len(record) > 5 and record[5] else 0.0,
                occurred_at=datetime.fromisoformat(record[6]) if len(record) > 6 else datetime.utcnow(),
                agency="Berkeley PD",
                case_number=record[7] if len(record) > 7 else None,
                raw_data=record
            )
        except Exception as e:
            logger.error(f"Failed to parse Berkeley PD record: {e}")
            return None
    
    def _standardize_crime_type(self, raw_type: str) -> str:
        """Standardize crime types across sources"""
        type_mapping = {
            'ROBBERY': 'ROBBERY',
            'BURGLARY': 'BURGLARY',
            'ASSAULT': 'ASSAULT',
            'THEFT': 'THEFT',
            'VANDALISM': 'VANDALISM',
            'DRUG': 'DRUG_OFFENSE',
            'WEAPON': 'WEAPON_OFFENSE',
            'SEXUAL': 'SEXUAL_ASSAULT',
            'HOMICIDE': 'HOMICIDE'
        }
        
        raw_upper = raw_type.upper()
        for key, value in type_mapping.items():
            if key in raw_upper:
                return value
        
        return 'OTHER'
    
    def _calculate_severity(self, crime_type: str) -> int:
        """Calculate severity score (1-10) based on crime type"""
        severity_map = {
            'HOMICIDE': 10,
            'SEXUAL_ASSAULT': 9,
            'ROBBERY': 8,
            'ASSAULT': 7,
            'BURGLARY': 6,
            'WEAPON_OFFENSE': 8,
            'THEFT': 4,
            'VANDALISM': 3,
            'DRUG_OFFENSE': 5,
            'OTHER': 2
        }
        
        return severity_map.get(crime_type, 2)
    
    async def _process_crimes(self, crimes: List[CrimeData], source_type: SourceType) -> List[Dict]:
        """Process and deduplicate crimes"""
        processed = []
        
        for crime in crimes:
            # Check for duplicates
            duplicates = db_manager.find_duplicates({
                'lat': crime.lat,
                'lng': crime.lng,
                'occurred_at': crime.occurred_at,
                'crime_type': crime.crime_type
            })
            
            if duplicates:
                # Mark as duplicate
                crime_dict = self._crime_to_dict(crime)
                crime_dict['is_duplicate'] = True
                crime_dict['duplicate_of'] = duplicates[0].id
                processed.append(crime_dict)
            else:
                # Add new crime
                crime_dict = self._crime_to_dict(crime)
                crime_dict['is_new'] = True
                
                # Save to database
                crime_id = db_manager.add_crime_report(crime_dict)
                crime_dict['id'] = crime_id
                processed.append(crime_dict)
        
        return processed
    
    def _crime_to_dict(self, crime: CrimeData) -> Dict:
        """Convert CrimeData to dictionary for database storage"""
        return {
            'id': str(uuid.uuid4()),
            'source_id': crime.source_id,
            'source': crime.source,
            'crime_type': crime.crime_type,
            'severity': crime.severity,
            'description': crime.description,
            'address': crime.address,
            'lat': crime.lat,
            'lng': crime.lng,
            'occurred_at': crime.occurred_at,
            'agency': crime.agency,
            'case_number': crime.case_number,
            'source_url': crime.source_url,
            'raw_data': crime.raw_data,
            'confidence_score': 0.9  # Default confidence
        }

# Initialize aggregator
aggregator = CrimeDataAggregator()

# Register default sources
async def initialize_sources():
    """Initialize default data sources"""
    await aggregator.register_source(SourceType.COMMUNITY_CRIME_MAP, {
        'name': 'CommunityCrimeMap',
        'type': 'scraper',
        'base_url': 'https://communitycrimemap.com',
        'sync_frequency': 30
    })
    
    await aggregator.register_source(SourceType.BERKELEY_PD_API, {
        'name': 'Berkeley PD Open Data',
        'type': 'api',
        'base_url': 'https://data.cityofberkeley.info',
        'sync_frequency': 60
    })
    
    await aggregator.register_source(SourceType.UCPD_API, {
        'name': 'UCPD Crime Log',
        'type': 'scraper',
        'base_url': 'https://police.berkeley.edu',
        'sync_frequency': 120
    })
