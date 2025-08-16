"""
Pydantic models for request/response validation.
"""
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr, constr


# --- User ---
class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    password: constr(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_admin: bool
    created_at: datetime

    class Config:
        orm_mode = True


# --- Project ---
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]


class ProjectRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


# --- File ---
class FileRead(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime
    file_path: str

    class Config:
        orm_mode = True


# --- Report ---
class ReportCreate(BaseModel):
    project_id: int
    source_type: str  # 'upload' or 'github'
    file_id: Optional[int]


class ReportRead(BaseModel):
    id: int
    project_id: int
    file_id: Optional[int]
    source_type: str
    created_at: datetime
    status: str
    summary: Optional[str]
    issues: Dict
    suggestions: Dict
    score: Optional[int]
    detailed_report_path: Optional[str]

    class Config:
        orm_mode = True


# --- Token, Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_admin: Optional[bool] = None


# --- Generic Response ---
class Msg(BaseModel):
    msg: str


# --- Github Repo ---
class GitHubRepo(BaseModel):
    name: str
    full_name: str
    owner: str
    description: Optional[str]
    url: str


class GitHubAnalyzeRequest(BaseModel):
    project_id: int
    repo_full_name: str
    branch: Optional[str]
