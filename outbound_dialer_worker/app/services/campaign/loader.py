import pandas as pd
import logging
import io
from app.db.redis_queue import enqueue_job # We'll define this helper
from app.core.config import settings

logger = logging.getLogger("campaign_loader")

class CampaignLoader:
    @staticmethod
    async def load_and_enqueue(file_content: bytes, campaign_id: str, tenant_id: str, agent_id: str, redis_pool):
        """
        Parses CSV/Excel and enqueues 'dial_number_job' for each row.
        """
        try:
            # 1. Parse File
            # Detect format based on content or extension (assuming csv for simplicity here)
            try:
                df = pd.read_csv(io.BytesIO(file_content))
            except:
                df = pd.read_excel(io.BytesIO(file_content))

            # Normalize headers
            df.columns = [c.lower() for c in df.columns]
            
            if 'phone' not in df.columns:
                raise ValueError("CSV must contain a 'phone' column.")

            count = 0
            for _, row in df.iterrows():
                phone = str(row['phone'])
                name = row.get('name', 'there') # Default name if missing
                
                # Basic normalization
                if not phone.startswith('+'):
                    # Assume US/Default country code if missing
                    phone = f"+1{phone.strip()}"

                # 2. Enqueue Job
                await redis_pool.enqueue_job(
                    'dial_number_job',
                    phone_number=phone,
                    campaign_id=campaign_id,
                    tenant_id=tenant_id,
                    agent_id=agent_id,
                    customer_name=name
                )
                count += 1
            
            logger.info(f"✅ Campaign {campaign_id}: Enqueued {count} calls.")
            return count

        except Exception as e:
            logger.error(f"Failed to load campaign: {e}")
            raise