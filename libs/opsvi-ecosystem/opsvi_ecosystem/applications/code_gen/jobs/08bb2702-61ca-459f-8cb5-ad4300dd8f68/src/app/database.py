"""
Database utility for the Task Management API.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
import sqlalchemy
import logging
from typing import AsyncGenerator

from app.models import Base

logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite+aiosqlite:///./tasks.db"

engine = create_async_engine(
    DATABASE_URL, echo=False, future=True, connect_args={"check_same_thread": False}
)

async_session_factory = async_sessionmaker(
    bind=engine, expire_on_commit=False, autoflush=False, class_=AsyncSession
)


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session = async_session_factory()
    try:
        yield session
    finally:
        await session.close()


async def init_db() -> None:
    """
    Initializes the database by creating tables if they don't exist.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully.")
    except Exception as exc:
        logger.error(f"Error creating database tables: {exc}")
        raise
