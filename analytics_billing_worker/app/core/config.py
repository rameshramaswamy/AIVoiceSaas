from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Analytics & Billing Worker"
    ENV: str = "development"
    
    # Messaging (Shared with Voice Engine)
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_STREAM_KEY: str = "call_events"
    
    # Analytics DB
    CLICKHOUSE_HOST: str = "clickhouse"
    CLICKHOUSE_PORT: int = 8123
    
    # Operational DB (Shared with SaaS Backend)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_SERVER: str = "db"
    POSTGRES_DB: str = "saas_voice_db"
    
    @property
    def DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    # Pricing Configuration (Base Costs)
    PRICE_STT_PER_MIN: float = 0.043 # Deepgram Nova-2
    PRICE_LLM_INPUT_1K: float = 0.005 # GPT-4o
    PRICE_LLM_OUTPUT_1K: float = 0.015
    PRICE_TTS_1K_CHARS: float = 0.18 # ElevenLabs Turbo
    PRICE_TWILIO_PER_MIN: float = 0.014
    
    PROFIT_MARGIN_PERCENT: float = 0.20 # 20% Markup

    class Config:
        env_file = ".env"

settings = Settings()