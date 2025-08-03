from typing import Dict, List, Optional

from pydantic import BaseModel


class MemoryAgentInput(BaseModel):
    prompt: str


class MemoryAgentOutput(BaseModel):
    result: str
    details: Optional[List[str]] = None


class KnowledgeAgentInput(BaseModel):
    prompt: str


class KnowledgeAgentOutput(BaseModel):
    result: str
    details: Optional[List[str]] = None


class TestingAgentInput(BaseModel):
    prompt: str


class TestingAgentOutput(BaseModel):
    result: str
    details: Optional[List[str]] = None


class ResearchAgentInput(BaseModel):
    question: str


class ResearchAgentOutput(BaseModel):
    answer: str
    sources: List[str]


class DocumentationAgentInput(BaseModel):
    prompt: str


class DocumentationAgentOutput(BaseModel):
    result: str
    details: Optional[List[str]] = None


class ConsultAgentInput(BaseModel):
    prompt: str
    session_id: Optional[str] = None
    file_paths: Optional[List[str]] = None
    analysis_type: Optional[str] = "architectural_guidance"


class ConsultAgentOutput(BaseModel):
    result: str
    details: Optional[List[str]] = None
    file_ids: Optional[List[str]] = None
    session_id: Optional[str] = None
    analysis_type: Optional[str] = "architectural_guidance"
    file_analysis: Optional[bool] = False


class ChallengeAgentInput(BaseModel):
    prompt: str


class ChallengeAgentOutput(BaseModel):
    result: str
    details: Optional[List[str]] = None


class CritiqueAgentInput(BaseModel):
    prompt: str


class CritiqueAgentOutput(BaseModel):
    result: str
    details: Optional[List[str]] = None


class CheckMeAgentInput(BaseModel):
    prompt: str


class CheckMeAgentOutput(BaseModel):
    result: str
    details: Optional[List[str]] = None


class RequirementsDoc(BaseModel):
    title: str
    requirements: List[str]
    rationale: str


class DesignDoc(BaseModel):
    title: str
    architecture: str
    diagrams: List[str]
    rationale: str


class SpecsDoc(BaseModel):
    title: str
    endpoints: List[Dict]
    data_models: List[Dict]


class TestPlanDoc(BaseModel):
    title: str
    test_cases: List[Dict]


class DocsBundle(BaseModel):
    requirements: RequirementsDoc
    design: DesignDoc
    specs: SpecsDoc
    test_plan: TestPlanDoc
