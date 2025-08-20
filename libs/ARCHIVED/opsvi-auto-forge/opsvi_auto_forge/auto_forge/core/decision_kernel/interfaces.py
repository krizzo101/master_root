"""Interfaces for decision kernel components to break circular imports."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from openai.types.responses import Response, ResponseStreamEvent


class IPromptGateway(ABC):
    """Abstract interface for prompt gateway to break circular imports."""

    @abstractmethod
    def create_response(
        self,
        run_id: str,
        role: str,
        task_type: str,
        user_goal: str,
        constraints: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_schema: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        **kwargs,
    ) -> Union[Response, ResponseStreamEvent]:
        """Create a response using DPG-enhanced prompt."""
        pass

    @abstractmethod
    async def create_structured_response(
        self,
        run_id: str,
        role: str,
        task_type: str,
        user_goal: str,
        schema: Union[Dict[str, Any], type],
        constraints: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        verifier_model: str = "gpt-4o-mini",
        max_repair_attempts: int = 1,
        **kwargs,
    ) -> Any:
        """Create a structured response with schema validation."""
        pass

    @abstractmethod
    def create_with_reasoning(
        self,
        run_id: str,
        role: str,
        task_type: str,
        user_goal: str,
        effort: str = "medium",
        include_encrypted: bool = False,
        constraints: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Response:
        """Create a response with reasoning capabilities."""
        pass

    @abstractmethod
    def create_background_task(
        self,
        run_id: str,
        role: str,
        task_type: str,
        user_goal: str,
        constraints: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Response:
        """Create a background task response."""
        pass


class ITaskAnalyzer(ABC):
    """Abstract interface for task analyzer."""

    @abstractmethod
    async def analyze_task(
        self,
        task_id: UUID,
        agent: str,
        task_type: str,
        budget_hint: Dict[str, Any],
        task_input: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze a task and return analysis results."""
        pass
