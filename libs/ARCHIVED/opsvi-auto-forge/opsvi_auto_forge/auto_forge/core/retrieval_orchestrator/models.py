from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Snippet(BaseModel):
    id: str
    text: str
    score: float
    citation: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class GraphPath(BaseModel):
    nodes: list[str]
    edges: list[str]
    score: float


class RetrievalConfig(BaseModel):
    top_k: int = 12
    bm25_k: int = 8
    namespaces: list[str] = Field(default_factory=lambda: ["project"])
    communities_top_k: int = 0
    paths_top_k: int = 0
    freshness_days: int = 90
    cite_required: bool = True
    max_ctx_chars: int = 120_000


class ContextPack(BaseModel):
    context_pack_id: str
    query: str
    vector_snippets: List[Snippet] = []
    bm25_snippets: List[Snippet] = []
    graph_paths: List[GraphPath] = []
    community_summaries: List[Snippet] = []
    web_findings: List[Snippet] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    citations_required: bool = True
    max_ctx_chars: int = 120_000
