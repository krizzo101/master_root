"""
Pydantic schemas for the Task Management API.
"""
from pydantic import BaseModel, Field
from typing import Optional


class TaskBase(BaseModel):
    title: str = Field(..., title="Title", max_length=255)
    description: Optional[str] = Field(None, title="Description")
    is_completed: Optional[bool] = Field(False, title="Completion Status")


class TaskCreate(TaskBase):
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Task title must be between 1 and 255 characters.",
    )


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_completed: Optional[bool] = None


class TaskInDB(TaskBase):
    id: int

    class Config:
        orm_mode = True


class TaskResponse(TaskInDB):
    pass


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]


class MessageResponse(BaseModel):
    message: str
