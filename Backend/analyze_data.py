#!/usr/bin/env python3
"""
Analyze crime data to understand the structure and identify issues
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
import sys
import os
import aiohttp

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_sources_config import CRIME_DATA_SOURCES, API_ENDPOINTS, RATE_LIMITS
from real_time_fetcher import RealTimeFetcher

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataAnalyzer:
    """Analyze crime data structure and identify issues"""
    
    def __init__(self):
        self.fetcher = RealTimeFetcher()
        self.analysis_results = {
            'total_records': 0,
            'records_with_coordinates': 0,
            'records_without_coordinates': 0,
            'datetime_issues': 0,
            'geocoding_issues': 0,
            'sample_records': [],
            'coordinate_analysis': {},
            'datetime_analysis': {}
        }
    
    async def analyze_data_sources(self):
        """Analyze data from all sources"""
        logger.info("🔍 Analyzing Crime Data Sources...")
        
        try:
            # Get raw data from sources
            for source_name, config in CRIME_DATA_SOURCES.items():
                if not config.is_active:
                    continue
                    
                logger.info(f"📊 Analyzing {source_name}...")
                
                try:
                    # Fetch raw data directly from the source
                    if source_name == "sf_police":
                        # Initialize session if not already done
                        if not self.fetcher.session:
                            self.fetcher.session = aiohttp.ClientSession()
                        
                        raw_data = await self.fetcher._fetch_sf_police(config)
                        # Limit to first 50 rows for testing
                        if raw_data and len(raw_data) > 50:
                            raw_data = raw_data[:50]
                            logger.info(f"Limited to first 50 rows for testing")
                    else:
                        logger.warning(f"Unknown source: {source_name}")
                        continue
                    
                    if raw_data:
                        self._analyze_source_data(source_name, raw_data)
                        
                except Exception as e:
                    logger.error(f"Failed to analyze {source_name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
    
    def _analyze_source_data(self, source_name: str, raw_data: List[Dict]):
        """Analyze data from a specific source"""
        logger.info(f"📈 Analyzing {len(raw_data)} records from {source_name}")
        
        for i, record in enumerate(raw_data[:10]):  # Analyze first 10 records
            self.analysis_results['total_records'] += 1
            
            # Check coordinates
            has_coords = self._check_coordinates(record)
            if has_coords:
                self.analysis_results['records_with_coordinates'] += 1
            else:
                self.analysis_results['records_without_coordinates'] += 1
            
            # Check datetime
            datetime_issue = self._check_datetime(record)
            if datetime_issue:
                self.analysis_results['datetime_issues'] += 1
            
            # Store sample record
            if i < 3:  # Store first 3 records as samples
                self.analysis_results['sample_records'].append({
                    'source': source_name,
                    'record': record,
                    'has_coordinates': has_coords,
                    'datetime_issue': datetime_issue
                })
    
    def _check_coordinates(self, record: Dict) -> bool:
        """Check if record has valid coordinates"""
        try:
            lat = record.get('lat')
            lng = record.get('lng')
            
            if lat is None or lng is None:
                return False
                
            # Check if coordinates are valid numbers
            float(lat)
            float(lng)
            
            # Check if coordinates are in reasonable range (San Francisco area)
            if 37.0 <= float(lat) <= 38.0 and -123.0 <= float(lng) <= -121.0:
                return True
            else:
                logger.warning(f"Coordinates out of range: lat={lat}, lng={lng}")
                return False
                
        except (ValueError, TypeError):
            return False
    
    def _check_datetime(self, record: Dict) -> bool:
        """Check if record has datetime issues"""
        try:
            date_str = record.get('date', '')
            time_str = record.get('time', '')
            
            if not date_str:
                return True  # Missing date is an issue
            
            # Try to parse the date
            from datetime import datetime
            date_formats = [
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%m-%d-%Y'
            ]
            
            for fmt in date_formats:
                try:
                    datetime.strptime(date_str.strip(), fmt)
                    return False  # No issue found
                except ValueError:
                    continue
            
            return True  # Could not parse date
            
        except Exception:
            return True
    
    def print_analysis_report(self):
        """Print detailed analysis report"""
        logger.info("📊 DATA ANALYSIS REPORT")
        logger.info("=" * 50)
        
        # Basic stats
        logger.info(f"Total records analyzed: {self.analysis_results['total_records']}")
        logger.info(f"Records with coordinates: {self.analysis_results['records_with_coordinates']}")
        logger.info(f"Records without coordinates: {self.analysis_results['records_without_coordinates']}")
        logger.info(f"Records with datetime issues: {self.analysis_results['datetime_issues']}")
        
        # Coordinate analysis
        coord_percentage = (self.analysis_results['records_with_coordinates'] / 
                          max(self.analysis_results['total_records'], 1)) * 100
        logger.info(f"Coordinate coverage: {coord_percentage:.1f}%")
        
        # Sample records
        logger.info("\n📋 SAMPLE RECORDS:")
        for i, sample in enumerate(self.analysis_results['sample_records']):
            logger.info(f"\n--- Sample {i+1} from {sample['source']} ---")
            logger.info(f"Has coordinates: {sample['has_coordinates']}")
            logger.info(f"Datetime issue: {sample['datetime_issue']}")
            logger.info(f"Record keys: {list(sample['record'].keys())}")
            
            # Show coordinate values if they exist
            if 'lat' in sample['record'] and 'lng' in sample['record']:
                logger.info(f"Coordinates: lat={sample['record']['lat']}, lng={sample['record']['lng']}")
            
            # Show datetime values
            if 'date' in sample['record']:
                logger.info(f"Date: {sample['record']['date']}")
            if 'time' in sample['record']:
                logger.info(f"Time: {sample['record']['time']}")
        
        # Recommendations
        logger.info("\n🎯 RECOMMENDATIONS:")
        if self.analysis_results['records_with_coordinates'] > 0:
            logger.info("✅ Data has coordinates - geocoding may not be needed")
        else:
            logger.info("❌ Data missing coordinates - geocoding required")
            
        if self.analysis_results['datetime_issues'] > 0:
            logger.info("⚠️  Datetime parsing issues detected - need better parsing")
        else:
            logger.info("✅ Datetime parsing looks good")
        
        # Save detailed report
        with open('data_analysis_report.json', 'w') as f:
            json.dump(self.analysis_results, f, indent=2, default=str)
        logger.info(f"\n📁 Detailed report saved to: data_analysis_report.json")

async def main():
    """Main analysis function"""
    logger.info("🚀 Starting Crime Data Analysis")
    logger.info("=" * 50)
    
    try:
        analyzer = DataAnalyzer()
        await analyzer.analyze_data_sources()
        analyzer.print_analysis_report()
        
        logger.info("\n✅ Analysis complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
