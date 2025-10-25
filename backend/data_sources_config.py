"""
Configuration for real-time crime data sources
Supports multiple APIs with fallback and rate limiting
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import os

class DataSourceType(Enum):
    API = "api"
    SCRAPER = "scraper"
    MANUAL = "manual"

@dataclass
class DataSourceConfig:
    """Configuration for a crime data source"""
    name: str
    source_type: DataSourceType
    base_url: str
    api_key: Optional[str] = None
    rate_limit: int = 100  # requests per hour
    update_frequency: int = 30  # minutes
    is_active: bool = True
    priority: int = 1  # 1 = highest priority
    coverage_area: Optional[Dict] = None
    categories: List[str] = None
    description: str = ""

# Real-time crime data sources
CRIME_DATA_SOURCES = {
    "crimeometer": DataSourceConfig(
        name="CrimeoMeter API",
        source_type=DataSourceType.API,
        base_url="https://api.crimeometer.com",
        api_key=os.getenv("CRIMEOMETER_API_KEY"),
        rate_limit=1000,
        update_frequency=15,  # 15 minutes
        priority=1,
        coverage_area={"type": "city", "name": "Berkeley", "state": "CA"},
        categories=[
            "ROBBERY", "ASSAULT", "BURGLARY", "THEFT", "AUTO_THEFT",
            "SEXUAL_ASSAULT", "WEAPON_OFFENSE", "DRUG_OFFENSE", "VANDALISM"
        ],
        description="Comprehensive real-time crime data for 700+ U.S. cities"
    ),
    
    "berkeley_pd": DataSourceConfig(
        name="Berkeley PD Open Data",
        source_type=DataSourceType.API,
        base_url="https://data.cityofberkeley.info",
        rate_limit=100,
        update_frequency=60,  # 1 hour
        priority=2,
        coverage_area={"type": "city", "name": "Berkeley", "state": "CA"},
        categories=[
            "ROBBERY", "ASSAULT", "BURGLARY", "THEFT", "AUTO_THEFT",
            "SEXUAL_ASSAULT", "WEAPON_OFFENSE", "DRUG_OFFENSE", "VANDALISM",
            "FRAUD", "EMBEZZLEMENT", "FORGERY", "ARSON"
        ],
        description="Official Berkeley Police Department data"
    ),
    
    "fbi_ucr": DataSourceConfig(
        name="FBI Crime Data API",
        source_type=DataSourceType.API,
        base_url="https://api.usa.gov/crime/fbi",
        rate_limit=1000,
        update_frequency=1440,  # 24 hours (annual data)
        priority=3,
        coverage_area={"type": "national", "name": "United States"},
        categories=[
            "HOMICIDE", "RAPE", "ROBBERY", "ASSAULT", "BURGLARY",
            "LARCENY", "AUTO_THEFT", "ARSON"
        ],
        description="FBI Uniform Crime Reporting data"
    ),
    
    "community_crime_map": DataSourceConfig(
        name="CommunityCrimeMap Scraper",
        source_type=DataSourceType.SCRAPER,
        base_url="https://communitycrimemap.com",
        rate_limit=10,
        update_frequency=30,
        priority=2,
        coverage_area={"type": "city", "name": "Berkeley", "state": "CA"},
        categories=[
            "ROBBERY", "ASSAULT", "BURGLARY", "THEFT", "AUTO_THEFT",
            "SEXUAL_ASSAULT", "WEAPON_OFFENSE", "DRUG_OFFENSE", "VANDALISM"
        ],
        description="Scraped data from CommunityCrimeMap.com"
    ),
    
    "ucpd": DataSourceConfig(
        name="UCPD Crime Log",
        source_type=DataSourceType.SCRAPER,
        base_url="https://police.berkeley.edu",
        rate_limit=5,
        update_frequency=120,  # 2 hours
        priority=2,
        coverage_area={"type": "campus", "name": "UC Berkeley"},
        categories=[
            "ROBBERY", "ASSAULT", "BURGLARY", "THEFT", "AUTO_THEFT",
            "SEXUAL_ASSAULT", "WEAPON_OFFENSE", "DRUG_OFFENSE", "VANDALISM"
        ],
        description="UC Berkeley Police Department crime log"
    ),
    
    "sf_police": DataSourceConfig(
        name="San Francisco Police Department",
        source_type=DataSourceType.API,
        base_url="https://data.sfgov.org",
        rate_limit=100,
        update_frequency=1440,  # 24 hours (as specified)
        priority=1,
        coverage_area={"type": "city", "name": "San Francisco", "state": "CA"},
        categories=[
            "ROBBERY", "ASSAULT", "BURGLARY", "THEFT", "AUTO_THEFT",
            "SEXUAL_ASSAULT", "WEAPON_OFFENSE", "DRUG_OFFENSE", "VANDALISM",
            "FRAUD", "EMBEZZLEMENT", "FORGERY", "ARSON", "HOMICIDE"
        ],
        description="San Francisco Police Department incident reports - updates every 24 hours"
    )
}

# API endpoint configurations
API_ENDPOINTS = {
    "crimeometer": {
        "incidents": "/v1/incidents/raw-data",
        "statistics": "/v1/incidents/stats",
        "safety_score": "/v1/safety-score"
    },
    "berkeley_pd": {
        "calls_for_service": "/api/views/k2nh-s5h5/rows.json",
        "arrests": "/api/views/arrests/rows.json"
    },
    "fbi_ucr": {
        "offenses": "/offenses",
        "agencies": "/agencies",
        "counts": "/counts"
    },
    "sf_police": {
        "incidents": "/api/v3/views/wg3w-h783/query.json"
    }
}

# Crime category mappings for standardization
CRIME_CATEGORY_MAPPING = {
    "crimeometer": {
        "ROBBERY": "ROBBERY",
        "ASSAULT": "ASSAULT", 
        "BURGLARY": "BURGLARY",
        "THEFT": "THEFT",
        "AUTO_THEFT": "AUTO_THEFT",
        "SEXUAL_ASSAULT": "SEXUAL_ASSAULT",
        "WEAPON_OFFENSE": "WEAPON_OFFENSE",
        "DRUG_OFFENSE": "DRUG_OFFENSE",
        "VANDALISM": "VANDALISM"
    },
    "berkeley_pd": {
        "ROBBERY": "ROBBERY",
        "ASSAULT": "ASSAULT",
        "BURGLARY": "BURGLARY", 
        "THEFT": "THEFT",
        "AUTO_THEFT": "AUTO_THEFT",
        "SEXUAL_ASSAULT": "SEXUAL_ASSAULT",
        "WEAPON_OFFENSE": "WEAPON_OFFENSE",
        "DRUG_OFFENSE": "DRUG_OFFENSE",
        "VANDALISM": "VANDALISM"
    }
}

# Rate limiting configuration
RATE_LIMITS = {
    "crimeometer": {"requests_per_hour": 1000, "burst_limit": 100},
    "berkeley_pd": {"requests_per_hour": 100, "burst_limit": 10},
    "fbi_ucr": {"requests_per_hour": 1000, "burst_limit": 50},
    "community_crime_map": {"requests_per_hour": 10, "burst_limit": 1},
    "ucpd": {"requests_per_hour": 5, "burst_limit": 1}
}

# Geographic coverage areas
COVERAGE_AREAS = {
    "berkeley": {
        "bounds": {
            "north": 37.89,
            "south": 37.85,
            "east": -122.25,
            "west": -122.28
        },
        "center": {"lat": 37.8719, "lng": -122.2585},
        "radius": 5000  # meters
    }
}

def get_active_sources() -> List[DataSourceConfig]:
    """Get list of active data sources"""
    return [config for config in CRIME_DATA_SOURCES.values() if config.is_active]

def get_source_by_name(name: str) -> Optional[DataSourceConfig]:
    """Get data source configuration by name"""
    return CRIME_DATA_SOURCES.get(name)

def get_priority_sources() -> List[DataSourceConfig]:
    """Get data sources sorted by priority"""
    active_sources = get_active_sources()
    return sorted(active_sources, key=lambda x: x.priority)

def get_sources_for_area(area: str) -> List[DataSourceConfig]:
    """Get data sources that cover a specific area"""
    sources = []
    for config in get_active_sources():
        if config.coverage_area and area.lower() in config.coverage_area.get("name", "").lower():
            sources.append(config)
    return sources
