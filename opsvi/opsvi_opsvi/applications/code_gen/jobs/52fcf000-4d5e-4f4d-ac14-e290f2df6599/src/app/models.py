"""
SQLAlchemy ORM models: User, Project, Report, File, etc.
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    JSON,
)
from sqlalchemy.orm import relationship
from app.db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    github_token = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    projects = relationship("Project", back_populates="owner")


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="projects")
    reports = relationship(
        "Report", back_populates="project", cascade="all, delete-orphan"
    )


class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(250), nullable=False)
    file_path = Column(String(512), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    project_id = Column(Integer, ForeignKey("projects.id"))
    uploader_id = Column(Integer, ForeignKey("users.id"))
    is_temp = Column(Boolean, default=True)
    project = relationship("Project")
    uploader = relationship("User")


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=True)
    source_type = Column(String(16), nullable=False)  # 'upload'/'github'
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(32), default="pending")  # 'pending', 'completed', 'failed'
    summary = Column(String(256), nullable=True)
    issues = Column(JSON, default={})
    suggestions = Column(JSON, default={})
    score = Column(Integer, nullable=True)
    detailed_report_path = Column(String(512), nullable=True)
    project = relationship("Project", back_populates="reports")
    file = relationship("File")
