import os
from sqlmodel import create_engine, Session
from backend.config import settings

DB_URL = settings.DATABASE_URL
engine = create_engine(
    DB_URL, echo=False, pool_pre_ping=True, pool_size=10, max_overflow=20
)


def get_session():
    with Session(engine) as session:
        yield session
