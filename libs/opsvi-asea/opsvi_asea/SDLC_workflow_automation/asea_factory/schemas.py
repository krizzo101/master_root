from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class Requirement(BaseModel):
    id: str
    description: str
    type: str  # functional, non-functional, constraint


class RequirementsSpec(BaseModel):
    requirements: List[Requirement]
    user_stories: List[str]
    acceptance_criteria: List[str]


class ResearchFinding(BaseModel):
    id: str
    query: str
    summary: str
    sources: List[Any]  # Allow both strings and objects with title/url
    related_requirements: List[str]


class ArchitectureSpec(BaseModel):
    id: str
    requirements: List[Any]  # Allow both strings and complex requirement objects
    architecture: Any  # Allow complex architecture objects
    decisions: List[Any]  # Allow complex decision objects
    traceability: Any  # Allow both dict and list formats


class DesignReviewSummary(BaseModel):
    id: str
    architecture_id: str
    summary: str
    approval: Any  # Allow string, boolean, or other formats
    reviewer_comments: Any  # Allow string, list, or other formats


class CodeArtifact(BaseModel):
    id: str
    type: str  # frontend, backend, database, integration
    requirements: List[Any]  # Allow both strings and complex requirement objects
    architecture_id: str
    code: str
    traceability: Any  # Allow both dict and list formats


class CriticReview(BaseModel):
    id: Optional[str] = "critic-review-001"  # Provide default
    artifact_id: Optional[str] = None
    review: Optional[str] = None
    issues: Optional[List[Any]] = []  # Allow complex issue objects
    improvement_suggestions: Optional[
        List[Any]
    ] = []  # Allow complex suggestion objects
    iteration: Optional[int] = 1
    reviews: Optional[List[Any]] = []  # Handle case where model returns reviews array


class TestSuite(BaseModel):
    id: Optional[str] = "test-suite-001"  # Provide default
    artifact_id: Optional[str] = None
    requirements: Optional[List[str]] = []
    tests: Optional[List[Any]] = []
    results: Optional[Any] = {}  # Allow both dict and list
    # Handle case where model returns nested structure
    test_results: Optional[List[Any]] = []
    coverage: Optional[Any] = None


class DocumentationArtifact(BaseModel):
    id: Optional[str] = "documentation-001"  # Provide default
    artifact_id: Optional[str] = None
    content: Optional[str] = ""
    doc_type: Optional[str] = "general"
    version: Optional[str] = "1.0"
    # Handle case where model returns nested structure
    documents: Optional[List[Any]] = []
    documentation: Optional[Any] = ""  # Allow string or list


class IntegrationResult(BaseModel):
    id: str
    artifacts: Optional[List[str]] = []
    integration_status: Optional[str] = "pending"
    issues: Optional[List[Any]] = []  # Allow complex issue objects
    recommendations: Optional[List[Any]] = []  # Allow complex recommendation objects


class TraceabilityMatrix(BaseModel):
    requirements: List[str]
    architecture: List[str]
    code: List[str]
    tests: List[str]
    docs: List[str]
    mapping: Dict[
        str, Dict[str, List[str]]
    ]  # Fixed: mapping values are dicts, not lists
