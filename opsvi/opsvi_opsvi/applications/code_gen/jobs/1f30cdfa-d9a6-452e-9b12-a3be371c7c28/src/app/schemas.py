from pydantic import BaseModel, Field
from typing import Optional


class TodoBase(BaseModel):
    title: str = Field(
        ..., min_length=1, max_length=100, description="Title of the todo item"
    )
    description: str = Field(
        ..., min_length=1, max_length=1000, description="Description of the todo item"
    )


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Title of the todo item"
    )
    description: Optional[str] = Field(
        None, min_length=1, max_length=1000, description="Description of the todo item"
    )


class Todo(TodoBase):
    id: int

    class Config:
        orm_mode = True


class HealthCheckResponse(BaseModel):
    status: str
