import json
import logging
from app.services.tools.calendar_tool import CalendarTool
import asyncio
from pydantic import BaseModel, ValidationError, create_model

logger = logging.getLogger("tools")


# 1. Define Strict Schemas for Validation
class CalendarCheckSchema(BaseModel):
    date: str
    time: str

class AppointmentBookSchema(BaseModel):
    date: str
    time: str
    name: str
    phone: str | None = None

class ToolExecutor:
    def __init__(self):
        self.functions = {
            "check_calendar_availability": (CalendarTool.check_calendar_availability, CalendarCheckSchema),
            "book_appointment": (CalendarTool.book_appointment, AppointmentBookSchema)
        }

    async def execute(self, tool_call_data: dict) -> str:
        name = tool_call_data.function.name
        raw_args = tool_call_data.function.arguments

        if name not in self.functions:
            return f"System Error: Tool {name} is defined in definitions but missing implementation."

        func, schema = self.functions[name]

        try:
            # 2. Validate JSON & Schema
            args_dict = json.loads(raw_args)
            validated_args = schema(**args_dict) # This throws ValidationError if LLM hallucinated
            
            # 3. Timeout Protection
            # Don't let a tool hang the call for >3 seconds
            result = await asyncio.wait_for(
                # Run sync function in thread pool to not block asyncio loop
                asyncio.to_thread(func, **validated_args.model_dump()), 
                timeout=3.0
            )
            return str(result)

        except json.JSONDecodeError:
            return "Error: Invalid JSON arguments provided by model."
        except ValidationError as e:
            # Return specific validation error so LLM can self-correct in next turn
            return f"Error: Missing or invalid arguments. Details: {e.errors()}"
        except asyncio.TimeoutError:
            return "Error: The tool took too long to respond."
        except Exception as e:
            logger.error(f"Tool Execution Critical Failure: {e}")
            return "Error: Internal tool failure."