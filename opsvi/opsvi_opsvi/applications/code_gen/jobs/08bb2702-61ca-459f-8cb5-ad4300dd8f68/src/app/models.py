"""
SQLAlchemy models for the Task Management API.
"""
from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
