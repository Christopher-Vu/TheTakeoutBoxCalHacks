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

# San Francisco Police Department - Primary Data Source
CRIME_DATA_SOURCES = {
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
    "sf_police": {
        "incidents": "/api/views/wg3w-h783/rows.json"
    }
}

# Crime category mappings for San Francisco Police data
CRIME_CATEGORY_MAPPING = {
    "sf_police": {
        "ROBBERY": "ROBBERY",
        "ASSAULT": "ASSAULT",
        "BURGLARY": "BURGLARY", 
        "THEFT": "THEFT",
        "AUTO_THEFT": "AUTO_THEFT",
        "SEXUAL_ASSAULT": "SEXUAL_ASSAULT",
        "WEAPON_OFFENSE": "WEAPON_OFFENSE",
        "DRUG_OFFENSE": "DRUG_OFFENSE",
        "VANDALISM": "VANDALISM",
        "FRAUD": "FRAUD",
        "EMBEZZLEMENT": "EMBEZZLEMENT",
        "FORGERY": "FORGERY",
        "ARSON": "ARSON",
        "HOMICIDE": "HOMICIDE"
    }
}

# Rate limiting configuration
RATE_LIMITS = {
    "sf_police": {"requests_per_hour": 100, "burst_limit": 10}
}

# Geographic coverage areas
COVERAGE_AREAS = {
    "san_francisco": {
        "bounds": {
            "north": 37.8324,
            "south": 37.7049,
            "east": -122.3482,
            "west": -122.5168
        },
        "center": {"lat": 37.7749, "lng": -122.4194},
        "radius": 10000  # meters
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
