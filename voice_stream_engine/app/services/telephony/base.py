from abc import ABC, abstractmethod
from fastapi import WebSocket

class TelephonyTransport(ABC):
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.stream_sid = None

    @abstractmethod
    async def process_incoming_message(self, message: str):
        """Handle raw text message from WebSocket"""
        pass

    @abstractmethod
    async def send_audio(self, audio_chunk: bytes):
        """Send raw PCM audio back to the provider"""
        pass