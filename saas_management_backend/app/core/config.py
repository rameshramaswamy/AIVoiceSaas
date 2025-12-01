from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Voice SaaS API"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "generate_a_secure_random_key_here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours
    
    # Database
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "saas_voice_db"
    MANAGEMENT_API_URL: str = "http://backend:8080/api/v1"

    # Vector DB
    QDRANT_HOST: str = "qdrant" # Service name in docker-compose
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "enterprise_knowledge_base"
    
    # AI Keys (Required for Embedding generation in Backend)
    OPENAI_API_KEY: str = "sk-proj-..."
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"

settings = Settings()