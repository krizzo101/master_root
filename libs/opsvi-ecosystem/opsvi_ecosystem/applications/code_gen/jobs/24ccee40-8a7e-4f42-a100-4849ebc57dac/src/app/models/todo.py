"""
Todo SQLAlchemy database model definition.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.db.base import Base


class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    description = Column(String(256), nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow
    )
