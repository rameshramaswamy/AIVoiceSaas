from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Use the same Redis as the Voice Engine
limiter = Limiter(
    key_func=get_remote_address, 
    storage_uri=settings.REDIS_URL
)