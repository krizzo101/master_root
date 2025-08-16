"""
Pydantic schemas for Todo models (request/response validation & serialization)
"""
from datetime import datetime

from pydantic import BaseModel, Field, validator


class TodoBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=256, example="Buy groceries")
    is_completed: bool = Field(default=False, example=False)


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    description: str | None = Field(
        None, min_length=1, max_length=256, example="Do laundry"
    )
    is_completed: bool | None = Field(None, example=True)

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
