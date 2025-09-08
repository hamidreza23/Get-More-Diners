"""
Database configuration and async SQLAlchemy setup for Supabase PostgreSQL.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
try:
    from sqlalchemy.ext.asyncio import async_sessionmaker
except ImportError:
    # Fallback for older SQLAlchemy versions
    from sqlalchemy.orm import sessionmaker
    async_sessionmaker = sessionmaker
try:
    from sqlalchemy.orm import DeclarativeBase
except ImportError:
    # Fallback for older SQLAlchemy versions
    from sqlalchemy.ext.declarative import declarative_base
    DeclarativeBase = declarative_base()
from sqlalchemy import MetaData
import logging

from .config import get_settings

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create async engine with Transaction pooler compatibility
connect_args = {}
logger.info(f"Database URL for connection: {settings.database_url}")
if "pooler.supabase.com" in settings.database_url or ":6543" in settings.database_url:
    # Disable statement cache for Transaction pooler compatibility
    connect_args["statement_cache_size"] = 0
    logger.info("Using Transaction pooler - disabled statement cache")
else:
    logger.info("Not using Transaction pooler - keeping default statement cache")

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL queries in debug mode
    pool_pre_ping=True,   # Validate connections before use
    pool_recycle=3600,    # Recycle connections every hour
    pool_size=20,         # Connection pool size
    max_overflow=10,      # Additional connections beyond pool_size
    connect_args=connect_args,  # Pass asyncpg-specific arguments
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    Note: In production, use Alembic migrations instead.
    """
    try:
        async with engine.begin() as conn:
            # Import all models here to ensure they are registered
            from . import models  # noqa
            
            # Create all tables (only for development)
            if settings.environment == "development":
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables created")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")


# Database health check
async def check_db_health() -> bool:
    """
    Check database connectivity.
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
