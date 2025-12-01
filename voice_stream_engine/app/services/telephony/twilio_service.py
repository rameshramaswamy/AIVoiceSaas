import json
import logging
from app.services.telephony.base import TelephonyTransport
from app.utils.audio import AudioUtils

logger = logging.getLogger(__name__)

class TwilioTransport(TelephonyTransport):
    async def process_incoming_message(self, message: str):
        """
        Parses Twilio WebSocket messages.
        Returns: bytes (PCM Audio) or None (Control Event)
        """
        data = json.loads(message)
        event_type = data.get("event")

        if event_type == "connected":
            logger.info(f"Twilio: Connected - Protocol: {data.get('protocol')}")
            return None

        elif event_type == "start":
            self.stream_sid = data['start']['streamSid']
            logger.info(f"Twilio: Stream Started - SID: {self.stream_sid}")
            return None

        elif event_type == "media":
            # This is the hot path (Audio Packet)
            payload = data['media']['payload']
            # Convert to PCM immediately
            pcm_data = AudioUtils.mulaw_to_pcm(payload)
            return pcm_data

        elif event_type == "stop":
            logger.info("Twilio: Stream Stopped")
            return None
            
        elif event_type == "mark":
            # Used for bidirectional latency tracking
            return None

        return None

    async def send_audio(self, audio_chunk: bytes):
        """
        Encodes PCM -> Mu-law -> Base64 -> WebSocket JSON
        """
        if not self.stream_sid:
            logger.warning("Attempted to send audio with no active Stream SID")
            return

        base64_payload = AudioUtils.pcm_to_mulaw(audio_chunk)
        response = AudioUtils.create_twilio_media_event(self.stream_sid, base64_payload)
        
        await self.websocket.send_json(response)

    async def send_clear_message(self):
        """
        Sends a 'clear' event to Twilio to interrupt playback immediately.
        """
        if not self.stream_sid:
            return
            
        msg = {
            "event": "clear",
            "streamSid": self.stream_sid
        }
        await self.websocket.send_json(msg)