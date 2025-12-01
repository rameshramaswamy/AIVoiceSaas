FROM python:3.11-slim

WORKDIR /app

# Install dependencies
# We need build tools for crypto libraries
RUN apt-get update && apt-get install -y build-essential libssl-dev libffi-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLP models for Presidio (PII)
RUN python -m spacy download en_core_web_lg

COPY . .

# Default to running the PII Redactor test wrapper
CMD ["python", "main.py"]