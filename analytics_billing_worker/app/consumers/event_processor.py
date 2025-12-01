import logging
import asyncio
import json
import redis.asyncio as redis
from app.core.config import settings
from app.services.cost_calculator import CostCalculator
from app.db.clickhouse import get_client as get_ch_client
from app.services.wallet_service import WalletService 

logger = logging.getLogger("event_processor")

class EventProcessor:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.stream_key = settings.REDIS_STREAM_KEY
        self.group_name = "billing_group"
        self.consumer_name = "worker_1"
        self.cost_calculator = CostCalculator()
        self.ch_client = get_ch_client()
        self.wallet_service = WalletService()

    async def setup(self):
        """Create Consumer Group if not exists"""
        try:
            await self.redis.xgroup_create(self.stream_key, self.group_name, id="0", mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def start_consuming(self):
        await self.setup()
        logger.info(f"🎧 Listening to stream: {self.stream_key}")

        while True:
            try:
                # Read new messages
                streams = await self.redis.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams={self.stream_key: ">"},
                    count=10,
                    block=2000
                )

                if not streams:
                    continue

                for stream_name, messages in streams:
                    for message_id, data in messages:
                        await self.process_message(data)
                        # Acknowledge processing
                        await self.redis.xack(self.stream_key, self.group_name, message_id)

            except Exception as e:
                logger.error(f"Error consuming events: {e}")
                await asyncio.sleep(1)

    async def process_message(self, data: dict):
        """
        Route events to logic
        """
        event_type = data.get("event")
        
        if event_type == "call_ended":
            logger.info(f"Processing Call End: {data.get('call_id')}")
            await self.handle_call_ended(data)
        elif event_type == "transcript":
            self.log_transcript(data)

    def log_transcript(self, data: dict):
        """Batch insert transcript lines to ClickHouse"""
        # In prod: Use a buffer/batcher here. For now, direct insert.
        try:
            self.ch_client.insert(
                'transcript_logs',
                [[
                    data.get('call_id'),
                    data.get('timestamp'), # Ensure ISO format
                    data.get('role'),
                    data.get('content'),
                    json.dumps(data.get('metadata', {}))
                ]],
                column_names=['call_id', 'timestamp', 'role', 'content', 'metadata']
            )
        except Exception as e:
            logger.error(f"Failed to log transcript: {e}")

    async def handle_call_ended(self, data: dict):
        """
        1. Calculate Cost
        2. Deduct from Wallet
        3. Save Metrics to ClickHouse
        """
        try:
            # 1. Calculate
            cost_details = await self.cost_calculator.calculate(data)
            total_cost = cost_details['total_cost']
            
            # 2. Billing (Deduct)
            tenant_id = data.get('tenant_id')
            call_id = data.get('call_id')
            # 2. Billing (Execute Deduction)
            if tenant_id and total_cost > 0:
                await self.wallet_service.deduct_balance(tenant_id, total_cost, call_id)
            
            # await self.wallet_service.deduct_balance(tenant_id, total_cost, call_id)
            logger.info(f"💰 Billing Tenant {tenant_id}: ${total_cost:.4f}")

            # 3. Analytics
            self.ch_client.insert(
                'call_metrics',
                [[
                    call_id,
                    tenant_id,
                    data.get('agent_id'),
                    data.get('start_time'),
                    data.get('end_time'),
                    float(data.get('duration_seconds', 0)),
                    data.get('status'),
                    total_cost,
                    data.get('end_reason'),
                    0.0 # Sentiment placeholder
                ]],
                column_names=['call_id', 'tenant_id', 'agent_id', 'start_time', 'end_time', 'duration_seconds', 'status', 'cost', 'end_reason', 'sentiment_score']
            )
        except Exception as e:
            logger.error(f"Failed to process call_ended: {e}")