"""
Database initialization script
Creates tables and enables PostGIS extension automatically
"""

import asyncio
import logging
import os
from sqlalchemy import create_engine, text
from database import Base, db_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def initialize_database():
    """Initialize the PostgreSQL database with PostGIS extension and proper schema"""
    logger.info("🔧 Initializing PostgreSQL database...")
    
    try:
        # Enable PostGIS extension FIRST
        with db_manager.engine.connect() as connection:
            # Enable PostGIS extension
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            logger.info("✅ PostGIS extension enabled")
            connection.commit()

        # Create tables using SQLAlchemy (after PostGIS is enabled)
        # Check if tables already exist to avoid conflicts
        with db_manager.engine.connect() as connection:
            result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name='crimes';"))
            if result.fetchone() is None:
                Base.metadata.create_all(db_manager.engine)
                logger.info("✅ Database tables created successfully")
            else:
                logger.info("✅ Database tables already exist")
        
        logger.info("🎉 Database initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(initialize_database())