# Multi-stage build for smaller image size
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final Stage
FROM python:3.11-slim

WORKDIR /app

# Install dependencies from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy Code
COPY . .

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Enterprise Entrypoint: Gunicorn
# -w 4: 4 Workers (Adjust based on CPU cores)
# -k uvicorn.workers.UvicornWorker: Async worker class
CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--access-logfile", "-", "--error-logfile", "-"]