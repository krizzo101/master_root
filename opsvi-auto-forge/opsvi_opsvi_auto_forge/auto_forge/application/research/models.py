"""Data models for the research stack."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SourceType(str, Enum):
    """Types of research sources."""

    WEB = "web"
    SCRAPE = "scrape"
    PAPER = "paper"
    DOCS = "docs"
    THINK = "think"


class RankingScore(float):
    """Score for ranking results (0.0 to 1.0)."""

    def __new__(cls, value: float) -> "RankingScore":
        if not 0.0 <= value <= 1.0:
            raise ValueError("RankingScore must be between 0.0 and 1.0")
        return super().__new__(cls, value)


@dataclass(frozen=True)
class SearchResult:
    """Result from a single search source."""

    source: SourceType
    url: str
    title: str
    snippet: str
    content: str | None = None
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class RankedResult(SearchResult):
    """Search result with relevance scoring applied."""

    relevance: RankingScore = field(default=RankingScore(0.0))
    ranking_factors: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class ResearchSummary:
    """Complete research summary with synthesis."""

    query: str
    top_results: list[RankedResult] = field(default_factory=list)
    synthesis: str = ""
    total_sources: int = 0
    successful_sources: int = 0
    failed_sources: int = 0
    execution_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class QueryTransform:
    """Query transformation result."""

    original: str
    transformed: str
    confidence: float = 0.0
    reasoning: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ClientConfig:
    """Configuration for an MCP client."""

    name: str
    enabled: bool = True
    timeout: float = 30.0
    max_results: int = 10
    api_key: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResearchConfig:
    """Complete research configuration."""

    clients: dict[str, ClientConfig] = field(default_factory=dict)
    default_timeout: float = 30.0
    max_parallel_requests: int = 5
    enable_synthesis: bool = True
    enable_persistence: bool = True
    synthesis_model: str = "gpt-4"
    metadata: dict[str, Any] = field(default_factory=dict)
