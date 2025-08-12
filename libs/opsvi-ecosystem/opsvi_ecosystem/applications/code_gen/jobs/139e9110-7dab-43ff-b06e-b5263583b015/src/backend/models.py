"""
models.py: ORM / SQLAlchemy DB models for User, Project, Task, Comment, TimeEntry, File, AuditLog, Dependency
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class UserRole(enum.StrEnum):
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"
    id = Column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid, index=True
    )
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    avatar_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    projects = relationship("Project", back_populates="owner")
    tasks = relationship("Task", back_populates="assignee")
    comments = relationship("Comment", back_populates="user")


class Project(Base):
    __tablename__ = "projects"
    id = Column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid, index=True
    )
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    owner_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project")


class TaskStatus(enum.StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class Task(Base):
    __tablename__ = "tasks"
    id = Column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid, index=True
    )
    project_id = Column(String, ForeignKey("projects.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    assignee_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    priority = Column(Integer, default=0)  # Lower = higher priority
    due_date = Column(DateTime, nullable=True)
    estimated_duration = Column(Float)  # hours, set by AI
    actual_duration = Column(Float)  # hours, sum of time entries

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks")
    comments = relationship("Comment", back_populates="task")
    dependencies = relationship(
        "Dependency", back_populates="task", foreign_keys="Dependency.task_id"
    )
    dependents = relationship(
        "Dependency",
        back_populates="depends_on",
        foreign_keys="Dependency.depends_on_task_id",
    )


class Dependency(Base):
    __tablename__ = "dependencies"
    id = Column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid, index=True
    )
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"))
    depends_on_task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"))
    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on = relationship(
        "Task", foreign_keys=[depends_on_task_id], back_populates="dependents"
    )
    UniqueConstraint("task_id", "depends_on_task_id", name="uq_task_dependency")


class Comment(Base):
    __tablename__ = "comments"
    id = Column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid, index=True
    )
    task_id = Column(String, ForeignKey("tasks.id"))
    user_id = Column(String, ForeignKey("users.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    mentions = Column(Text)  # comma-separated user ids
    file_id = Column(String, ForeignKey("files.id"), nullable=True)
    task = relationship("Task", back_populates="comments")
    user = relationship("User", back_populates="comments")
    file = relationship("File", back_populates="comments")


class File(Base):
    __tablename__ = "files"
    id = Column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid, index=True
    )
    filename = Column(String, nullable=False)
    url = Column(String, nullable=False)
    uploader_id = Column(String, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    comments = relationship("Comment", back_populates="file")


class TimeEntry(Base):
    __tablename__ = "time_entries"
    id = Column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid, index=True
    )
    task_id = Column(String, ForeignKey("tasks.id"))
    user_id = Column(String, ForeignKey("users.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    stopped_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)
    exported = Column(Boolean, default=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid, index=True
    )
    action = Column(String, nullable=False)
    user_id = Column(String)
    entity = Column(String)
    entity_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    meta = Column(Text)
