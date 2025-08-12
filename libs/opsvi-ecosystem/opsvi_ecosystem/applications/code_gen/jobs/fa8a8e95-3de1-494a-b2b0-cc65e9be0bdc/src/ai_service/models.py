from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from uuid import UUID


class TeamMember(BaseModel):
    id: str
    name: str
    skill_level: int = 5  # 1-10
    availability: float = 1.0  # 0-1 (fraction of working time)
    role: str


class Task(BaseModel):
    id: str
    title: str
    description: str
    importance: int = 5  # 1-10
    deadline: Optional[str] = None  # ISO datetime string
    estimated_duration: Optional[float] = None  # Hours
    assigned_to: Optional[str] = None  # TeamMember.id
    status: str = "pending"
    previous_duration: Optional[float] = None  # historical actual
    dependencies: List[str] = Field(default_factory=list)


class TaskInput(BaseModel):
    tasks: List[Task]
    members: List[TeamMember]


class AIResponse(BaseModel):
    result: Dict
