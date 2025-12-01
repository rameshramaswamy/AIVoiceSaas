import logging
from twilio.rest import Client
from app.core.config import settings

logger = logging.getLogger("dialer")

class TwilioDialer:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    async def place_call(self, to_number: str, campaign_id: str, tenant_id: str, agent_id: str, customer_name: str = None):
        """
        Initiates an outbound call.
        """
        try:
            # Construct the Webhook URL
            # We append query params so the Voice Engine knows who picked up
            # URL Encode the name
            import urllib.parse
            name_param = f"&customer_name={urllib.parse.quote(customer_name)}" if customer_name else ""

            webhook_url = (
                f"{settings.VOICE_ENGINE_URL}"
                f"?campaign_id={campaign_id}"
                f"&tenant_id={tenant_id}"
                f"&agent_id={agent_id}"
                f"&direction=outbound"
                f"{name_param}"
            )

            call = self.client.calls.create(
                to=to_number,
                from_=settings.TWILIO_FROM_NUMBER,
                url=webhook_url, # Twilio POSTs here when user picks up
                
                # Answering Machine Detection (AMD)
                machine_detection='Enable', 
                machine_detection_timeout=30, # Wait up to 30s for greeting
                # If machine detected, Twilio passes 'AnsweredBy': 'machine_start' to webhook
                async_amd='true' # Don't block connection, detect in background
            )
            
            logger.info(f"☎️ Dialed {to_number}: SID {call.sid}")
            return call.sid

        except Exception as e:
            logger.error(f"Failed to dial {to_number}: {e}")
            raise