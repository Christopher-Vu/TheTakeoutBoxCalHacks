"""
Enhanced API endpoints for SAFEPATH crime data aggregation
Supports multiple data sources with comprehensive filtering and analytics
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from database import db_manager, CrimeReport
from data_aggregator import aggregator, SourceType
from routing import calculate_routes
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SAFEPATH Crime Data API",
    description="Multi-source crime data aggregation and routing API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
db_manager.create_tables()

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "SAFEPATH API is running"}

@app.get("/crimes")
async def get_crimes(
    min_lat: float = Query(..., description="Minimum latitude"),
    max_lat: float = Query(..., description="Maximum latitude"),
    min_lng: float = Query(..., description="Minimum longitude"),
    max_lng: float = Query(..., description="Maximum longitude"),
    crime_types: Optional[str] = Query(None, description="Comma-separated crime types"),
    severity_min: Optional[int] = Query(None, description="Minimum severity (1-10)"),
    days_back: Optional[int] = Query(30, description="Days back to include"),
    sources: Optional[str] = Query(None, description="Comma-separated data sources"),
    include_duplicates: bool = Query(False, description="Include duplicate reports")
):
    """Get crimes within geographic bounds with filtering"""
    try:
        # Parse filters
        crime_type_filter = crime_types.split(',') if crime_types else None
        source_filter = sources.split(',') if sources else None
        
        # Calculate date filter
        date_filter = datetime.utcnow() - timedelta(days=days_back)
        
        # Get crimes from database
        crimes = db_manager.get_crimes_in_bounds(min_lat, max_lat, min_lng, max_lng)
        
        # Apply filters
        filtered_crimes = []
        for crime in crimes:
            # Date filter
            if crime.get('occurred_at'):
                crime_date = datetime.fromisoformat(crime['occurred_at'].replace('Z', '+00:00'))
                if crime_date < date_filter:
                    continue
            
            # Crime type filter
            if crime_type_filter and crime['crime_type'] not in crime_type_filter:
                continue
            
            # Severity filter
            if severity_min and crime['severity'] < severity_min:
                continue
            
            # Source filter
            if source_filter and crime['source'] not in source_filter:
                continue
            
            # Duplicate filter
            if not include_duplicates and crime.get('is_duplicate', False):
                continue
            
            filtered_crimes.append(crime)
        
        return {
            "crimes": filtered_crimes,
            "total": len(filtered_crimes),
            "filters_applied": {
                "crime_types": crime_type_filter,
                "severity_min": severity_min,
                "days_back": days_back,
                "sources": source_filter,
                "include_duplicates": include_duplicates
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting crimes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crimes/near")
async def get_crimes_near(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: float = Query(100, description="Radius in meters"),
    days_back: Optional[int] = Query(7, description="Days back to include")
):
    """Get crimes near a specific point"""
    try:
        crimes = db_manager.get_crimes_near_point(lat, lng, radius)
        
        # Filter by date
        if days_back:
            date_filter = datetime.utcnow() - timedelta(days=days_back)
            filtered_crimes = []
            for crime in crimes:
                if crime.get('occurred_at'):
                    crime_date = datetime.fromisoformat(crime['occurred_at'].replace('Z', '+00:00'))
                    if crime_date >= date_filter:
                        filtered_crimes.append(crime)
            crimes = filtered_crimes
        
        return {
            "crimes": crimes,
            "total": len(crimes),
            "center": {"lat": lat, "lng": lng},
            "radius": radius
        }
        
    except Exception as e:
        logger.error(f"Error getting crimes near point: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/route")
async def calculate_route(
    start: List[float] = Query(..., description="Start coordinates [lat, lng]"),
    end: List[float] = Query(..., description="End coordinates [lat, lng]"),
    safety_weight: float = Query(0.5, description="Safety vs speed weight (0-1)")
):
    """Calculate fastest and safest routes"""
    try:
        if len(start) != 2 or len(end) != 2:
            raise HTTPException(status_code=400, detail="Invalid coordinates format")
        
        start_lat, start_lng = start
        end_lat, end_lng = end
        
        # Calculate routes using routing module
        routes = calculate_routes(start, end, safety_weight)
        
        return routes
        
    except Exception as e:
        logger.error(f"Error calculating route: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_crime_stats(
    min_lat: float = Query(..., description="Minimum latitude"),
    max_lat: float = Query(..., description="Maximum latitude"),
    min_lng: float = Query(..., description="Minimum longitude"),
    max_lng: float = Query(..., description="Maximum longitude"),
    days_back: int = Query(30, description="Days back to include")
):
    """Get crime statistics for an area"""
    try:
        # Get crimes in area
        crimes = db_manager.get_crimes_in_bounds(min_lat, max_lat, min_lng, max_lng)
        
        # Filter by date
        date_filter = datetime.utcnow() - timedelta(days=days_back)
        recent_crimes = []
        for crime in crimes:
            if crime.get('occurred_at'):
                crime_date = datetime.fromisoformat(crime['occurred_at'].replace('Z', '+00:00'))
                if crime_date >= date_filter:
                    recent_crimes.append(crime)
        
        # Calculate statistics
        stats = {
            "total_crimes": len(recent_crimes),
            "by_type": {},
            "by_severity": {},
            "by_source": {},
            "by_agency": {},
            "time_distribution": {},
            "average_severity": 0
        }
        
        if recent_crimes:
            # Count by type
            for crime in recent_crimes:
                crime_type = crime.get('crime_type', 'OTHER')
                stats["by_type"][crime_type] = stats["by_type"].get(crime_type, 0) + 1
            
            # Count by severity
            for crime in recent_crimes:
                severity = crime.get('severity', 0)
                stats["by_severity"][str(severity)] = stats["by_severity"].get(str(severity), 0) + 1
            
            # Count by source
            for crime in recent_crimes:
                source = crime.get('source', 'unknown')
                stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
            
            # Count by agency
            for crime in recent_crimes:
                agency = crime.get('agency', 'unknown')
                stats["by_agency"][agency] = stats["by_agency"].get(agency, 0) + 1
            
            # Time distribution (by hour of day)
            for crime in recent_crimes:
                if crime.get('occurred_at'):
                    try:
                        crime_date = datetime.fromisoformat(crime['occurred_at'].replace('Z', '+00:00'))
                        hour = crime_date.hour
                        stats["time_distribution"][str(hour)] = stats["time_distribution"].get(str(hour), 0) + 1
                    except:
                        pass
            
            # Average severity
            total_severity = sum(crime.get('severity', 0) for crime in recent_crimes)
            stats["average_severity"] = total_severity / len(recent_crimes)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting crime stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sync")
async def sync_data_sources():
    """Manually trigger data source synchronization"""
    try:
        results = await aggregator.sync_all_sources()
        return {
            "status": "success",
            "sync_results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error syncing data sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sources")
async def get_data_sources():
    """Get information about registered data sources"""
    try:
        with db_manager.get_session() as session:
            sources = session.query(DataSource).all()
            return {
                "sources": [
                    {
                        "id": source.id,
                        "name": source.name,
                        "type": source.source_type,
                        "last_sync": source.last_sync.isoformat() if source.last_sync else None,
                        "sync_frequency": source.sync_frequency,
                        "is_active": source.is_active
                    }
                    for source in sources
                ]
            }
    except Exception as e:
        logger.error(f"Error getting data sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sync-logs")
async def get_sync_logs(
    source_id: Optional[str] = Query(None, description="Filter by source ID"),
    limit: int = Query(50, description="Number of logs to return")
):
    """Get data synchronization logs"""
    try:
        with db_manager.get_session() as session:
            query = session.query(DataSyncLog)
            if source_id:
                query = query.filter(DataSyncLog.source_id == source_id)
            
            logs = query.order_by(DataSyncLog.sync_started.desc()).limit(limit).all()
            
            return {
                "logs": [
                    {
                        "id": log.id,
                        "source_id": log.source_id,
                        "sync_started": log.sync_started.isoformat(),
                        "sync_completed": log.sync_completed.isoformat() if log.sync_completed else None,
                        "records_processed": log.records_processed,
                        "records_added": log.records_added,
                        "records_updated": log.records_updated,
                        "records_duplicated": log.records_duplicated,
                        "status": log.status,
                        "errors": log.errors
                    }
                    for log in logs
                ]
            }
    except Exception as e:
        logger.error(f"Error getting sync logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper function for route calculation
def calculate_routes(start: List[float], end: List[float], safety_weight: float) -> Dict:
    """Calculate routes using the routing module"""
    # This would integrate with your existing routing.py
    # For now, return mock data
    return {
        "fastest_route": {
            "path": [start, end],
            "distance": 1000,
            "time": 8,
            "safety_score": 6
        },
        "safest_route": {
            "path": [start, end],
            "distance": 1200,
            "time": 11,
            "safety_score": 8
        },
        "crime_points": []
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
