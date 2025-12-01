import asyncio
from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings

async def main():
    redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    
    print("enqueueing call...")
    await redis.enqueue_job(
        'dial_number_job',
        phone_number="+15550000000", # REPLACE WITH REAL VERIFIED NUMBER
        campaign_id="test_camp_1",
        tenant_id="tenant_123",
        agent_id="agent_456"
    )
    print("Job Enqueued.")
    await redis.close()

if __name__ == "__main__":
    asyncio.run(main())