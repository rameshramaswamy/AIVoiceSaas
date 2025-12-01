# OpenAI Tool Schemas
AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_calendar_availability",
            "description": "Check if a specific time slot is available for a meeting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "The date to check in YYYY-MM-DD format."
                    },
                    "time": {
                        "type": "string",
                        "description": "The time to check in HH:MM format (24h)."
                    }
                },
                "required": ["date", "time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book a meeting for the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "time": {"type": "string"},
                    "name": {"type": "string", "description": "Name of the person booking"},
                    "phone": {"type": "string", "description": "Phone number of the person"}
                },
                "required": ["date", "time", "name"]
            }
        }
    }
]