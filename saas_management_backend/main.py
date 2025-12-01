from fastapi import FastAPI
from app.core.config import settings
from app.api.api import api_router
from app.middleware.correlation import CorrelationIdMiddleware
from app.core.logging_config import setup_json_logging

setup_json_logging()
app = FastAPI(title=settings.PROJECT_NAME)
app.add_middleware(CorrelationIdMiddleware)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "healthy", "component": "management_api"}