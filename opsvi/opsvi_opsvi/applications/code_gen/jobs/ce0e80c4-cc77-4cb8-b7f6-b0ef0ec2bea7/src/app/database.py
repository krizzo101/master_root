import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from app.models import Base

DATABASE_URL = os.getenv("TODO_DB_URL", "sqlite:///./todo.sqlite3")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = logging.getLogger(__name__)


def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created.")
    except SQLAlchemyError as ex:
        logger.error(f"Failed to create database tables: {ex}")
        raise


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Make sure to initialize the database schema
init_db()
