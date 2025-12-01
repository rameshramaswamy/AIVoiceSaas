import uuid
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, func,Index 
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)

    # AI Configuration
    system_prompt = Column(Text, nullable=False)
    voice_provider = Column(String, default="elevenlabs")
    voice_id = Column(String, nullable=False) # e.g., 'JBFqnCBsd6RMkjVDRZzb'
    
    # Telephony Mapping
    phone_number = Column(String, unique=True, index=True, nullable=True)
    
    # Tenant Isolation
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    tenant = relationship("Tenant", back_populates="agents")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # OPTIMIZATION: Add Composite Index
    # We frequently query by phone_number to find the config.
    # We also frequently query by tenant_id to list agents in the dashboard.
    __table_args__ = (
        Index('ix_agent_phone_lookup', 'phone_number', 'tenant_id'),
    )