"""Central agent registry."""

from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass

import structlog

from ..core import BaseAgent, AgentConfig

logger = structlog.get_logger(__name__)


@dataclass
class AgentDefinition:
    """Agent definition with metadata."""
    name: str
    agent_class: Type[BaseAgent]
    description: str
    default_config: AgentConfig
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class AgentRegistry:
    """Central registry for agent types."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._agents: Dict[str, AgentDefinition] = {}
        self._tags: Dict[str, List[str]] = {}
        self._logger = logger.bind(component="AgentRegistry")
        self._initialized = True
    
    def register(
        self,
        name: str,
        agent_class: Type[BaseAgent],
        description: str = None,
        default_config: AgentConfig = None,
        tags: List[str] = None
    ) -> None:
        """Register an agent type."""
        if name in self._agents:
            self._logger.warning("Overwriting existing agent", name=name)
        
        # Create default config if not provided
        if default_config is None:
            default_config = AgentConfig(name=name)
        
        # Create agent definition
        definition = AgentDefinition(
            name=name,
            agent_class=agent_class,
            description=description or agent_class.__doc__ or "",
            default_config=default_config,
            tags=tags or []
        )
        
        # Register agent
        self._agents[name] = definition
        
        # Update tag index
        for tag in definition.tags:
            if tag not in self._tags:
                self._tags[tag] = []
            self._tags[tag].append(name)
        
        self._logger.info("Agent registered", name=name, class_name=agent_class.__name__)
    
    def create(self, name: str, config: AgentConfig = None) -> BaseAgent:
        """Create agent instance."""
        definition = self._agents.get(name)
        if not definition:
            raise ValueError(f"Agent not found: {name}")
        
        # Use provided config or default
        agent_config = config or definition.default_config
        
        # Create agent instance
        try:
            agent = definition.agent_class(agent_config)
            self._logger.info("Agent created", name=name)
            return agent
        except Exception as e:
            self._logger.error("Agent creation failed", name=name, error=str(e))
            raise
    
    def get_definition(self, name: str) -> Optional[AgentDefinition]:
        """Get agent definition."""
        return self._agents.get(name)
    
    def list_agents(self, tag: str = None) -> List[str]:
        """List available agents."""
        if tag:
            return self._tags.get(tag, [])
        return list(self._agents.keys())
    
    def get_tags(self) -> List[str]:
        """Get all tags."""
        return list(self._tags.keys())
    
    def clear(self) -> None:
        """Clear registry."""
        self._agents.clear()
        self._tags.clear()
        self._logger.info("Registry cleared")
    
    def __contains__(self, name: str) -> bool:
        """Check if agent exists."""
        return name in self._agents
    
    def __len__(self) -> int:
        """Get number of registered agents."""
        return len(self._agents)


# Global registry instance
registry = AgentRegistry()
