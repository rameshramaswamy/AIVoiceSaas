import audioop
import base64

class AudioUtils:
    @staticmethod
    def mulaw_to_pcm(base64_audio: str) -> bytes:
        """
        Convert Twilio G.711 mu-law (8kHz) to Raw PCM (16-bit Signed).
        """
        # 1. Decode base64
        audio_bytes = base64.b64decode(base64_audio)
        # 2. Convert mu-law to 16-bit linear PCM
        # Width 2 = 16-bit
        return audioop.ulaw2lin(audio_bytes, 2)

    @staticmethod
    def pcm_to_mulaw(pcm_bytes: bytes) -> str:
        """
        Convert Raw PCM (16-bit Signed) back to G.711 mu-law base64
        for Twilio playback.
        """
        # 1. Convert 16-bit linear PCM to mu-law
        mulaw_bytes = audioop.lin2ulaw(pcm_bytes, 2)
        # 2. Encode to base64
        return base64.b64encode(mulaw_bytes).decode('utf-8')

    @staticmethod
    def create_twilio_media_event(stream_sid: str, payload: str) -> dict:
        """
        Construct the JSON payload Twilio expects for outbound audio.
        """
        return {
            "event": "media",
            "streamSid": stream_sid,
            "media": {
                "payload": payload
            }
        }