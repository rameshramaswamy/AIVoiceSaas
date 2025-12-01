import json
import time
import base64
import gevent
from locust import User, task, events, constant
from websocket import create_connection

# Mock Audio Chunk (100ms of silence in mu-law)
# In a real test, you might load a real audio file
MOCK_PAYLOAD = "ff" * 800 # Hex representation of silence
MOCK_PAYLOAD_B64 = base64.b64encode(bytes.fromhex(MOCK_PAYLOAD)).decode("utf-8")

class VoiceUser(User):
    # Simulate a user waiting 1-3 seconds between "turns"
    wait_time = constant(1) 
    
    def on_start(self):
        """
        Simulate Twilio connecting to the server.
        """
        self.call_sid = f"Call_{time.time()}"
        self.ws_url = "ws://voice-engine:8000/api/v1/voice/stream"
        self.ws = None
        self.connect()

    def connect(self):
        start_time = time.time()
        try:
            self.ws = create_connection(self.ws_url)
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="ws_connect",
                name="connect",
                response_time=total_time,
                response_length=0,
            )
            
            # Send Twilio "start" event
            start_msg = {
                "event": "start",
                "start": {
                    "streamSid": self.call_sid,
                    "callSid": self.call_sid,
                    "customParameters": {"phone_number": "+15550000000"} # Test Agent
                }
            }
            self.ws.send(json.dumps(start_msg))
            
            # Spawn a listener thread (Greenlet) to read responses
            gevent.spawn(self.receive_loop)

        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request.fire(
                request_type="ws_connect",
                name="connect",
                response_time=total_time,
                exception=e,
            )

    def receive_loop(self):
        """
        Continuously listen for audio back from the server.
        """
        while True:
            try:
                message = self.ws.recv()
                data = json.loads(message)
                
                if data['event'] == 'media':
                    # We received audio!
                    # In a real test, we would correlate this with the sent packet ID to calc specific latency.
                    # For stress testing, we just verify the server is responding.
                    pass
                elif data['event'] == 'mark':
                    pass
                    
            except Exception:
                # Connection closed
                break

    @task
    def speak(self):
        """
        Simulate the user speaking (streaming audio chunks).
        """
        if not self.ws or not self.ws.connected:
            return

        # Simulate sending 1 second of audio (10 chunks of 100ms)
        for _ in range(10):
            msg = {
                "event": "media",
                "media": {
                    "payload": MOCK_PAYLOAD_B64,
                    "timestamp": str(int(time.time() * 1000))
                }
            }
            
            start_time = time.time()
            try:
                self.ws.send(json.dumps(msg))
                # Note: We don't fire an event for every packet to avoid clogging Locust logs
                # We assume if the socket doesn't crash, write is successful.
            except Exception as e:
                events.request.fire(
                    request_type="ws_send",
                    name="media",
                    response_time=0,
                    exception=e,
                )
                break
            
            gevent.sleep(0.1) # Wait 100ms (Real-time simulation)

    def on_stop(self):
        if self.ws:
            self.ws.close()