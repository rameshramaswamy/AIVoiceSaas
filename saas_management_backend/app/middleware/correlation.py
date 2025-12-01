import uuid
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check if incoming request already has an ID (from Load Balancer)
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Bind Request ID to the logger context for this thread/request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        
        response = await call_next(request)
        
        # Return ID to client for debugging
        response.headers["X-Request-ID"] = request_id
        return response