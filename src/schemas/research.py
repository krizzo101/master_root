from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class Citation(BaseModel):
    chunk_id: str = Field(..., description="Qdrant chunk UUID")
    source_url: HttpUrl
    title: str | None
    snippet: str


class ResearchPackage(BaseModel):
    query: str
    answer: str  # markdown allowed
    citations: list[Citation]
    generation_ts: datetime = Field(default_factory=datetime.utcnow)
    audit_id: str
    model_signature: str
    trace: str | None = None
