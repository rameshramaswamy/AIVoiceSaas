import sys
import logging
from arq import run_worker
from app.worker import WorkerSettings

# Setup Logging
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    # ARQ Worker Runner
    run_worker(WorkerSettings)