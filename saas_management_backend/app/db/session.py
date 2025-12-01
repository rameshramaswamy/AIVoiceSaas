from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Enterprise: Connection Pooling Configuration
# pool_size: The number of connections to keep open inside the connection pool.
# max_overflow: The number of connections to allow in connection pool "overflow".
# pool_recycle: Recycle connections after this many seconds to prevent timeouts.
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=False, # Disable SQL echoing in production for performance/logs
    pool_size=20,
    max_overflow=10,
    pool_recycle=1800, # 30 minutes
    pool_pre_ping=True, # Check connection health before handling request
    connect_args={
        "server_settings": {
            "application_name": f"{settings.PROJECT_NAME}_api", # Tag queries for DB monitoring
            "statement_timeout": "10000" # 10s timeout to prevent locking tables
        }
    }
)

AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False # Performance optimization
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()