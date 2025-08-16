"""
Session manager for SQLAlchemy ORM (for SQLite database)
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

DATABASE_URL = get_settings().DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False, future=True, pool_pre_ping=True)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def get_session() -> AsyncSession:
    """
    Session generator for dependency injection in FastAPI.
    Yields:
        AsyncSession: async SQLAlchemy DB session
    """
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
