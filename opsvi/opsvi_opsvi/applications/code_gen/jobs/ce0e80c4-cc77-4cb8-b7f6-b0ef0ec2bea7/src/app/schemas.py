from datetime import datetime

from pydantic import BaseModel, Field


class TodoBase(BaseModel):
    title: str = Field(
        ..., min_length=1, max_length=256, description="Title of the todo item."
    )
    description: str | None = Field(
        None, max_length=1024, description="Optional description."
    )
    completed: bool = Field(False, description="Completion status.")


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=256)
    description: str | None = Field(None, max_length=1024)
    completed: bool | None


class TodoRead(TodoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
