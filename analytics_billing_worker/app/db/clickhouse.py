import clickhouse_connect
import logging
from app.core.config import settings

logger = logging.getLogger("clickhouse")

def get_client():
    return clickhouse_connect.get_client(
        host=settings.CLICKHOUSE_HOST,
        port=settings.CLICKHOUSE_PORT,
        username='default', 
        password=''
    )

def init_clickhouse():
    """
    Idempotent initialization of Analytics Tables.
    """
    try:
        client = get_client()
        
        # 1. Call Metrics (One row per call)
        # Replacing standard SQL with ClickHouse specific DDL
        client.command("""
        CREATE TABLE IF NOT EXISTS call_metrics (
            call_id String,
            tenant_id String,
            agent_id String,
            start_time DateTime,
            end_time DateTime,
            duration_seconds Float32,
            status String,
            cost Float32,
            end_reason String,
            sentiment_score Float32
        ) ENGINE = MergeTree()
        ORDER BY (tenant_id, start_time)
        """)
        
        # 2. Transcripts (Many rows per call)
        client.command("""
        CREATE TABLE IF NOT EXISTS transcript_logs (
            call_id String,
            timestamp DateTime,
            role String, -- user, assistant, tool
            content String,
            metadata String -- JSON string for token counts etc.
        ) ENGINE = MergeTree()
        ORDER BY (call_id, timestamp)
        """)
        
        logger.info("✅ ClickHouse Tables Initialized")
    except Exception as e:
        logger.error(f"❌ ClickHouse Init Failed: {e}")
        raise