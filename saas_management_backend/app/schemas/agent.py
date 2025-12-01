from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class AgentCreate(BaseModel):
    name: str
    system_prompt: str
    voice_id: str
    voice_provider: str = "elevenlabs"
    phone_number: Optional[str] = None

class AgentResponse(AgentCreate):
    id: UUID
    tenant_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True