from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TodoBase(BaseModel):
    title: str = Field(
        ..., min_length=1, max_length=256, description="Title of the todo item."
    )
    description: Optional[str] = Field(
        None, max_length=1024, description="Optional description."
    )
    completed: bool = Field(False, description="Completion status.")


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=256)
    description: Optional[str] = Field(None, max_length=1024)
    completed: Optional[bool]


class TodoRead(TodoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
