from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Voice Stream Engine"
    ENV: str = "development"
    
    # Infrastructure
    REDIS_URL: str = "redis://localhost:6379/0"
    PORT: int = 8000
    
    # Security
    API_SECRET_KEY: str = "changeme"
    
    # AI Providers
    OPENAI_API_KEY: Optional[str] = None
    DEEPGRAM_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    
    # Telephony
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None

    # RAG Configuration
    QDRANT_HOST: str = "qdrant" # Docker service name
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "enterprise_knowledge_base"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()