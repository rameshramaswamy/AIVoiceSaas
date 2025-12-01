import time
import redis.asyncio as redis
from app.core.config import settings

class Throttler:
    def __init__(self, tenant_id: str, limit_cps: int = 1):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.tenant_id = tenant_id
        self.limit = limit_cps
        self.key = f"throttle:{tenant_id}"

    async def acquire(self) -> bool:
        """
        Returns True if call can proceed, False if throttled.
        Implementation: Simple Fixed Window Counter for 1 second.
        For stricter limits, use Leaky Bucket.
        """
        current_second = int(time.time())
        bucket_key = f"{self.key}:{current_second}"
        
        # Increment counter for this second
        count = await self.redis.incr(bucket_key)
        
        # Set expiry (cleanup)
        if count == 1:
            await self.redis.expire(bucket_key, 5) # 5 sec safety buffer
            
        if count > self.limit:
            return False
        
        return True

    async def wait_for_slot(self):
        """Blocking helper that waits until a slot is open"""
        while not await self.acquire():
            # Wait 100ms before retrying
            await asyncio.sleep(0.1)