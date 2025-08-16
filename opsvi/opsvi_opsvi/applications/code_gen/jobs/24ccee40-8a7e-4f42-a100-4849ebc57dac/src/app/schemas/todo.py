"""
Pydantic schemas for Todo models (request/response validation & serialization)
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class TodoBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=256, example="Buy groceries")
    is_completed: bool = Field(default=False, example=False)


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    description: Optional[str] = Field(
        None, min_length=1, max_length=256, example="Do laundry"
    )
    is_completed: Optional[bool] = Field(None, example=True)

    @validator("description")
    def validate_description(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Description must not be empty")
        return v


class TodoInDB(TodoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TodoResponse(TodoInDB):
    pass
