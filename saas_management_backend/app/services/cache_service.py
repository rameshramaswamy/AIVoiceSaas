import redis.asyncio as redis
from app.core.config import settings

class CacheService:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def invalidate_agent_config(self, phone_number: str):
        """
        Deletes the cached configuration for a specific phone number.
        Forces the Voice Engine to refetch fresh data from DB on the next call.
        """
        if phone_number:
            key = f"agent_config:{phone_number}"
            await self.redis.delete(key)