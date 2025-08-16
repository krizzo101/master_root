"""
Pydantic models for request/response validation.
"""
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
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None
    description: str | None


class ProjectRead(BaseModel):
    id: int
    name: str
    description: str | None
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
    file_id: int | None


class ReportRead(BaseModel):
    id: int
    project_id: int
    file_id: int | None
    source_type: str
    created_at: datetime
    status: str
    summary: str | None
    issues: dict
    suggestions: dict
    score: int | None
    detailed_report_path: str | None

    class Config:
        orm_mode = True


# --- Token, Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: int | None = None
    username: str | None = None
    email: EmailStr | None = None
    is_admin: bool | None = None


# --- Generic Response ---
class Msg(BaseModel):
    msg: str


# --- Github Repo ---
class GitHubRepo(BaseModel):
    name: str
    full_name: str
    owner: str
    description: str | None
    url: str


class GitHubAnalyzeRequest(BaseModel):
    project_id: int
    repo_full_name: str
    branch: str | None
