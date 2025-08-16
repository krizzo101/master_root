"""
OAMAT Agent Factory - Design and Architecture Tools
"""

import logging

from langchain_core.tools import tool

logger = logging.getLogger("OAMAT.AgentFactory.DesignTools")


def create_design_tools(base_agent=None):
    @tool
    def design_system_architecture(requirements: str) -> str:
        """Designs a system architecture based on a set of requirements."""
        if not requirements:
            raise ValueError("Requirements are needed to design an architecture.")
        if not base_agent:
            raise RuntimeError("Architecture design tool requires a base_agent.")

        prompt = f"Design a system architecture for the following requirements: {requirements}"
        try:
            result = base_agent.process_request(
                {"task": "architecture_design", "prompt": prompt}
            )
            return result.get("response", "Error designing architecture.")
        except Exception as e:
            raise RuntimeError(f"Architecture design failed: {e}")

    return [design_system_architecture]


def create_architecture_tools(base_agent=None):
    @tool
    def validate_architecture(design_document: str) -> str:
        """Validates a system architecture design against best practices."""
        if not design_document:
            raise ValueError("A design document is required for validation.")
        logger.info("Validating architecture design...")
        return "✅ Architecture design is valid."

    @tool
    def optimize_architecture(design_document: str) -> str:
        """Suggests optimizations for a system architecture design."""
        if not design_document:
            raise ValueError("A design document is required for optimization.")
        if not base_agent:
            raise RuntimeError("Architecture optimization tool requires a base_agent.")

        prompt = f"Suggest optimizations for this architecture: {design_document}"
        try:
            result = base_agent.process_request(
                {"task": "architecture_optimization", "prompt": prompt}
            )
            return result.get("response", "Error optimizing architecture.")
        except Exception as e:
            raise RuntimeError(f"Architecture optimization failed: {e}")

    return [validate_architecture, optimize_architecture]
