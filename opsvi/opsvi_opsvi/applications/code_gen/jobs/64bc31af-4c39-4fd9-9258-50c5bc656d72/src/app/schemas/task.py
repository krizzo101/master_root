from pydantic import BaseModel, Field
from typing import Optional


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, example="Buy groceries")
    description: Optional[str] = Field(
        None, max_length=500, example="Buy milk, bread, and eggs."
    )


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(
        None, min_length=1, max_length=100, example="Buy groceries"
    )
    description: Optional[str] = Field(
        None, max_length=500, example="Buy more fruits as well."
    )


class TaskResponse(TaskBase):
    id: int

    class Config:
        orm_mode = True
