"""
Database configuration and async SQLAlchemy setup for Supabase PostgreSQL.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
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
from sqlalchemy.engine.url import make_url, URL
import ssl
import certifi

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create async engine with Transaction pooler compatibility
connect_args = {}
logger.info(f"Database URL for connection: {settings.database_url}")

# Derive an effective URL: optionally rewrite Supabase pooler URL to direct DB host (5432)
effective_database_url = settings.database_url
parsed_host = None
parsed_port: int | None = None
if settings.use_direct_db:
    try:
        url = make_url(settings.database_url)
        parsed_host = url.host or ""
        parsed_port = url.port or None
        if ("pooler.supabase.com" in parsed_host) or (parsed_port == 6543):
            # Try to extract ref id from username 'postgres.<ref>'
            ref = None
            if url.username and "." in url.username:
                parts = url.username.split(".")
                if len(parts) >= 2 and parts[0] == "postgres":
                    ref = parts[1]
            if ref:
                rewritten = URL.create(
                    drivername=url.drivername,
                    username="postgres",
                    password=url.password,
                    host=f"db.{ref}.supabase.co",
                    port=5432,
                    database=url.database,
                    query=url.query,
                )
                effective_database_url = str(rewritten)
                logger.info("Rewriting pooler URL to direct DB for MVP stability: %s", effective_database_url)
            else:
                logger.info("Pooler URL detected but could not extract ref; using pooler as-is")
    except Exception as e:
        logger.warning("Failed to parse/possibly rewrite DATABASE_URL: %s", e)
else:
    try:
        url = make_url(settings.database_url)
        parsed_host = url.host or ""
        parsed_port = url.port or None
    except Exception:
        parsed_host = None
        parsed_port = None

using_pooler = False
drivername = None
try:
    url_obj_all = make_url(effective_database_url)
    drivername = url_obj_all.drivername
    host_all = url_obj_all.host or ""
    port_all = url_obj_all.port or None
    using_pooler = ("pooler.supabase.com" in host_all) or (port_all == 6543)
except Exception:
    using_pooler = (parsed_host and "pooler.supabase.com" in parsed_host) or (parsed_port == 6543)

# If using Supabase, ensure TLS is used; adapt per driver
if "supabase.co" in effective_database_url:
    if using_pooler:
        # For PgBouncer pooler, prefer psycopg driver and libpq sslmode
        try:
            url_obj = make_url(effective_database_url)
            dname = url_obj.drivername or ""
            if "+asyncpg" in dname:
                url_obj = url_obj.set(drivername=dname.replace("+asyncpg", "+psycopg"))
                effective_database_url = str(url_obj)
                logger.info("Switching driver to psycopg for PgBouncer compatibility: %s", effective_database_url)
        except Exception as e:
            logger.warning(f"Could not parse URL for driver switch: {e}")

        # TLS for psycopg/libpq
        if settings.db_ssl_insecure:
            connect_args["sslmode"] = "require"  # TLS without CA verification (demo-safe)
            logger.warning("Using INSECURE TLS (no cert verification) for Supabase pooler host. Set DB_SSL_INSECURE=false to enforce verification.")
        else:
            connect_args["sslmode"] = "verify-full"
            connect_args["sslrootcert"] = certifi.where()
            logger.info("Using verified TLS with certifi for Supabase pooler host")
    else:
        # Direct DB host: verified TLS via asyncpg SSL context
        verify_ctx = ssl.create_default_context(cafile=certifi.where())
        connect_args["ssl"] = verify_ctx
        logger.info("Using verified TLS with certifi for Supabase direct host")

# If still using pooler, disable prepared statement caches for PgBouncer transaction/statement poolers
if using_pooler:
    # If psycopg is used, disable server-side prepared statements entirely
    try:
        if "+psycopg" in (drivername or make_url(effective_database_url).drivername or ""):
            connect_args["prepare_threshold"] = 0
            logger.info("Using PgBouncer pooler with psycopg: prepare_threshold=0")
        else:
            # asyncpg path: best-effort cache disables
            connect_args["prepared_statement_cache_size"] = 0
            connect_args["statement_cache_size"] = 0
            logger.info("Using PgBouncer pooler with asyncpg: disabled asyncpg statement caches")
    except Exception:
        # Fallback to asyncpg disables
        connect_args["prepared_statement_cache_size"] = 0
        connect_args["statement_cache_size"] = 0
else:
    logger.info("Not using PgBouncer pooler - keeping default statement cache")

engine = create_async_engine(
    effective_database_url,
    echo=settings.debug,          # Log SQL queries in debug mode
    pool_pre_ping=True,           # Validate connections before use
    pool_recycle=3600,            # Recycle connections every hour (harmless with NullPool)
    poolclass=NullPool,           # Rely on PgBouncer; avoid app-level pooling to prevent prepared stmt reuse
    connect_args=connect_args,    # Pass asyncpg-specific arguments
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
