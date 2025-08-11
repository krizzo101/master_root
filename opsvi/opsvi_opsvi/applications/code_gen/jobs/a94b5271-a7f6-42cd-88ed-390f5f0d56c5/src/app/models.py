"""
Pydantic models and SQLAlchemy ORM schema for core entities:
- User
- Document
- DocumentVersion
- UserPresence
- AuditLog
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

# Orm definitions for DB integration omitted for brevity


class User(BaseModel):
    id: str
    username: str
    email: EmailStr
    full_name: Optional[str]
    disabled: Optional[bool] = False
    created_at: datetime


class Document(BaseModel):
    id: str
    owner_id: str
    title: str
    body: str
    created_at: datetime
    updated_at: datetime
    collaborators: List[str] = []
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
    doc_id: Optional[str]
    action: str
    detail: Optional[str]
    timestamp: datetime
    ip: Optional[str]
