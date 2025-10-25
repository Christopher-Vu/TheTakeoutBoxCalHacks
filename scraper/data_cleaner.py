"""
Enhanced data cleaning and standardization pipeline
Handles multiple data sources with deduplication and quality scoring
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher

from geocoder import geocoder, GeocodingResult

logger = logging.getLogger(__name__)

@dataclass
class CleanedCrimeData:
    """Standardized crime data after cleaning"""
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
    case_number: Optional[str]
    quality_score: float
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None

class DataCleaner:
    """Enhanced data cleaning with multi-source support"""
    
    def __init__(self):
        self.crime_type_mapping = self._build_crime_type_mapping()
        self.severity_mapping = self._build_severity_mapping()
        self.agency_mapping = self._build_agency_mapping()
        
    def _build_crime_type_mapping(self) -> Dict[str, str]:
        """Build comprehensive crime type mapping"""
        return {
            # Robbery variations
            'ROBBERY': 'ROBBERY',
            'ROB': 'ROBBERY',
            'ARMED ROBBERY': 'ROBBERY',
            'STRONG ARM ROBBERY': 'ROBBERY',
            
            # Assault variations
            'ASSAULT': 'ASSAULT',
            'BATTERY': 'ASSAULT',
            'AGGRAVATED ASSAULT': 'ASSAULT',
            'SIMPLE ASSAULT': 'ASSAULT',
            
            # Burglary variations
            'BURGLARY': 'BURGLARY',
            'BURG': 'BURGLARY',
            'RESIDENTIAL BURGLARY': 'BURGLARY',
            'COMMERCIAL BURGLARY': 'BURGLARY',
            
            # Theft variations
            'THEFT': 'THEFT',
            'LARCENY': 'THEFT',
            'GRAND THEFT': 'THEFT',
            'PETTY THEFT': 'THEFT',
            'SHOPLIFTING': 'THEFT',
            'AUTO THEFT': 'AUTO_THEFT',
            'VEHICLE THEFT': 'AUTO_THEFT',
            
            # Drug offenses
            'DRUG': 'DRUG_OFFENSE',
            'POSSESSION': 'DRUG_OFFENSE',
            'SALES': 'DRUG_OFFENSE',
            'MARIJUANA': 'DRUG_OFFENSE',
            
            # Sexual offenses
            'SEXUAL': 'SEXUAL_ASSAULT',
            'RAPE': 'SEXUAL_ASSAULT',
            'SEXUAL ASSAULT': 'SEXUAL_ASSAULT',
            
            # Weapon offenses
            'WEAPON': 'WEAPON_OFFENSE',
            'FIREARM': 'WEAPON_OFFENSE',
            'GUN': 'WEAPON_OFFENSE',
            
            # Vandalism
            'VANDALISM': 'VANDALISM',
            'GRAFFITI': 'VANDALISM',
            'DAMAGE': 'VANDALISM',
            
            # Homicide
            'HOMICIDE': 'HOMICIDE',
            'MURDER': 'HOMICIDE',
            'DEATH': 'HOMICIDE'
        }
    
    def _build_severity_mapping(self) -> Dict[str, int]:
        """Build severity scoring for crime types"""
        return {
            'HOMICIDE': 10,
            'SEXUAL_ASSAULT': 9,
            'ROBBERY': 8,
            'ASSAULT': 7,
            'WEAPON_OFFENSE': 8,
            'BURGLARY': 6,
            'AUTO_THEFT': 5,
            'DRUG_OFFENSE': 5,
            'THEFT': 4,
            'VANDALISM': 3,
            'OTHER': 2
        }
    
    def _build_agency_mapping(self) -> Dict[str, str]:
        """Build agency name standardization"""
        return {
            'BERKELEY PD': 'Berkeley PD',
            'BERKELEY POLICE': 'Berkeley PD',
            'BPD': 'Berkeley PD',
            'UCPD': 'UCPD',
            'UC POLICE': 'UCPD',
            'UNIVERSITY POLICE': 'UCPD',
            'ALAMEDA COUNTY': 'Alameda County Sheriff',
            'SHERIFF': 'Alameda County Sheriff'
        }
    
    def clean_crime_data(self, raw_data: List[Dict], source: str) -> List[CleanedCrimeData]:
        """Clean and standardize crime data from any source"""
        cleaned_data = []
        
        for record in raw_data:
            try:
                cleaned = self._clean_single_record(record, source)
                if cleaned:
                    cleaned_data.append(cleaned)
            except Exception as e:
                logger.error(f"Failed to clean record from {source}: {e}")
                continue
        
        # Deduplicate within the batch
        deduplicated = self._deduplicate_batch(cleaned_data)
        
        return deduplicated
    
    def _clean_single_record(self, record: Dict, source: str) -> Optional[CleanedCrimeData]:
        """Clean a single crime record"""
        
        # Extract basic fields
        crime_type = self._standardize_crime_type(record.get('type', ''))
        description = self._clean_description(record.get('description', ''))
        address = self._clean_address(record.get('address', ''))
        agency = self._standardize_agency(record.get('agency', ''))
        
        # Parse date/time
        occurred_at = self._parse_datetime(record.get('date', ''), record.get('time', ''))
        if not occurred_at:
            logger.warning(f"Could not parse datetime for record: {record}")
            return None
        
        # Geocode address if coordinates not provided
        lat, lng = self._get_coordinates(record, address)
        if lat is None or lng is None:
            logger.warning(f"Could not geocode address: {address}")
            return None
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(record, lat, lng, occurred_at)
        
        return CleanedCrimeData(
            source_id=record.get('id', ''),
            source=source,
            crime_type=crime_type,
            severity=self.severity_mapping.get(crime_type, 2),
            description=description,
            address=address,
            lat=lat,
            lng=lng,
            occurred_at=occurred_at,
            agency=agency,
            case_number=record.get('case_number'),
            quality_score=quality_score
        )
    
    def _standardize_crime_type(self, raw_type: str) -> str:
        """Standardize crime type across sources"""
        if not raw_type:
            return 'OTHER'
        
        raw_upper = raw_type.upper().strip()
        
        # Direct mapping
        if raw_upper in self.crime_type_mapping:
            return self.crime_type_mapping[raw_upper]
        
        # Partial matching
        for key, value in self.crime_type_mapping.items():
            if key in raw_upper:
                return value
        
        # Fuzzy matching for similar types
        best_match = self._fuzzy_match_crime_type(raw_upper)
        if best_match:
            return best_match
        
        return 'OTHER'
    
    def _fuzzy_match_crime_type(self, raw_type: str) -> Optional[str]:
        """Fuzzy match crime types for better classification"""
        best_score = 0
        best_match = None
        
        for key, value in self.crime_type_mapping.items():
            score = SequenceMatcher(None, raw_type, key).ratio()
            if score > 0.6 and score > best_score:
                best_score = score
                best_match = value
        
        return best_match
    
    def _clean_description(self, description: str) -> str:
        """Clean and standardize description text"""
        if not description:
            return ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', description.strip())
        
        # Remove common prefixes
        prefixes_to_remove = [
            'CASE#', 'CASE:', 'INCIDENT:', 'REPORT:', 'CALL:'
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.upper().startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        return cleaned
    
    def _clean_address(self, address: str) -> str:
        """Clean and standardize address format"""
        if not address:
            return ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', address.strip())
        
        # Standardize common abbreviations
        abbreviations = {
            'ST': 'Street',
            'AVE': 'Avenue',
            'BLVD': 'Boulevard',
            'DR': 'Drive',
            'RD': 'Road',
            'CT': 'Court',
            'PL': 'Place',
            'LN': 'Lane',
            'BL': 'Block',
            'N': 'North',
            'S': 'South',
            'E': 'East',
            'W': 'West'
        }
        
        for abbr, full in abbreviations.items():
            cleaned = re.sub(rf'\b{abbr}\b', full, cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    def _standardize_agency(self, agency: str) -> str:
        """Standardize agency names"""
        if not agency:
            return "Unknown"
        
        agency_upper = agency.upper().strip()
        return self.agency_mapping.get(agency_upper, agency)
    
    def _parse_datetime(self, date_str: str, time_str: str = "") -> Optional[datetime]:
        """Parse various datetime formats"""
        if not date_str:
            return None
        
        # Common date formats
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m-%d-%Y',
            '%Y/%m/%d',
            '%d/%m/%Y',
            '%B %d, %Y',
            '%b %d, %Y'
        ]
        
        # Common time formats
        time_formats = [
            '%H:%M:%S',
            '%H:%M',
            '%I:%M %p',
            '%I:%M:%S %p'
        ]
        
        # Try to parse date
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), fmt).date()
                break
            except ValueError:
                continue
        
        if not parsed_date:
            return None
        
        # Try to parse time
        parsed_time = None
        if time_str:
            for fmt in time_formats:
                try:
                    parsed_time = datetime.strptime(time_str.strip(), fmt).time()
                    break
                except ValueError:
                    continue
        
        # Combine date and time
        if parsed_time:
            return datetime.combine(parsed_date, parsed_time)
        else:
            return datetime.combine(parsed_date, datetime.min.time())
    
    def _get_coordinates(self, record: Dict, address: str) -> Tuple[Optional[float], Optional[float]]:
        """Get coordinates from record or geocode address"""
        
        # Check if coordinates already exist
        if 'lat' in record and 'lng' in record:
            try:
                return float(record['lat']), float(record['lng'])
            except (ValueError, TypeError):
                pass
        
        if 'latitude' in record and 'longitude' in record:
            try:
                return float(record['latitude']), float(record['longitude'])
            except (ValueError, TypeError):
                pass
        
        # Geocode address
        if address:
            result = geocoder.geocode(address)
            if result:
                return result.lat, result.lng
        
        return None, None
    
    def _calculate_quality_score(self, record: Dict, lat: float, lng: float, occurred_at: datetime) -> float:
        """Calculate quality score for crime data (0-1)"""
        score = 0.0
        
        # Base score for having required fields
        if lat and lng:
            score += 0.3
        if occurred_at:
            score += 0.2
        if record.get('type'):
            score += 0.1
        if record.get('description'):
            score += 0.1
        
        # Recency bonus (newer crimes are more relevant)
        if occurred_at:
            days_old = (datetime.now() - occurred_at).days
            if days_old <= 7:
                score += 0.2
            elif days_old <= 30:
                score += 0.1
        
        # Location precision bonus
        if lat and lng:
            # Check if coordinates are in Berkeley area
            if 37.85 <= lat <= 37.89 and -122.28 <= lng <= -122.25:
                score += 0.1
        
        return min(score, 1.0)
    
    def _deduplicate_batch(self, crimes: List[CleanedCrimeData]) -> List[CleanedCrimeData]:
        """Remove duplicates within a batch of crimes"""
        if not crimes:
            return crimes
        
        # Sort by quality score (highest first)
        crimes.sort(key=lambda x: x.quality_score, reverse=True)
        
        deduplicated = []
        seen_locations = set()
        
        for crime in crimes:
            # Create location key for duplicate detection
            location_key = (
                round(crime.lat, 4),  # Round to ~11m precision
                round(crime.lng, 4),
                crime.occurred_at.strftime('%Y-%m-%d %H')  # Same hour
            )
            
            if location_key not in seen_locations:
                seen_locations.add(location_key)
                deduplicated.append(crime)
            else:
                # Mark as duplicate
                crime.is_duplicate = True
                # Find the canonical record
                for canonical in deduplicated:
                    canonical_key = (
                        round(canonical.lat, 4),
                        round(canonical.lng, 4),
                        canonical.occurred_at.strftime('%Y-%m-%d %H')
                    )
                    if canonical_key == location_key:
                        crime.duplicate_of = canonical.source_id
                        break
        
        return deduplicated

# Initialize data cleaner
data_cleaner = DataCleaner()
