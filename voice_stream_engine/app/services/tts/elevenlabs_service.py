import asyncio
import json
import base64
import logging
import websockets
from typing import AsyncGenerator
from app.core.config import settings

logger = logging.getLogger("tts")

class ElevenLabsService:
    def __init__(self , voice_id: str):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = voice_id 
        self.model_id = "eleven_turbo_v2_5"
        # Request 8000Hz directly to match Twilio (Zero Resampling Latency)
        self.output_format = "pcm_8000" 

    async def stream_audio(self, text_iterator: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
        """
        Bi-directional Streaming:
        - Task A: Sends text tokens to ElevenLabs.
        - Task B: Receives audio bytes from ElevenLabs.
        """
        uri = (
            f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input"
            f"?model_id={self.model_id}&output_format={self.output_format}"
        )

        async with websockets.connect(uri) as ws:
            # 1. Send Initial Configuration (BOS)
            await ws.send(json.dumps({
                "text": " ", # Initialize
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.7},
                "xi_api_key": self.api_key
            }))

            # 2. Define the Sender Task (Push Text)
            async def send_text():
                try:
                    async for text_chunk in text_iterator:
                        # Send text + a space to help TTS context
                        # ElevenLabs prefers chunks ending with space for streaming
                        payload = {"text": text_chunk + " "} 
                        await ws.send(json.dumps(payload))
                    
                    # Send EOS (End of Stream)
                    await ws.send(json.dumps({"text": ""})) 
                except Exception as e:
                    logger.error(f"TTS Send Error: {e}")

            # 3. Start Sender in background
            sender_task = asyncio.create_task(send_text())

            # 4. Main Loop: Receive Audio
            try:
                while True:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=10.0)
                        data = json.loads(message)

                        if data.get("audio"):
                            # Decode base64 audio chunk
                            chunk = base64.b64decode(data["audio"])
                            if chunk:
                                yield chunk
                        
                        if data.get("isFinal"):
                            break
                            
                    except asyncio.TimeoutError:
                        logger.warning("TTS WebSocket Timed out waiting for audio")
                        break
                        
            except websockets.exceptions.ConnectionClosed:
                logger.warning("TTS WebSocket Closed")
            finally:
                if not sender_task.done():
                    sender_task.cancel()