"""
OAMAT Agent Factory - Diagram Generation Tools
"""

import logging

from langchain_core.tools import tool

logger = logging.getLogger("OAMAT.AgentFactory.DiagrammingTools")


def create_diagram_generation_tools(base_agent=None):
    @tool
    def generate_architecture_diagram(system_description: str) -> str:
        """Generates a system architecture diagram from a description."""
        if not system_description:
            raise ValueError("A system description is required to generate a diagram.")
        if not base_agent:
            raise RuntimeError("Diagram generation tool requires a base_agent.")

        prompt = f"Generate a Mermaid syntax diagram for the following system: {system_description}"
        try:
            result = base_agent.process_request(
                {"task": "diagram_generation", "prompt": prompt}
            )
            return result.get("response", "Error generating diagram.")
        except Exception as e:
            raise RuntimeError(f"Diagram generation failed: {e}")

    @tool
    def create_flowchart(process_description: str) -> str:
        """Creates a process flowchart from a description."""
        if not process_description:
            raise ValueError("A process description is required to create a flowchart.")
        if not base_agent:
            raise RuntimeError("Flowchart creation tool requires a base_agent.")

        prompt = f"Generate a Mermaid syntax flowchart for the following process: {process_description}"
        try:
            result = base_agent.process_request(
                {"task": "flowchart_creation", "prompt": prompt}
            )
            return result.get("response", "Error creating flowchart.")
        except Exception as e:
            raise RuntimeError(f"Flowchart creation failed: {e}")

    return [generate_architecture_diagram, create_flowchart]
