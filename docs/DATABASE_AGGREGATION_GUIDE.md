# SAFEPATH Database Aggregation System

## Overview

This system aggregates crime data from multiple sources, cleans and standardizes it, and provides a unified API for the SAFEPATH routing application. It's designed to handle data from various law enforcement agencies and public sources.

## Architecture

### Data Sources Supported

1. **CommunityCrimeMap.com** - Primary source via web scraping
2. **Berkeley PD Open Data** - Official Berkeley Police Department data
3. **UCPD Crime Log** - UC Berkeley Police Department data
4. **Manual Entry** - For testing and data correction
5. **News Scrapers** - Additional sources for comprehensive coverage

### Key Components

- **Database Schema** (`backend/database.py`) - PostgreSQL with PostGIS for geospatial data
- **Data Aggregator** (`backend/data_aggregator.py`) - Multi-source data collection
- **Data Cleaner** (`scraper/data_cleaner.py`) - Standardization and deduplication
- **Geocoding Service** (`scraper/geocoder.py`) - Address to coordinates conversion
- **API Endpoints** (`backend/main.py`) - RESTful API for data access

## Setup Instructions

### 1. Database Setup

```bash
# Install PostgreSQL with PostGIS extension
# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib postgis

# macOS:
brew install postgresql postgis

# Create database
createdb safepath
psql safepath -c "CREATE EXTENSION postgis;"
```

### 2. Environment Configuration

Create `.env` file in backend directory:

```env
DATABASE_URL=postgresql://username:password@localhost/safepath
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
python -c "from database import db_manager; db_manager.create_tables()"
```

## Usage

### Starting the API Server

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints

#### Get Crimes in Area
```bash
GET /crimes?min_lat=37.85&max_lat=37.89&min_lng=-122.28&max_lng=-122.25
```

#### Get Crimes Near Point
```bash
GET /crimes/near?lat=37.8719&lng=-122.2585&radius=100
```

#### Get Crime Statistics
```bash
GET /stats?min_lat=37.85&max_lat=37.89&min_lng=-122.28&max_lng=-122.25&days_back=30
```

#### Sync Data Sources
```bash
POST /sync
```

## Data Sources Configuration

### CommunityCrimeMap Integration

The system can scrape CommunityCrimeMap.com for crime data. This requires:

1. **Selenium WebDriver** for JavaScript-heavy pages
2. **Rate limiting** to respect the website
3. **Data parsing** for various crime types

### Berkeley PD Open Data

Berkeley provides official crime data through their open data portal:

- **API Endpoint**: `https://data.cityofberkeley.info/api/views/k2nh-s5h5/rows.json`
- **Update Frequency**: Daily
- **Data Format**: JSON with standardized fields

### UCPD Integration

UC Berkeley Police Department provides crime logs:

- **Source**: `https://police.berkeley.edu/crime-log/`
- **Format**: HTML tables requiring scraping
- **Update Frequency**: Daily

## Data Processing Pipeline

### 1. Data Collection
- Automated scraping from multiple sources
- API calls to official data feeds
- Manual data entry for corrections

### 2. Data Cleaning
- **Address Standardization**: Convert various address formats to standard format
- **Crime Type Mapping**: Standardize crime classifications across sources
- **Geocoding**: Convert addresses to GPS coordinates
- **Quality Scoring**: Rate data quality (0-1 scale)

### 3. Deduplication
- **Spatial Deduplication**: Remove crimes within 50 meters of each other
- **Temporal Deduplication**: Remove crimes within 1 hour of each other
- **Type Matching**: Ensure similar crime types are grouped

### 4. Database Storage
- **PostgreSQL** with **PostGIS** for geospatial queries
- **Spatial Indexing** for fast geographic searches
- **JSONB** for flexible metadata storage

## Data Quality Features

### Quality Scoring
Each crime record receives a quality score (0-1) based on:
- **Completeness**: Required fields present
- **Recency**: Newer crimes score higher
- **Location Precision**: Accurate coordinates
- **Source Reliability**: Official sources score higher

### Deduplication Rules
- **Location Threshold**: 50 meters
- **Time Threshold**: 1 hour
- **Type Similarity**: 80% match required
- **Quality Preference**: Higher quality records are kept

## API Features

### Filtering Options
- **Geographic Bounds**: min/max lat/lng
- **Crime Types**: Filter by specific crime types
- **Severity Range**: Minimum severity threshold
- **Time Range**: Days back to include
- **Data Sources**: Filter by source
- **Duplicate Handling**: Include/exclude duplicates

### Analytics
- **Crime Statistics**: Counts by type, severity, source
- **Time Distribution**: Crimes by hour of day
- **Geographic Analysis**: Crime density mapping
- **Trend Analysis**: Crime patterns over time

## Monitoring and Maintenance

### Sync Logs
Track data synchronization:
- **Success/Failure Status**
- **Records Processed**
- **Processing Time**
- **Error Logs**

### Data Source Health
Monitor source availability:
- **Last Sync Time**
- **Success Rate**
- **Error Frequency**
- **Data Quality Trends**

## Performance Optimization

### Database Indexing
- **Spatial Indexes**: PostGIS GIST indexes for geographic queries
- **Composite Indexes**: Multi-column indexes for common queries
- **Partial Indexes**: Indexes on filtered data subsets

### Caching
- **Geocoding Cache**: Avoid repeated address lookups
- **Query Results**: Cache frequent API responses
- **Source Data**: Cache scraped data temporarily

### Rate Limiting
- **API Rate Limits**: Respect external API limits
- **Scraping Delays**: Avoid overwhelming target websites
- **Batch Processing**: Process data in batches

## Troubleshooting

### Common Issues

1. **Geocoding Failures**
   - Check API keys
   - Verify address formats
   - Use fallback geocoding services

2. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check connection string
   - Ensure PostGIS extension is installed

3. **Scraping Failures**
   - Check website changes
   - Update selectors
   - Implement rate limiting

4. **Data Quality Issues**
   - Review cleaning rules
   - Adjust quality scoring
   - Manual data correction

### Debugging Tools

- **API Logs**: Detailed request/response logging
- **Database Queries**: SQL query performance monitoring
- **Sync Status**: Real-time sync monitoring
- **Data Validation**: Automated data quality checks

## Future Enhancements

### Planned Features
- **Machine Learning**: Crime prediction models
- **Real-time Updates**: WebSocket connections
- **Mobile API**: Optimized mobile endpoints
- **Advanced Analytics**: Crime pattern analysis
- **Data Visualization**: Interactive dashboards

### Scalability Improvements
- **Microservices**: Split into smaller services
- **Message Queues**: Asynchronous processing
- **Load Balancing**: Multiple API instances
- **Database Sharding**: Distribute data across servers

## Security Considerations

### Data Privacy
- **PII Removal**: Strip personal information
- **Location Generalization**: Round coordinates for privacy
- **Access Controls**: Restrict API access
- **Audit Logging**: Track data access

### API Security
- **Rate Limiting**: Prevent abuse
- **Authentication**: API key management
- **Input Validation**: Sanitize user inputs
- **CORS Configuration**: Proper cross-origin settings

## Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Implement changes
4. Add tests
5. Submit pull request

### Code Standards
- **Python**: PEP 8 style guide
- **Documentation**: Docstring format
- **Testing**: Unit and integration tests
- **Type Hints**: Use type annotations

## Support

For issues and questions:
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check this guide and API docs
- **Community**: Join our Discord server
- **Email**: Contact the development team
