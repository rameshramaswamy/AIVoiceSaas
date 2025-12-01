import logging

logger = logging.getLogger("tools")

class CalendarTool:
    @staticmethod
    def check_calendar_availability(date: str, time: str) -> str:
        logger.info(f"🔧 TOOL: Checking calendar for {date} at {time}")
        # Mock Logic: Tuesday 10:00 is always taken.
        if "10:00" in time:
            return "false" # Slot is taken
        return "true" # Slot is free

    @staticmethod
    def book_appointment(date: str, time: str, name: str, phone: str = None) -> str:
        logger.info(f"🔧 TOOL: Booking for {name} on {date} at {time}")
        # Mock Logic: Success
        return f"Success. Appointment booked for {name} on {date} at {time}."