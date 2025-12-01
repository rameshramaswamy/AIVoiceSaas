import asyncio
import logging
from app.core.config import settings
from app.consumers.event_processor import EventProcessor
from app.db.clickhouse import init_clickhouse

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("worker")

async def main():
    logger.info("🚀 Starting Analytics & Billing Worker...")
    
    # 1. Initialize Analytics DB
    init_clickhouse()
    
    # 2. Start Event Processor
    processor = EventProcessor()
    
    try:
        await processor.start_consuming()
    except KeyboardInterrupt:
        logger.info("Stopping worker...")

if __name__ == "__main__":
    asyncio.run(main())