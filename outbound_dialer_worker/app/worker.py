import logging
import asyncio
from arq.connections import RedisSettings
from app.core.config import settings
from app.services.throttler import Throttler
from app.services.telephony.twilio_dialer import TwilioDialer
from app.services.campaign.loader import CampaignLoader

logger = logging.getLogger("worker")

async def startup(ctx):
    """Initialize services on worker start"""
    ctx['dialer'] = TwilioDialer()
    logger.info("🚀 Outbound Dialer Worker Started")

async def shutdown(ctx):
    logger.info("🛑 Outbound Dialer Worker Stopped")

async def dial_number_job(ctx, phone_number: str, campaign_id: str, tenant_id: str, agent_id: str, customer_name: str = None):
    # Pass customer_name to the dialer so it can be sent to Voice Engine via query params
    dialer: TwilioDialer = ctx['dialer']
    throttler = Throttler(tenant_id, limit_cps=1) # Fetch real limit from DB in prod
    await throttler.wait_for_slot()
    
    await dialer.place_call(phone_number, campaign_id, tenant_id, agent_id, customer_name)

async def load_campaign_job(ctx, file_content: bytes, campaign_id: str, tenant_id: str, agent_id: str):
    """
    Job to parse CSV and spawn child jobs.
    """
    await CampaignLoader.load_and_enqueue(file_content, campaign_id, tenant_id, agent_id, ctx['redis'])

# ARQ Worker Settings
class WorkerSettings:
    functions = [dial_number_job]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10 # Concurrency