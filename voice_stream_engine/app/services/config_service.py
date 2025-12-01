import httpx
import json
import logging
import redis.asyncio as redis
from typing import Optional, Dict
from app.core.config import settings

logger = logging.getLogger("config_service")

class ConfigService:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.api_url = settings.MANAGEMENT_API_URL

    async def get_agent_config(self, phone_number: str) -> Optional[Dict]:
        """
        Retrieves agent configuration based on the inbound phone number.
        Strategy: Cache-Aside (Redis -> API -> Redis)
        """
        cache_key = f"agent_config:{phone_number}"
        
        # 1. Check Cache
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            logger.info(f"Using cached config for {phone_number}")
            return json.loads(cached_data)

        # 2. Fetch from SaaS Backend
        logger.info(f"Fetching config from Backend for {phone_number}")
        try:
            async with httpx.AsyncClient() as client:
                # We need an endpoint in Backend to look up by number
                # GET /api/v1/agents/lookup?phone_number=+123...
                response = await client.get(
                    f"{self.api_url}/agents/internal/lookup",
                    params={"phone_number": phone_number},
                    headers={"X-Internal-Key": settings.INTERNAL_API_KEY},
                    timeout=2.0
                )
                
                if response.status_code == 200:
                    config = response.json()
                    
                    # 3. Cache it (TTL: 5 minutes)
                    # We use a short TTL so updates in Dashboard reflect quickly
                    await self.redis.setex(cache_key, 300, json.dumps(config))
                    return config
                else:
                    logger.error(f"Config API Error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to fetch agent config: {e}")
            return None