import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from pgvector.sqlalchemy import Vector

from app.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


settings = get_settings()

# Disable SSL for asyncpg (Docker PostgreSQL doesn't use SSL)
connect_args = {}
if "asyncpg" in settings.database_url:
    connect_args["ssl"] = False

engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
    connect_args=connect_args,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database with retry logic for Docker startup timing."""
    for attempt in range(5):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            return
        except Exception as e:
            if attempt < 4:
                wait = 2 ** attempt
                logger.warning(f"DB connection attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                await asyncio.sleep(wait)
            else:
                logger.error(f"Could not connect to database after 5 attempts: {e}")
                raise
