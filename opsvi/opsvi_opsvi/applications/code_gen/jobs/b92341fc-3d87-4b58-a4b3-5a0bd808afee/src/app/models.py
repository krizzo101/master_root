from typing import Optional
from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    title: str = Field(
        ..., title="Task Title", max_length=200, description="Short title for the task"
    )
    description: Optional[str] = Field(
        None,
        title="Task Description",
        max_length=1000,
        description="Detailed description of the task",
    )
    completed: bool = Field(
        False, title="Completed", description="Status of task completion"
    )


class TaskCreate(TaskBase):
    title: str = Field(..., min_length=1, max_length=200)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, title="Task Title", max_length=200)
    description: Optional[str] = Field(None, title="Task Description", max_length=1000)
    completed: Optional[bool] = Field(None, title="Completed")


class Task(TaskBase):
    id: int = Field(
        ..., title="Task ID", description="Unique numeric identifier for the task"
    )

    class Config:
        orm_mode = True


class ErrorResponse(BaseModel):
    error: str = Field(
        ...,
        title="Error Message",
        description="Error message explaining what went wrong.",
    )
