"""
Orchestration Interface Contracts

ABC interfaces for orchestration components emphasizing dynamic
workflow generation and adaptive coordination.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from src.applications.oamat_sd.src.models.data_models import (
    AgentState,
)


class ILangGraphOrchestrator(ABC):
    """Interface for dynamic LangGraph workflow orchestration"""

    @abstractmethod
    async def build_dynamic_workflow(self, workflow_spec: Dict[str, Any]) -> Any:
        """
        Build LangGraph workflow from dynamically generated specifications

        Must construct workflows from O3-generated designs,
        not use predefined workflow templates.
        """
        pass

    @abstractmethod
    async def execute_adaptive_workflow(
        self, workflow: Any, initial_state: AgentState
    ) -> Dict[str, Any]:
        """
        Execute workflow with adaptive coordination

        Must adapt execution based on runtime conditions,
        not follow static execution patterns.
        """
        pass

    @abstractmethod
    async def coordinate_agents_dynamically(
        self, agents: List[Any], coordination_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Coordinate agents using dynamically generated coordination strategies

        Must implement novel coordination approaches,
        not use predefined coordination patterns.
        """
        pass

    @abstractmethod
    async def adapt_workflow_realtime(
        self, workflow: Any, execution_state: Dict[str, Any]
    ) -> Any:
        """
        Adapt workflow structure during execution based on results

        Must modify workflow based on intelligent analysis,
        not predefined adaptation rules.
        """
        pass


class IMCPToolRegistry(ABC):
    """Interface for intelligent MCP tool management and selection"""

    @abstractmethod
    async def select_tools_intelligently(
        self, requirements: Dict[str, Any]
    ) -> List[Any]:
        """
        Intelligently select tools based on contextual analysis

        Must analyze tool needs contextually,
        not use predefined tool categories.
        """
        pass

    @abstractmethod
    async def optimize_tool_usage(
        self, tools: List[Any], execution_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Optimize tool usage patterns based on context

        Must generate intelligent usage strategies,
        not apply static optimization rules.
        """
        pass

    @abstractmethod
    async def monitor_tool_performance_adaptively(
        self, tools: List[Any]
    ) -> Dict[str, Any]:
        """
        Adaptively monitor and adjust tool performance

        Must adapt monitoring based on usage patterns,
        not use fixed monitoring strategies.
        """
        pass
