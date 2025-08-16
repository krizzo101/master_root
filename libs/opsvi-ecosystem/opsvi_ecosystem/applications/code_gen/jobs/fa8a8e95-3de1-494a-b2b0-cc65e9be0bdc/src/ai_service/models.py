from pydantic import BaseModel, Field


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
    deadline: str | None = None  # ISO datetime string
    estimated_duration: float | None = None  # Hours
    assigned_to: str | None = None  # TeamMember.id
    status: str = "pending"
    previous_duration: float | None = None  # historical actual
    dependencies: list[str] = Field(default_factory=list)


class TaskInput(BaseModel):
    tasks: list[Task]
    members: list[TeamMember]


class AIResponse(BaseModel):
    result: dict
