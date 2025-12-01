import logging
import json
from typing import AsyncGenerator, Callable
from deepgram import DeepgramClient, DeepgramClientOptions, LiveOptions, LiveTranscriptionEvents
from app.core.config import settings

logger = logging.getLogger("stt")

class DeepgramService:
    def __init__(self, on_transcript: Callable, on_speech_start: Callable):
        self.on_transcript = on_transcript
        self.on_speech_start = on_speech_start
        self.dg_client = DeepgramClient(settings.DEEPGRAM_API_KEY)
        self.dg_connection = None

    async def connect(self):
        """Initialize Deepgram WebSocket Connection"""
        try:
            # Create a websocket connection to Deepgram
            self.dg_connection = self.dg_client.listen.live.v("1")

            # Register Event Handlers
            self.dg_connection.on(LiveTranscriptionEvents.Transcript, self._handle_transcript)
            self.dg_connection.on(LiveTranscriptionEvents.SpeechStarted, self._handle_speech_start)
            
            # Configure Options (Nova-2 is fastest model)
            options = LiveOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                encoding="linear16", # Raw PCM
                channels=1,
                sample_rate=8000,    # Twilio Mulaw is 8000Hz
                interim_results=True,
                vad_events=True,     # Critical for interruption
                endpointing=300      # 300ms silence = end of sentence
            )

            if await self.dg_connection.start(options) is False:
                logger.error("Failed to connect to Deepgram")
                return False
            
            logger.info("Deepgram Connected")
            return True

        except Exception as e:
            logger.error(f"Deepgram connection error: {e}")
            return False

    async def send_audio(self, audio_chunk: bytes):
        """Stream raw audio to Deepgram"""
        if self.dg_connection:
            await self.dg_connection.send(audio_chunk)

    async def finish(self):
        if self.dg_connection:
            await self.dg_connection.finish()

    def _handle_speech_start(self, *args, **kwargs):
        """Triggered immediately when VAD detects voice"""
        # This is the "Kill Switch" for TTS
        self.on_speech_start()

    def _handle_transcript(self, *args, **kwargs):
        """Process transcription results"""
        try:
            result = kwargs.get('result')
            if not result: 
                return
                
            channel = result.channel
            alternatives = channel.alternatives
            
            if alternatives:
                text = alternatives[0].transcript
                is_final = result.is_final
                
                # We only care about non-empty transcripts
                if len(text.strip()) > 0:
                    self.on_transcript(text, is_final)
        except Exception as e:
            logger.error(f"Error handling transcript: {e}")