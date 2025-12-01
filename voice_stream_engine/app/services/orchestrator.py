import asyncio
import logging
import time
from fastapi import WebSocket, WebSocketDisconnect
from app.services.telephony.twilio_service import TwilioTransport
from app.services.stt.deepgram_service import DeepgramService
from app.services.llm.openai_service import OpenAIService
from app.services.tts.elevenlabs_service import ElevenLabsService
from app.services.rag.retrieval_service import RetrievalService
from app.services.tools.executor import ToolExecutor 
from app.services.telemetry_service import TelemetryService
from app.security.pii_redactor import PIIRedactor

logger = logging.getLogger("orchestrator")

class StreamOrchestrator:
    def __init__(self, websocket: WebSocket, agent_config: dict):
        self.websocket = websocket
        self.config = agent_config 
        self.tenant_id = self.config.get("tenant_id")
        self.transport = TwilioTransport(websocket)
        self.stt = DeepgramService(self.on_transcript, self.on_interruption)
        self.llm = OpenAIService(system_prompt=self.config.get("system_prompt"))
        self.tts = ElevenLabsService(voice_id=self.config.get("voice_id"))
        self.rag = RetrievalService() 
        self.conversation_history = []
        self.is_ai_speaking = False
        self.interrupt_event = asyncio.Event()
        self.tool_executor = ToolExecutor()
        self.telemetry = TelemetryService()

        # Metrics State
        self.call_id = str(uuid.uuid4())
        self.start_time = time.time()
        self.metrics = {
            "call_id": self.call_id,
            "tenant_id": self.config.get("tenant_id"),
            "agent_id": self.config.get("id"),
            "input_tokens": 0,
            "output_tokens": 0,
            "tts_characters": 0,
            "status": "completed"
        }

    async def handle_stream(self):
        await self.websocket.accept()
        if not await self.stt.connect():
            await self.websocket.close()
            return
        
        # --- OUTBOUND LOGIC START ---
        if self.call_context.get("direction") == "outbound":
            answered_by = self.call_context.get("answered_by")
            
            if answered_by == "machine_start":
                logger.info("🤖 Answering Machine Detected.")
                # Logic: Leave voicemail or hang up
                # For now, let's hang up to save money
                logger.info("Hanging up on machine.")
                return # Exits loop, closes socket
                
            elif answered_by == "human" or answered_by is None:
                # Initiate conversation
                logger.info("👤 Human Detected. Starting conversation.")
                name = self.call_context.get("customer_name", "there")
                
                # Dynamic Greeting
                opening_line = f"Hello {name}, I am calling from Acme Corp. Is this a good time?"
                
                # We artificially inject this into the history so the LLM knows it "said" it
                self.conversation_history.append({"role": "assistant", "content": opening_line})
                
                # Speak it immediately
                asyncio.create_task(self.tts_speak_immediate(opening_line))
        # --- OUTBOUND LOGIC END ---

        try:
            while True:
                message = await self.websocket.receive_text()
                audio_chunk = await self.transport.process_incoming_message(message)
                if audio_chunk:
                    await self.stt.send_audio(audio_chunk)
        except WebSocketDisconnect:
            logger.info("Client disconnected")
        except Exception as e:
            self.metrics["status"] = "failed"
            self.metrics["end_reason"] = str(e)
            logger.error(f"Stream error: {e}")
        finally:
            # CALL ENDED LOGIC
            duration = time.time() - self.start_time
            self.metrics["duration_seconds"] = duration
            self.metrics["end_time"] = time.time()
            
            # Flush Telemetry
            await self.telemetry.emit_call_ended(self.metrics)
            await self.stt.finish()

    async def tts_speak_immediate(self, text: str):
        """Helper to speak text without LLM generation"""
        self.is_ai_speaking = True
        try:
            # Create a simple generator that yields the text
            async def text_gen():
                yield text
            
            async for audio in self.tts.stream_audio(text_gen()):
                await self.transport.send_audio(audio)
        finally:
            self.is_ai_speaking = False

    def on_interruption(self):
        if self.is_ai_speaking:
            logger.info("⚠️ INTERRUPTION: Clearing Queues")
            self.interrupt_event.set()
            asyncio.create_task(self.transport.send_clear_message())

    def on_transcript(self, text: str, is_final: bool):
        if is_final and text.strip():
            logger.info(f"User: {text}")
            clean_text = self.pii_redactor.redact_text(text)
            self.conversation_history.append({"role": "user", "content": clean_text})
            asyncio.create_task(self.process_turn())


    async def process_turn(self):
        """
        Manages the Turn Loop: LLM -> Tool -> LLM -> Tool -> TTS
        """
        self.is_ai_speaking = True
        self.interrupt_event.clear()

        # 1. Prepare Context (RAG)
        # (Same RAG logic as Phase 3.3)
        current_messages = self.conversation_history # + RAG injection if applicable
        
        # 2. Tool/Generation Loop (Max 3 turns to prevent infinite loops)
        for _ in range(3): 
            if self.interrupt_event.is_set(): break
            
            should_continue = await self._run_llm_step(current_messages)
            if not should_continue:
                break
        
        self.is_ai_speaking = False

    async def _run_llm_step(self, messages) -> bool:
        """
        Runs one step of LLM generation. 
        Returns True if a tool was called and we need to run again.
        Returns False if text was generated (turn over).
        """
        llm_stream = self.llm.get_response_stream_with_tools(messages)
        
        full_response_text = []
        tool_requests = None

        # Wrapper to handle the mixed stream (Text vs Dict)
        async def stream_processor():
            nonlocal tool_requests
            async for item in llm_stream:
                if isinstance(item, str):
                    full_response_text.append(item)
                    yield item
                elif isinstance(item, dict) and item.get("type") == "tool_call_request":
                    tool_requests = item["calls"]
        
        # Pipe to TTS
        # If the LLM is calling a tool, it usually outputs NO text, or very brief text.
        try:
            async for audio_chunk in self.tts.stream_audio(stream_processor()):
                if self.interrupt_event.is_set(): return False
                await self.transport.send_audio(audio_chunk)
        except Exception as e:
            logger.error(f"Gen Error: {e}")

        # Handle Tool Execution
        if tool_requests:
            # 1. Append the Assistant's "Thought" (Tool Call) to history
            # We must convert our buffer back to the OpenAI object format
            tool_calls_msg = {
                "role": "assistant",
                "content": None,
                "tool_calls": []
            }
            
            for req in tool_requests:
                tool_calls_msg["tool_calls"].append({
                    "id": req["id"],
                    "type": "function",
                    "function": {
                        "name": req["function"]["name"],
                        "arguments": req["function"]["arguments"]
                    }
                })
            
            self.conversation_history.append(tool_calls_msg)

            # 2. Execute Tools
            for req in tool_requests:
                logger.info(f"🛠️ EXECUTING TOOL: {req['function']['name']}")
                
                # Mock objects for the execute call
                # In production, clean this up to match class structure
                class MockToolCall:
                    class Func:
                        def __init__(self, n, a): self.name=n; self.arguments=a
                    def __init__(self, f): self.function=f

                mock_obj = MockToolCall(MockToolCall.Func(req['function']['name'], req['function']['arguments']))
                
                tool_result_str = await self.tool_executor.execute(mock_obj)
                
                logger.info(f"✅ TOOL RESULT: {tool_result_str}")

                # 3. Append Result to History
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": req["id"],
                    "content": tool_result_str
                })

            # Return True to signal the loop to run the LLM again (to read the result)
            return True
        
        # If no tools, we just spoke text. Save it and exit.
        if full_response_text:
            self.conversation_history.append(
                {"role": "assistant", "content": "".join(full_response_text)}
            )
            return False # Turn Complete

        return False

    async def generate_and_speak(self, user_text: str):
        self.is_ai_speaking = True
        self.interrupt_event.clear()
        
        start_time = time.time() # Latency Tracking


       # --- RAG ENRICHMENT START ---
        # Only perform RAG if tenant_id is present
        if self.tenant_id:
            logger.info("🔍 Searching Knowledge Base...")
            rag_context = await self.rag.retrieve(user_text, self.tenant_id)
            
            if rag_context:
                logger.info("✅ RAG Context Found")
                # We inject context temporarily for this turn
                # Strategy: Create a temporary message list for the LLM
                # We don't want to pollute the permanent history with massive text chunks
                
                system_instruction = {
                    "role": "system", 
                    "content": f"Use the following context to answer the user question if relevant:\n{rag_context}"
                }
                
                # Prepend RAG context instruction immediately after the main system prompt
                # Copy history to avoid modifying the permanent state reference
                current_messages = [self.conversation_history[0]] + [system_instruction] + self.conversation_history[1:]
            else:
                current_messages = self.conversation_history
        else:
            current_messages = self.conversation_history
        # --- RAG ENRICHMENT END ---


        # 1. LLM Stream
        llm_stream = self.llm.get_response_stream_from_messages(user_text, current_messages)
        
        # 2. Wrapper to capture full text for history while streaming
        full_response_text = []

        async def text_iterator():
            full_response = []
            async for item in llm_stream:
                if item["type"] == "content":
                    token = item["text"]
                    full_response.append(token)
                    yield token
                elif item["type"] == "usage":
                    # Capture Costs
                    self.metrics["input_tokens"] += item["input_tokens"]
                    self.metrics["output_tokens"] += item["output_tokens"]

                   # Log Transcript (Async)
            if full_response:
                text = "".join(full_response)
                self.metrics["tts_characters"] += len(text) # Estimate TTS cost
                # Emit transcript line for dashboard
                asyncio.create_task(self.telemetry.emit_transcript(self.call_id, "assistant", text))

        # 3. TTS Stream (WebSocket)
        try:
            first_byte_received = False
            
            async for audio_chunk in self.tts.stream_audio(text_iterator()):
                if self.interrupt_event.is_set():
                    break
                
                # Latency Logging: Time from STT_Final to First Audio Byte sent
                if not first_byte_received:
                    latency_ms = (time.time() - start_time) * 1000
                    logger.info(f"⚡ Latency (STT->TTS): {latency_ms:.0f}ms")
                    first_byte_received = True

                # Send directly (Audio is already 8kHz PCM)
                await self.transport.send_audio(audio_chunk)

            # Save assistant response to history
            if full_response_text:
                self.conversation_history.append(
                    {"role": "assistant", "content": "".join(full_response_text)}
                )
                
        except Exception as e:
            logger.error(f"Generation Error: {e}")
        finally:
            self.is_ai_speaking = False