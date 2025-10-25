import asyncio
import aiohttp
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_pagination():
    """Test pagination with a small sample"""
    async with aiohttp.ClientSession() as session:
        all_data = []
        offset = 0
        limit = 100  # Small limit for testing
        max_records = 500  # Only fetch 500 records for testing
        
        logger.info("Testing pagination with small sample...")
        
        while len(all_data) < max_records:
            url = f"https://data.sfgov.org/resource/wg3w-h783.json?$limit={limit}&$offset={offset}"
            
            logger.info(f"Fetching records {offset} to {offset + limit}...")
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if not data or len(data) == 0:
                        logger.info("No more data available")
                        break
                    
                    all_data.extend(data)
                    logger.info(f"Fetched {len(data)} records (total: {len(all_data)})")
                    
                    if len(data) < limit:
                        logger.info("Reached end of data")
                        break
                    
                    offset += limit
                    await asyncio.sleep(0.1)
                else:
                    logger.error(f"API error: {response.status}")
                    break
        
        logger.info(f"Pagination test complete. Total records: {len(all_data)}")
        return all_data

if __name__ == "__main__":
    asyncio.run(test_pagination())
