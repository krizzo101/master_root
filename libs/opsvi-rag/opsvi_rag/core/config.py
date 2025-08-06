"""
Configuration for opsvi-rag.

Extends foundation configuration with RAG-specific settings.
"""

from typing import Optional
from pydantic import BaseModel, Field
from opsvi_foundation import FoundationConfig


class RAGConfig(BaseModel):
    """Configuration for opsvi-rag."""
    
    # Inherit foundation settings
    foundation: FoundationConfig = Field(default_factory=FoundationConfig.from_env)
    
    # Domain-specific settings can be added here
    
    @classmethod
    def from_env(cls) -> "RAGConfig":
        """Create configuration from environment variables."""
        return cls(
            foundation=FoundationConfig.from_env(),
        )


# Global configuration instance
config = RAGConfig.from_env()
