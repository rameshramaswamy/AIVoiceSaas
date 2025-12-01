import logging
from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.endpoints import voice

# Configure Logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.PROJECT_NAME)

# Include Routers
app.include_router(voice.router, prefix="/api/v1/voice", tags=["voice"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "voice_stream_engine"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)