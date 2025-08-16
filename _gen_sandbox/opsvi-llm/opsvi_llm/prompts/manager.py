"""Prompt manager for opsvi-llm.

Manages prompt templates and generation.
"""

from typing import Dict, Any, Optional, List
import json
import logging

from opsvi_llm.core.base import OpsviLlmManager
from opsvi_llm.config.settings import OpsviLlmConfig
from opsvi_llm.exceptions.base import OpsviLlmError

logger = logging.getLogger(__name__)

class PromptTemplate:
    """Prompt template class."""
    def __init__(self, name: str, template: str, variables: List[str] = None):
        self.name = name
        self.template = template
        self.variables = variables or []

    def format(self, **kwargs) -> str:
        """Format the prompt template."""
        return self.template.format(**kwargs)

class OpsviLlmPromptManager(OpsviLlmManager):
    """Prompt manager for opsvi-llm."""

    def __init__(self, config: OpsviLlmConfig):
        super().__init__(config=config)
        self.templates: Dict[str, PromptTemplate] = {}

    async def register_template(self, name: str, template: str,
                              variables: List[str] = None) -> None:
        """Register a prompt template."""
        self.templates[name] = PromptTemplate(name, template, variables)
        logger.info(f"Registered prompt template: {name}")

    async def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a prompt template by name."""
        return self.templates.get(name)

    async def format_prompt(self, name: str, **kwargs) -> str:
        """Format a prompt template."""
        template = await self.get_template(name)
        if not template:
            raise OpsviLlmError(f"Template not found: {name}")
        return template.format(**kwargs)
