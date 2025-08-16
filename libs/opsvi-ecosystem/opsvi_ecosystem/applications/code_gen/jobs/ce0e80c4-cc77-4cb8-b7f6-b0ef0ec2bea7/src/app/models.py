from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
