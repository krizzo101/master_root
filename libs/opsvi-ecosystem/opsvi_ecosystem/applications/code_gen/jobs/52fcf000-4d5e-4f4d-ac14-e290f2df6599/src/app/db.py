"""
Database setup and session management using SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.DB_URL, echo=settings.DB_ECHO, future=True)
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)
Base = declarative_base()


def get_db():
    """
    FastAPI dependency to provide a session per request.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
