from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create async session factory
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create declarative base
Base = declarative_base()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database - create tables
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connection
    """
    await engine.dispose() 