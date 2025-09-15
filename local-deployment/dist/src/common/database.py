"""
Database Configuration and Management

SQLAlchemy setup and database management for True-Asset-ALLUSE.
Implements the core database schema as specified in the implementation requirements.
"""

import asyncio
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import structlog

from src.common.config import get_settings
from src.common.exceptions import DatabaseError

# Import all models to ensure they are registered with SQLAlchemy
from src.common.models import *  # noqa: F401, F403

logger = structlog.get_logger(__name__)

# Database settings
settings = get_settings()

# SQLAlchemy Base
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

# Global variables for database connections
async_engine: Optional[AsyncEngine] = None
async_session_factory: Optional[async_sessionmaker] = None
sync_engine = None
sync_session_factory = None


def get_database_url(async_driver: bool = True) -> str:
    """Get database URL with appropriate driver."""
    url = str(settings.database_url)
    
    if async_driver:
        # Convert to async driver
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    else:
        # Ensure sync driver
        if url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    
    return url


async def init_db() -> None:
    """Initialize database connections and create tables."""
    global async_engine, async_session_factory, sync_engine, sync_session_factory
    
    try:
        # Create async engine
        async_engine = create_async_engine(
            get_database_url(async_driver=True),
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_pre_ping=True,
            echo=settings.debug,
        )
        
        # Create async session factory
        async_session_factory = async_sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Create sync engine for migrations and synchronous operations
        sync_engine = create_engine(
            get_database_url(async_driver=False),
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_pre_ping=True,
            echo=settings.debug,
        )
        
        # Create sync session factory
        sync_session_factory = sessionmaker(
            bind=sync_engine,
            expire_on_commit=False
        )
        
        logger.info(
            "Database initialized successfully",
            async_url=get_database_url(async_driver=True),
            sync_url=get_database_url(async_driver=False)
        )
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e), exc_info=True)
        raise DatabaseError(
            message=f"Failed to initialize database: {str(e)}",
            operation="init_db"
        )


async def close_db() -> None:
    """Close database connections."""
    global async_engine, sync_engine
    
    try:
        if async_engine:
            await async_engine.dispose()
            logger.info("Async database engine disposed")
        
        if sync_engine:
            sync_engine.dispose()
            logger.info("Sync database engine disposed")
            
    except Exception as e:
        logger.error("Error closing database connections", error=str(e))


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    if not async_session_factory:
        raise DatabaseError(
            message="Database not initialized. Call init_db() first.",
            operation="get_async_session"
        )
    
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()


def get_sync_session():
    """Get synchronous database session."""
    if not sync_session_factory:
        raise DatabaseError(
            message="Database not initialized. Call init_db() first.",
            operation="get_sync_session"
        )
    
    return sync_session_factory()


@asynccontextmanager
async def get_db_transaction():
    """Get database session with automatic transaction management."""
    async with get_async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Transaction rolled back", error=str(e))
            raise


async def check_database_health() -> bool:
    """Check database connectivity and health."""
    try:
        if not async_engine:
            return False
            
        async with async_engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            return result.scalar() == 1
            
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False


def create_tables() -> None:
    """Create all database tables (for migrations)."""
    if not sync_engine:
        raise DatabaseError(
            message="Sync engine not initialized",
            operation="create_tables"
        )
    
    try:
        Base.metadata.create_all(bind=sync_engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error("Failed to create tables", error=str(e))
        raise DatabaseError(
            message=f"Failed to create tables: {str(e)}",
            operation="create_tables"
        )


def drop_tables() -> None:
    """Drop all database tables (for testing)."""
    if not sync_engine:
        raise DatabaseError(
            message="Sync engine not initialized",
            operation="drop_tables"
        )
    
    try:
        Base.metadata.drop_all(bind=sync_engine)
        logger.info("Database tables dropped successfully")
        
    except Exception as e:
        logger.error("Failed to drop tables", error=str(e))
        raise DatabaseError(
            message=f"Failed to drop tables: {str(e)}",
            operation="drop_tables"
        )


# Dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async for session in get_async_session():
        yield session

