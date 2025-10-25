"""
PostgreSQL models + connections for SAFEPATH crime data aggregation
Supports multiple data sources with deduplication and standardization
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
try:
    from geoalchemy2 import Geometry
    HAS_POSTGIS = True
except ImportError:
    HAS_POSTGIS = False
    # Fallback for SQLite
    from sqlalchemy import Column as GeoColumn
from datetime import datetime
import os
from typing import List, Dict, Optional

Base = declarative_base()

class CrimeReport(Base):
    """Unified crime report model supporting multiple data sources"""
    __tablename__ = 'crimes'
    
    # Primary identification
    id = Column(String, primary_key=True)  # UUID or source-specific ID
    source_id = Column(String, nullable=False)  # Original ID from source
    source = Column(String, nullable=False)  # 'communitycrimemap', 'berkeley_pd', 'ucpd', etc.
    
    # Crime details
    crime_type = Column(String, nullable=False)  # Standardized: 'ROBBERY', 'ASSAULT', etc.
    severity = Column(Integer, nullable=False)  # 1-10 scale
    description = Column(Text)
    
    # Location data
    address = Column(String)  # Human-readable address
    if HAS_POSTGIS:
        point = Column(Geometry('POINT', srid=4326))  # PostGIS geometry
    else:
        point = Column(Text)  # SQLite fallback - store as text
    lat = Column(Float)
    lng = Column(Float)
    block_address = Column(String)  # Generalized address for privacy
    
    # Temporal data
    occurred_at = Column(DateTime, nullable=False)  # When crime happened
    reported_at = Column(DateTime)  # When it was reported
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Source metadata
    agency = Column(String)  # 'Berkeley PD', 'UCPD', etc.
    case_number = Column(String)
    source_url = Column(String)
    
    # Aggregation metadata
    is_duplicate = Column(Boolean, default=False)
    duplicate_of = Column(String)  # ID of canonical report if this is a duplicate
    confidence_score = Column(Float)  # 0-1, how confident we are in this data
    
    # Additional data (flexible JSON storage)
    raw_data = Column(JSON)  # Original data from source (JSONB for PostgreSQL, JSON for SQLite)
    tags = Column(JSON)  # Additional categorization
    
    # Indexes for performance
    if HAS_POSTGIS:
        __table_args__ = (
            Index('idx_crimes_point', 'point', postgresql_using='gist'),
            Index('idx_crimes_occurred_at', 'occurred_at'),
            Index('idx_crimes_source', 'source'),
            Index('idx_crimes_type', 'crime_type'),
            Index('idx_crimes_severity', 'severity'),
            Index('idx_crimes_duplicate', 'is_duplicate'),
        )
    else:
        # SQLite indexes (no spatial index)
        __table_args__ = (
            Index('idx_crimes_lat_lng', 'lat', 'lng'),
            Index('idx_crimes_occurred_at', 'occurred_at'),
            Index('idx_crimes_source', 'source'),
            Index('idx_crimes_type', 'crime_type'),
            Index('idx_crimes_severity', 'severity'),
            Index('idx_crimes_duplicate', 'is_duplicate'),
        )

class DataSource(Base):
    """Track data sources and their metadata"""
    __tablename__ = 'data_sources'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)  # 'CommunityCrimeMap', 'Berkeley PD API', etc.
    source_type = Column(String, nullable=False)  # 'scraper', 'api', 'manual'
    base_url = Column(String)
    api_key = Column(String)  # Encrypted
    last_sync = Column(DateTime)
    sync_frequency = Column(Integer)  # Minutes between syncs
    is_active = Column(Boolean, default=True)
    config = Column(JSON)  # Source-specific configuration
    created_at = Column(DateTime, default=datetime.utcnow)

class DataSyncLog(Base):
    """Track sync operations and errors"""
    __tablename__ = 'data_sync_logs'
    
    id = Column(String, primary_key=True)
    source_id = Column(String, nullable=False)
    sync_started = Column(DateTime, nullable=False)
    sync_completed = Column(DateTime)
    records_processed = Column(Integer, default=0)
    records_added = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_duplicated = Column(Integer, default=0)
    errors = Column(JSON)
    status = Column(String)  # 'success', 'partial', 'failed'

class DatabaseManager:
    """Database connection and operations manager"""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            # Use SQLite for development, PostgreSQL for production
            database_url = os.getenv('DATABASE_URL', 'sqlite:///./safepath.db')
        
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def add_crime_report(self, crime_data: Dict) -> str:
        """Add a new crime report to the database"""
        with self.get_session() as session:
            crime = CrimeReport(**crime_data)
            session.add(crime)
            session.commit()
            return crime.id
    
    def get_crimes_in_bounds(self, min_lat: float, max_lat: float, 
                           min_lng: float, max_lng: float) -> List[Dict]:
        """Get crimes within geographic bounds"""
        with self.get_session() as session:
            # Use PostGIS spatial query for efficient geographic filtering
            query = session.query(CrimeReport).filter(
                CrimeReport.lat.between(min_lat, max_lat),
                CrimeReport.lng.between(min_lng, max_lng),
                CrimeReport.is_duplicate == False
            )
            return [self._crime_to_dict(crime) for crime in query.all()]
    
    def get_crimes_near_point(self, lat: float, lng: float, radius_meters: float = 100) -> List[Dict]:
        """Get crimes within radius of a point"""
        with self.get_session() as session:
            if HAS_POSTGIS:
                # PostGIS ST_DWithin for efficient radius queries
                from sqlalchemy import text
                query = session.query(CrimeReport).filter(
                    text("ST_DWithin(point, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), :radius)"),
                    CrimeReport.is_duplicate == False
                ).params(lat=lat, lng=lng, radius=radius_meters)
            else:
                # SQLite fallback - simple lat/lng distance calculation
                # Convert radius from meters to approximate degrees (rough approximation)
                lat_radius = radius_meters / 111000  # 1 degree ≈ 111km
                lng_radius = radius_meters / (111000 * abs(lat))  # Adjust for latitude
                
                query = session.query(CrimeReport).filter(
                    CrimeReport.lat.between(lat - lat_radius, lat + lat_radius),
                    CrimeReport.lng.between(lng - lng_radius, lng + lng_radius),
                    CrimeReport.is_duplicate == False
                )
            
            return [self._crime_to_dict(crime) for crime in query.all()]
    
    def find_duplicates(self, crime_data: Dict) -> List[CrimeReport]:
        """Find potential duplicate crimes based on location and time"""
        with self.get_session() as session:
            # Look for crimes within 50 meters and 1 hour time window
            from sqlalchemy import text
            query = session.query(CrimeReport).filter(
                text("ST_DWithin(point, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), 50)"),
                CrimeReport.occurred_at.between(
                    crime_data['occurred_at'] - timedelta(hours=1),
                    crime_data['occurred_at'] + timedelta(hours=1)
                ),
                CrimeReport.crime_type == crime_data['crime_type']
            ).params(
                lat=crime_data['lat'], 
                lng=crime_data['lng']
            )
            return query.all()
    
    def mark_duplicate(self, duplicate_id: str, canonical_id: str):
        """Mark a crime report as duplicate of another"""
        with self.get_session() as session:
            duplicate = session.query(CrimeReport).filter(CrimeReport.id == duplicate_id).first()
            if duplicate:
                duplicate.is_duplicate = True
                duplicate.duplicate_of = canonical_id
                session.commit()
    
    def _crime_to_dict(self, crime: CrimeReport) -> Dict:
        """Convert CrimeReport object to dictionary"""
        return {
            'id': crime.id,
            'source': crime.source,
            'crime_type': crime.crime_type,
            'severity': crime.severity,
            'description': crime.description,
            'address': crime.address,
            'lat': crime.lat,
            'lng': crime.lng,
            'occurred_at': crime.occurred_at.isoformat() if crime.occurred_at else None,
            'agency': crime.agency,
            'case_number': crime.case_number
        }

# Initialize database manager
db_manager = DatabaseManager()