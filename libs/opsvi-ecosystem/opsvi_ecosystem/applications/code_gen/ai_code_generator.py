"""
AI-Powered Code Generation Module

Replaces static templates with dynamic AI-generated code based on requirements and architecture.
Uses OpenAI structured outputs for reliable code generation.
"""

from __future__ import annotations

import logging

from local_shared.openai_interfaces.responses_interface import get_openai_interface

# Model selector imported locally where needed
from project_templates import ProjectType
from pydantic import BaseModel, Field

from config import get_config
from schemas import ArchitectureSpec, RequirementsSpec

logger = logging.getLogger(__name__)


class GeneratedFile(BaseModel):
    """Represents a single generated code file."""

    filename: str = Field(..., description="Relative path and filename")
    content: str = Field(..., description="Complete file content")
    purpose: str = Field(..., description="What this file does")


class CodeGeneration(BaseModel):
    """Complete code generation output."""

    main_files: list[GeneratedFile] = Field(..., description="Main application files")
    test_files: list[GeneratedFile] = Field(..., description="Test files")
    config_files: list[GeneratedFile] = Field(..., description="Configuration files")
    dependencies: list[str] = Field(..., description="Required Python packages")
    setup_instructions: str = Field(..., description="Setup and usage instructions")


class AICodeGenerator:
    """AI-powered code generator that creates project files based on requirements."""

    def __init__(self):
        self.interface = get_openai_interface()
        self.config = get_config()

    def generate_project_code(
        self,
        requirements: RequirementsSpec,
        architecture: ArchitectureSpec,
        project_type: ProjectType,
        insights: str = "",
    ) -> CodeGeneration:
        """
        Generate complete project code using AI based on requirements and architecture.

        Args:
            requirements: Structured requirements from user input
            architecture: AI-generated architecture specification
            project_type: Type of project to generate
            insights: Optional research insights to inform code generation

        Returns:
            Complete code generation with all files
        """
        logger.info(f"Generating AI-powered code for {project_type.value} project")

        # Select optimal model for code generation
        from local_shared.openai_interfaces.model_selector import ModelSelector

        model_selector = ModelSelector()
        model = model_selector.select_optimal_model(
            task_type="execution",
            require_structured_outputs=True,
            prefer_cost_effective=False,  # Use more capable model for code generation
        )

        # Create comprehensive prompt for code generation
        system_prompt = self._build_system_prompt(project_type, insights)
        user_prompt = self._build_user_prompt(requirements, architecture, project_type)

        try:
            generation = self.interface.create_structured_response(
                prompt=user_prompt,
                response_model=CodeGeneration,
                model=model,
                system_prompt=system_prompt,
            )

            logger.info(
                f"Generated {len(generation.main_files)} main files, "
                f"{len(generation.test_files)} test files, "
                f"{len(generation.config_files)} config files"
            )

            return generation

        except Exception as e:
            logger.error(f"AI code generation failed: {e}")
            # Fallback to basic template-based generation
            return self._fallback_generation(requirements, project_type)

    def _build_system_prompt(
        self, project_type: ProjectType, insights: str = ""
    ) -> str:
        """Build system prompt for code generation."""

        base_prompt = """You are an expert Python developer and software architect. Generate complete, production-ready code based on the user's requirements and architecture specifications.

CRITICAL REQUIREMENTS:
- Generate COMPLETE, FUNCTIONAL code - not snippets or placeholders
- Include proper error handling, logging, and documentation
- Follow Python best practices (PEP 8, type hints, docstrings)
- Create realistic, working implementations
- Include proper imports and dependencies
- Generate meaningful test cases that actually test functionality
- Use modern Python 3.10+ features when appropriate

CODE QUALITY STANDARDS:
- All functions must have type hints and docstrings
- Include comprehensive error handling
- Use logging for debugging and monitoring
- Follow SOLID principles and clean code practices
- Add input validation where appropriate
- Include configuration management
- Generate realistic sample data and examples"""

        project_specific = {
            ProjectType.WEB_API: """
FASTAPI SPECIFIC REQUIREMENTS:
- Use FastAPI with proper routing and dependency injection
- Include Pydantic models for request/response validation
- Add proper HTTP status codes and error responses
- Include middleware for CORS, security, logging
- Generate OpenAPI documentation
- Add health check endpoints
- Include proper async/await patterns
- Add database models if data persistence is needed""",
            ProjectType.CLI_TOOL: """
CLI TOOL SPECIFIC REQUIREMENTS:
- Use Click or argparse for command-line interface
- Include proper help text and examples
- Add configuration file support
- Include progress bars for long operations
- Add proper exit codes and error messages
- Support common CLI patterns (verbose, quiet, etc.)
- Include shell completion support when possible""",
            ProjectType.WEB_APP: """
WEB APP SPECIFIC REQUIREMENTS:
- Use Flask or FastAPI with template rendering
- Include proper HTML templates with modern CSS
- Add form handling and validation
- Include session management and security
- Add proper routing and error pages
- Include static file serving
- Generate responsive, accessible HTML""",
            ProjectType.DATA_PROCESSOR: """
DATA PROCESSING SPECIFIC REQUIREMENTS:
- Use pandas, numpy for data manipulation
- Include proper data validation and cleaning
- Add support for multiple input/output formats
- Include data quality checks and error reporting
- Add progress tracking for large datasets
- Include data visualization when appropriate
- Generate sample data for testing""",
            ProjectType.SIMPLE_SCRIPT: """
SIMPLE SCRIPT SPECIFIC REQUIREMENTS:
- Create focused, single-purpose functionality
- Include proper command-line interface
- Add configuration options
- Include file I/O operations when needed
- Add proper logging and error messages
- Make script easily extensible""",
        }

        final_prompt = base_prompt + "\n\n" + project_specific.get(project_type, "")

        # Add research insights if available
        if insights:
            final_prompt += f"""

### LATEST TECHNICAL INSIGHTS ###
{insights}

Use these insights to inform your technology choices, ensure you're using current versions, and follow modern best practices."""

        return final_prompt

    def _build_user_prompt(
        self,
        requirements: RequirementsSpec,
        architecture: ArchitectureSpec,
        project_type: ProjectType,
    ) -> str:
        """Build user prompt with specific requirements and architecture."""

        prompt = f"""Generate a complete {project_type.value.replace('_', ' ')} project with the following specifications:

PROJECT TITLE: {requirements.title}
ORIGINAL REQUEST: {requirements.original_request}

FUNCTIONAL REQUIREMENTS:
{chr(10).join(f"- {req}" for req in requirements.functional_requirements)}

NON-FUNCTIONAL REQUIREMENTS:
{chr(10).join(f"- {req}" for req in requirements.non_functional_requirements)}

ARCHITECTURE COMPONENTS:
{chr(10).join(f"- {comp.name}: {comp.responsibility} (using {', '.join(comp.technologies)})" for comp in architecture.components)}

TECHNOLOGY STACK:
{chr(10).join(f"- {tech}" for tech in architecture.technology_stack)}

CONSTRAINTS:
{chr(10).join(f"- {constraint}" for constraint in requirements.constraints)}

DESIGN DECISIONS:
{chr(10).join(f"- {decision}" for decision in architecture.design_decisions)}

Generate a complete, working implementation that satisfies all requirements. Include:
1. Main application files with full functionality
2. Comprehensive test files that verify the implementation
3. Configuration files (requirements.txt, config files, etc.)
4. Clear setup and usage instructions

Make sure the code is production-ready, well-documented, and follows modern Python best practices."""

        return prompt

    def _fallback_generation(
        self, requirements: RequirementsSpec, project_type: ProjectType
    ) -> CodeGeneration:
        """Fallback generation when AI fails."""

        logger.warning("Using fallback code generation")

        # Simple fallback based on project type
        if project_type == ProjectType.SIMPLE_SCRIPT:
            return CodeGeneration(
                main_files=[
                    GeneratedFile(
                        filename="main.py",
                        content=f'''#!/usr/bin/env python3
"""
{requirements.title}

{requirements.description}
"""

import logging
import sys
from pathlib import Path


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


def main():
    """Main application logic."""
    logger = logging.getLogger(__name__)
    logger.info("Starting {requirements.title}")

    # Implementation based on: {requirements.original_request}
    print("Application is running...")

    # TODO: Implement specific functionality

    logger.info("Application completed successfully")


if __name__ == "__main__":
    setup_logging()
    main()
''',
                        purpose="Main application entry point",
                    )
                ],
                test_files=[
                    GeneratedFile(
                        filename="test_main.py",
                        content='''import pytest
from main import main


def test_main_execution():
    """Test that main function executes without error."""
    main()  # Should not raise an exception
''',
                        purpose="Basic functionality tests",
                    )
                ],
                config_files=[
                    GeneratedFile(
                        filename="requirements.txt",
                        content="# Add dependencies here\n",
                        purpose="Python package dependencies",
                    )
                ],
                dependencies=[],
                setup_instructions=f"""# {requirements.title}

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python main.py
```

## Description
{requirements.description}
""",
            )

        # Add more fallback implementations for other project types as needed
        return self._fallback_generation(requirements, ProjectType.SIMPLE_SCRIPT)


def generate_ai_code(
    requirements: RequirementsSpec,
    architecture: ArchitectureSpec,
    project_type: ProjectType,
) -> CodeGeneration:
    """
    Main function to generate AI-powered code.

    Args:
        requirements: User requirements specification
        architecture: Generated architecture specification
        project_type: Type of project to generate

    Returns:
        Complete code generation result
    """
    generator = AICodeGenerator()
    return generator.generate_project_code(requirements, architecture, project_type)
