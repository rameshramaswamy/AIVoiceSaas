from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Outbound Dialer Worker"
    ENV: str = "development"
    
    # Infrastructure
    REDIS_URL: str = "redis://redis:6379/0"
    DATABASE_URI: str = "postgresql+asyncpg://postgres:password@db/saas_voice_db"
    
    # Twilio
    TWILIO_ACCOUNT_SID: str = "AC..."
    TWILIO_AUTH_TOKEN: str = "..."
    TWILIO_FROM_NUMBER: str = "+1234567890" # Default, or fetch from DB per tenant
    
    # Voice Engine Webhook (Where Twilio connects when call picks up)
    VOICE_ENGINE_URL: str = "https://your-ngrok-url.app/api/v1/voice/incoming"

    class Config:
        env_file = ".env"

settings = Settings()