"""
Pydantic models and SQLAlchemy ORM schema for core entities:
- User
- Document
- DocumentVersion
- UserPresence
- AuditLog
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr

# Orm definitions for DB integration omitted for brevity


class User(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: str | None
    disabled: bool | None = False
    created_at: datetime


class Document(BaseModel):
    id: str
    owner_id: str
    title: str
    body: str
    created_at: datetime
    updated_at: datetime
    collaborators: list[str] = []
    current_version: int = 1


class DocumentVersion(BaseModel):
    id: str
    doc_id: str
    version: int
    title: str
    body: str
    created_at: datetime
    author_id: str


class UserPresence(BaseModel):
    doc_id: str
    user_id: str
    username: str
    last_active: datetime


class AuditLog(BaseModel):
    id: str
    user_id: str
    doc_id: str | None
    action: str
    detail: str | None
    timestamp: datetime
    ip: str | None
