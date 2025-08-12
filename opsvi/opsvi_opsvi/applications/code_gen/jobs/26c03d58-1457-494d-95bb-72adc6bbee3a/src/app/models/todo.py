"""
Pydantic models for todo items and API messages.
"""
from datetime import datetime

from pydantic import BaseModel, Field, validator


class TodoItemBase(BaseModel):
    title: str = Field(
        ..., min_length=2, max_length=200, description="Title of the todo item."
    )
    description: str | None = Field(
        None, max_length=1000, description="Description of the todo item."
    )
    completed: bool = Field(default=False, description="Completion status.")

    @validator("title")
    def title_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be blank.")
        return v


class TodoItemCreate(TodoItemBase):
    pass


class TodoItemUpdate(BaseModel):
    title: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = Field(None, max_length=1000)
    completed: bool | None = Field(None)

    @validator("title")
    def title_must_not_be_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Title cannot be blank.")
        return v


class TodoItemModel(TodoItemBase):
    id: int = Field(..., gt=0, description="Unique ID of the todo item.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")

    class Config:
        orm_mode = True


class TodoItemResponse(BaseModel):
    data: TodoItemModel


class MessageResponse(BaseModel):
    message: str
