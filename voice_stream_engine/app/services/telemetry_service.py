import json
import time
import logging
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger("telemetry")

class TelemetryService:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.stream_key = "call_events" # Must match Worker config

    async def emit_call_ended(self, metrics: dict):
        """
        Publishes the final call summary to Redis.
        """
        event = {
            "event": "call_ended",
            "timestamp": time.time(),
            **metrics
        }
        try:
            await self.redis.xadd(self.stream_key, event)
            logger.info(f"📡 Emitted call_ended for {metrics.get('call_id')}")
        except Exception as e:
            logger.error(f"Failed to emit telemetry: {e}")

    async def emit_transcript(self, call_id: str, role: str, content: str):
        """
        Publishes live transcript lines (optional, for real-time dashboards).
        """
        event = {
            "event": "transcript",
            "call_id": call_id,
            "timestamp": time.time(),
            "role": role,
            "content": content
        }
        try:
            await self.redis.xadd(self.stream_key, event)
        except Exception as e:
            logger.error(f"Failed to emit transcript: {e}")