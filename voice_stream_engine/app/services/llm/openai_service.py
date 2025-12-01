from openai import AsyncOpenAI
from app.core.config import settings
from typing import AsyncGenerator

class OpenAIService:
    def __init__(self, system_prompt: str):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.system_prompt = system_prompt

    async def get_response_stream(self, user_text: str, conversation_history: list = None) -> AsyncGenerator[str, None]:
        """
        Generate streaming response from GPT-4o
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": user_text})

        try:
            stream = await self.client.chat.completions.create(
                model="gpt-4o", # Use gpt-3.5-turbo if 4o is too expensive/slow for dev
                messages=messages,
                stream=True,
                max_tokens=150
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f"Error generating response: {str(e)}"

    async def get_response_stream_from_messages(self, messages: list) -> AsyncGenerator[str, None]:
        """
        Directly streams response based on the provided list of messages.
        Used when RAG modifies the context dynamically.
        """
        # Ensure System Prompt is first if not present (defensive coding)
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": self.system_prompt})

        try:
            stream = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                stream=True,
                max_tokens=250 # Concise answers for voice
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f" I'm having trouble thinking right now. {str(e)}"

    async def get_response_stream_with_tools(self, messages: list) -> AsyncGenerator[Union[str, Dict], None]:
        """
        Yields strings (tokens) for TTS 
        OR 
        Yields a Dictionary (Tool Call Request) if the AI decides to use a tool.
        """
        # Ensure System Prompt
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": self.system_prompt})

        try:
            stream = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                stream=True,
                tools=AVAILABLE_TOOLS,
                tool_choice="auto"
            )

            tool_calls_buffer = []
            
            async for chunk in stream:
                delta = chunk.choices[0].delta
                
                # Case 1: Text Content (Speak it)
                if delta.content:
                    yield delta.content

                # Case 2: Tool Call (Buffer it)
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        # OpenAI sends tool calls in partial chunks
                        if len(tool_calls_buffer) <= tc.index:
                            tool_calls_buffer.append({
                                "id": tc.id,
                                "function": {"name": tc.function.name, "arguments": ""}
                            })
                        
                        if tc.function.arguments:
                            tool_calls_buffer[tc.index]["function"]["arguments"] += tc.function.arguments

            # End of Stream: Check if we have buffered tools
            if tool_calls_buffer:
                # Yield the structured tool call request
                yield {"type": "tool_call_request", "calls": tool_calls_buffer}

        except Exception as e:
            yield f"Error: {str(e)}"

    async def get_response_stream_with_usage(self, messages: list) -> AsyncGenerator[dict, None]:
        """
        Yields content chunks AND final usage stats.
        """
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": self.system_prompt})

        try:
            stream = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                stream=True,
                # CRITICAL: Request usage stats in stream
                stream_options={"include_usage": True} 
            )

            async for chunk in stream:
                # 1. Content
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {"type": "content", "text": chunk.choices[0].delta.content}
                
                # 2. Usage Stats (Usually in the last chunk where choices is empty)
                if chunk.usage:
                    yield {
                        "type": "usage", 
                        "input_tokens": chunk.usage.prompt_tokens,
                        "output_tokens": chunk.usage.completion_tokens
                    }

        except Exception as e:
            yield {"type": "error", "text": str(e)}