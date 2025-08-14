"""Legacy agent adapter for backward compatibility."""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

import structlog

from ..core import BaseAgent, AgentConfig, AgentResult
from ..registry import AgentRegistry

logger = structlog.get_logger(__name__)


class UniversalAgentAdapter(BaseAgent):
    """Adapter to run legacy agents in V2 framework."""
    
    def __init__(self, config: AgentConfig, legacy_agent: Any = None):
        """Initialize adapter with legacy agent."""
        super().__init__(config)
        self.legacy_agent = legacy_agent
        self._logger = logger.bind(adapter="UniversalAgentAdapter")
    
    def _execute(self, prompt: str, **kwargs) -> Any:
        """Execute legacy agent."""
        if not self.legacy_agent:
            raise ValueError("No legacy agent configured")
        
        # Map V2 parameters to legacy format
        legacy_params = self._map_to_legacy(prompt, kwargs)
        
        # Execute legacy agent
        try:
            # Try different execution patterns
            if hasattr(self.legacy_agent, "execute"):
                result = self.legacy_agent.execute(**legacy_params)
            elif hasattr(self.legacy_agent, "run"):
                result = self.legacy_agent.run(**legacy_params)
            elif hasattr(self.legacy_agent, "__call__"):
                result = self.legacy_agent(**legacy_params)
            else:
                raise ValueError("Legacy agent has no known execution method")
            
            # Map result back to V2 format
            return self._map_from_legacy(result)
            
        except Exception as e:
            self._logger.error("Legacy execution failed", error=str(e))
            raise
    
    def _map_to_legacy(self, prompt: str, kwargs: Dict) -> Dict:
        """Map V2 parameters to legacy format."""
        # Common legacy parameter mappings
        legacy_params = {
            "prompt": prompt,
            "task": prompt,  # Some legacy agents use 'task'
            "input": prompt,  # Others use 'input'
            **kwargs
        }
        
        # Map config to legacy format if needed
        if hasattr(self.legacy_agent, "config"):
            legacy_params["config"] = {
                "model": self.config.model,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            }
        
        return legacy_params
    
    def _map_from_legacy(self, result: Any) -> Any:
        """Map legacy result to V2 format."""
        # Handle different legacy result formats
        if isinstance(result, dict):
            if "output" in result:
                return result["output"]
            elif "result" in result:
                return result["result"]
            elif "response" in result:
                return result["response"]
            else:
                return result
        else:
            return result
    
    @classmethod
    def from_legacy_class(cls, legacy_class: type, config: AgentConfig) -> "UniversalAgentAdapter":
        """Create adapter from legacy agent class."""
        try:
            # Instantiate legacy agent
            legacy_agent = legacy_class()
            return cls(config, legacy_agent)
        except Exception as e:
            logger.error("Failed to create legacy adapter", error=str(e))
            raise
    
    @classmethod
    def from_legacy_instance(cls, legacy_agent: Any, config: AgentConfig) -> "UniversalAgentAdapter":
        """Create adapter from legacy agent instance."""
        return cls(config, legacy_agent)


def migrate_legacy_agent(legacy_agent: Any, name: str = None) -> UniversalAgentAdapter:
    """Helper to migrate legacy agent to V2."""
    config = AgentConfig(
        name=name or getattr(legacy_agent, "name", "legacy_agent"),
        model=getattr(legacy_agent, "model", "gpt-4o-mini"),
        metadata={"legacy": True}
    )
    
    if isinstance(legacy_agent, type):
        return UniversalAgentAdapter.from_legacy_class(legacy_agent, config)
    else:
        return UniversalAgentAdapter.from_legacy_instance(legacy_agent, config)
