"""
AI Agent Functions for Code Generation Pipeline

This module centralizes AI agent logic using modern OpenAI structured outputs.
Updated for July 2025 best practices with client.chat.completions.parse().
"""

import logging
from typing import Optional

from config import get_config
from schemas import (
    ProjectTypeDetection,
    SecurityAnalysis,
    RequirementsSpec,
    ArchitectureSpec,
)
from project_templates import ProjectType
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from local_shared.openai_interfaces.responses_interface import get_openai_interface
from audit_logger import log_prompt

# Model selector imported locally where needed

logger = logging.getLogger(__name__)


def detect_project_type_with_ai(user_request: str) -> ProjectType:
    """
    Use AI to detect the project type from a user request.

    Args:
        user_request: The raw user input describing what they want to build

    Returns:
        ProjectType enum value

    Raises:
        ValueError: If AI detection fails or returns invalid type
    """
    config = get_config()
    interface = get_openai_interface()

    # Select optimal model for structured task
    from local_shared.openai_interfaces.model_selector import ModelSelector

    model_selector = ModelSelector()
    model = model_selector.select_optimal_model(
        task_type="structured",
        require_structured_outputs=True,
        prefer_cost_effective=True,
    )

    system_prompt = f"""You are a project type classifier. Analyze the user's request and determine what type of Python project they want to build.

Valid project types are:
- cli_tool: Command-line interface applications
- web_api: REST APIs, web services, FastAPI/Flask applications
- data_processor: Data analysis, ETL, data science projects
- web_app: Full-stack web applications with frontend
- simple_script: Simple automation scripts or utilities

Provide your classification with confidence level and reasoning.
You must use the exact lowercase enum values (e.g., 'cli_tool', 'web_api') for project_type."""

    try:
        logger.info("Detecting project type with AI")

        # Log the prompt
        log_prompt(
            "ProjectTypeDetector", "project_type_detection", system_prompt, model=model
        )

        detection = interface.create_structured_response(
            prompt=f"Classify this project request: {user_request}",
            response_model=ProjectTypeDetection,
            model=model,
            system_prompt=system_prompt,
        )

        # Convert string to ProjectType enum
        try:
            project_type = ProjectType(detection.project_type)
            logger.info(
                f"AI detected project type: {project_type.value} (confidence: {detection.confidence:.2f})"
            )
            return project_type
        except ValueError:
            logger.warning(
                f"AI returned invalid project type: {detection.project_type}"
            )
            # Fallback logic
            return _fallback_project_type_detection(user_request)

    except Exception as e:
        logger.error(f"AI project type detection failed: {e}")
        return _fallback_project_type_detection(user_request)


def extract_requirements_with_ai(
    user_request: str, project_type: ProjectType, insights: str = ""
) -> RequirementsSpec:
    """
    Use AI to extract structured requirements from a user request.

    Args:
        user_request: The raw user input
        project_type: The detected project type
        insights: Optional research insights to inform requirements

    Returns:
        Structured RequirementsSpec object

    Raises:
        ValueError: If AI extraction fails
    """
    config = get_config()
    interface = get_openai_interface()

    # Use cost-effective model for requirements extraction
    from local_shared.openai_interfaces.model_selector import ModelSelector

    model_selector = ModelSelector()
    model = model_selector.select_optimal_model(
        task_type="structured",
        require_structured_outputs=True,
        prefer_cost_effective=False,  # Use more capable model for complex extraction
    )

    # Build system prompt with optional research insights
    system_prompt = f"""You are a requirements analyst. Extract detailed, structured requirements from the user's project request.

Project Type: {project_type.value}

{f'''### Latest Technical Insights ###
{insights}

''' if insights else ''}Generate:
1. A clear project title
2. A detailed description
3. Specific functional requirements (what the system should do)
4. Non-functional requirements (performance, security, usability)
5. Technology preferences mentioned by the user
6. Any constraints or limitations

{f'Use the technical insights above to inform technology choices and ensure requirements reflect current best practices.' if insights else ''}
Be thorough but concise. Each requirement should be actionable and testable."""

    try:
        logger.info("Extracting requirements with AI")

        # Log the prompt
        log_prompt(
            "RequirementsExtractor",
            "requirements_extraction",
            system_prompt,
            model=model,
        )

        requirements = interface.create_structured_response(
            prompt=f"Extract requirements from: {user_request}",
            response_model=RequirementsSpec,
            model=model,
            system_prompt=system_prompt,
        )

        logger.info(f"AI extracted requirements: {requirements.title}")
        return requirements

    except Exception as e:
        logger.error(f"AI requirements extraction failed: {e}")
        return _fallback_requirements_extraction(user_request, project_type)


def generate_architecture_with_ai(
    requirements: RequirementsSpec, insights: str = ""
) -> ArchitectureSpec:
    """
    Use AI to generate architecture specification from requirements.

    Args:
        requirements: The structured requirements
        insights: Optional research insights to inform architecture decisions

    Returns:
        Structured ArchitectureSpec object

    Raises:
        ValueError: If AI generation fails
    """
    config = get_config()
    interface = get_openai_interface()

    # Use optimal model for architecture generation
    from local_shared.openai_interfaces.model_selector import ModelSelector

    model_selector = ModelSelector()
    model = model_selector.select_optimal_model(
        task_type="structured",
        require_structured_outputs=True,
        prefer_cost_effective=False,  # Use more capable model for complex architecture
    )

    # Build system prompt with optional research insights
    system_prompt = f"""You are a senior software architect. Design a comprehensive architecture based on the provided requirements.

{f'''### Latest Technical Insights ###
{insights}

''' if insights else ''}Generate:
1. System components with names, responsibilities, and technologies
2. Complete technology stack (libraries, frameworks, databases)
3. Deployment strategy (containerization, cloud deployment, etc.)
4. Key architectural decisions with rationale

{f'Use the technical insights above to select current technologies and follow modern architectural patterns.' if insights else ''}
Provide detailed, implementable architecture that follows best practices."""

    try:
        logger.info("Generating architecture with AI")

        # Log the prompt
        log_prompt(
            "ArchitectureGenerator",
            "architecture_generation",
            system_prompt,
            model=model,
        )

        prompt = f"""Design architecture for this project:

Title: {requirements.title}
Description: {requirements.description}

Functional Requirements:
{chr(10).join(f"- {req}" for req in requirements.functional_requirements)}

Non-Functional Requirements:
{chr(10).join(f"- {req}" for req in requirements.non_functional_requirements)}

Preferred Technologies:
{chr(10).join(f"- {tech}" for tech in requirements.technologies)}

Constraints:
{chr(10).join(f"- {constraint}" for constraint in requirements.constraints)}"""

        architecture = interface.create_structured_response(
            prompt=prompt,
            response_model=ArchitectureSpec,
            model=model,
            system_prompt=system_prompt,
        )

        logger.info(
            f"AI generated architecture with {len(architecture.components)} components"
        )
        return architecture

    except Exception as e:
        logger.error(f"AI architecture generation failed: {e}")
        return _fallback_architecture_generation(requirements)


def analyze_request_security_with_ai(user_request: str) -> SecurityAnalysis:
    """
    Use AI to analyze a user request for security concerns.

    Args:
        user_request: The raw user input to analyze

    Returns:
        SecurityAnalysis object with risk assessment

    Raises:
        ValueError: If AI analysis fails
    """
    config = get_config()
    interface = get_openai_interface()

    # Use cost-effective model for security screening
    from local_shared.openai_interfaces.model_selector import ModelSelector

    model_selector = ModelSelector()
    model = model_selector.select_optimal_model(
        task_type="structured",
        require_structured_outputs=True,
        prefer_cost_effective=True,
    )

    system_prompt = """You are a security analyst. Analyze user requests for potential security risks and policy violations.

Evaluate for:
- Malicious intent (malware, hacking tools, exploits)
- Privacy violations (personal data harvesting, surveillance)
- Illegal activities (fraud, unauthorized access)
- Harmful content generation
- Resource abuse potential

Classify risk as: low, medium, or high
Provide specific concerns and actionable recommendations."""

    try:
        logger.info("Analyzing request security with AI")

        analysis = interface.create_structured_response(
            prompt=f"Analyze this request for security risks: {user_request}",
            response_model=SecurityAnalysis,
            model=model,
            system_prompt=system_prompt,
        )

        # After creation, adjust is_safe based on risk_level
        if analysis.risk_level.lower() in {"low", "medium"}:
            analysis.is_safe = True
        return analysis

    except Exception as e:
        logger.error(f"AI security analysis failed: {e}")
        return _fallback_security_analysis()


# Fallback functions for when AI fails ----------------------------------------


def _fallback_project_type_detection(user_request: str) -> ProjectType:
    """Simple keyword-based fallback for project type detection."""
    request_lower = user_request.lower()

    if any(
        word in request_lower
        for word in ["api", "rest", "fastapi", "flask", "web service"]
    ):
        return ProjectType.WEB_API
    elif any(
        word in request_lower for word in ["cli", "command", "terminal", "argparse"]
    ):
        return ProjectType.CLI_TOOL
    elif any(
        word in request_lower for word in ["data", "pandas", "analysis", "csv", "etl"]
    ):
        return ProjectType.DATA_PROCESSOR
    elif any(
        word in request_lower for word in ["app", "frontend", "react", "vue", "web app"]
    ):
        return ProjectType.WEB_APP
    else:
        return ProjectType.SIMPLE_SCRIPT


def _fallback_requirements_extraction(
    user_request: str, project_type: ProjectType
) -> RequirementsSpec:
    """Basic fallback for requirements extraction."""
    return RequirementsSpec(
        title=f"{project_type.value.replace('_', ' ').title()} Project",
        original_request=user_request,
        description=f"A {project_type.value.replace('_', ' ')} based on user requirements.",
        functional_requirements=[
            "Process user input",
            "Provide expected output",
            "Handle errors gracefully",
        ],
        non_functional_requirements=[
            "Be reliable and robust",
            "Have good performance",
            "Be maintainable",
        ],
        technologies=["Python 3.10+", "Standard library"],
        constraints=["Follow Python best practices", "Include proper error handling"],
    )


def _fallback_architecture_generation(
    requirements: RequirementsSpec,
) -> ArchitectureSpec:
    """Basic fallback for architecture generation."""
    from schemas import ArchitectureComponent

    return ArchitectureSpec(
        components=[
            ArchitectureComponent(
                name="Main Application",
                responsibility="Core application logic",
                technologies=["Python", "Standard Library"],
            )
        ],
        technology_stack=[
            "Python 3.10+",
            "pytest (testing)",
            "black (formatting)",
            "ruff (linting)",
        ],
        deployment_strategy="Local installation via pip",
        design_decisions=[
            "Use Python standard library for simplicity",
            "Follow Python PEP standards",
            "Include comprehensive tests",
        ],
    )


def extract_research_topics_with_ai(
    user_request: str, requirements: Optional["RequirementsSpec"] = None
) -> "ResearchTopics":
    """
    Extract research topics from user request and requirements using AI.

    Args:
        user_request: The raw user input describing what they want to build
        requirements: Optional parsed requirements for additional context

    Returns:
        ResearchTopics with primary technologies and secondary topics

    Raises:
        ValueError: If AI extraction fails
    """
    from schemas import ResearchTopics

    config = get_config()
    interface = get_openai_interface()

    # Select optimal model for structured task
    from local_shared.openai_interfaces.model_selector import ModelSelector

    model_selector = ModelSelector()
    model = model_selector.select_optimal_model(
        task_type="structured",
        require_structured_outputs=True,
        prefer_cost_effective=True,
    )

    # Build context from request and requirements
    context = f"User Request: {user_request}"
    if requirements:
        context += f"\n\nExtracted Technologies: {', '.join(requirements.technologies)}"
        context += f"\nFunctional Requirements: {'; '.join(requirements.functional_requirements[:3])}"

    system_prompt = """You are a research topic extraction expert. Analyze the user's project request and identify specific technologies, frameworks, libraries, and concepts that should be researched to provide up-to-date information for code generation.

Focus on:
- Specific frameworks, libraries, and technologies mentioned or implied
- Programming concepts and patterns relevant to the project
- Best practices and current standards for the domain
- Security, testing, and deployment considerations

Be comprehensive but focused - aim for 3-7 primary technologies and 3-5 secondary topics."""

    user_prompt = f"""Analyze this project request and extract research topics:

{context}

Identify the primary technologies (frameworks, libraries, databases, etc.) and secondary topics (patterns, best practices, concepts) that should be researched to ensure the generated code uses current best practices and latest versions."""

    try:
        # Log the prompt
        log_prompt(
            "ResearchTopicExtractor",
            "research_topic_extraction",
            f"{system_prompt}\n\n{user_prompt}",
            model=model,
        )

        response = interface.create_structured_response(
            prompt=user_prompt,
            response_model=ResearchTopics,
            model=model,
            system_prompt=system_prompt,
        )

        logger.info(
            f"Extracted research topics: {len(response.primary_technologies)} primary, {len(response.secondary_topics)} secondary"
        )
        return response

    except Exception as e:
        logger.error(f"Research topic extraction failed: {e}")
        # Fallback: extract basic technologies from requirements
        if requirements and requirements.technologies:
            return ResearchTopics(
                primary_technologies=requirements.technologies[:5],
                secondary_topics=["best practices", "security", "testing"],
                reasoning="Fallback extraction from parsed requirements due to AI failure",
            )
        else:
            # Last resort fallback
            return ResearchTopics(
                primary_technologies=["Python"],
                secondary_topics=["best practices"],
                reasoning="Minimal fallback due to extraction failure",
            )


def _fallback_security_analysis() -> SecurityAnalysis:
    """Conservative fallback for security analysis."""
    return SecurityAnalysis(
        risk_level="medium",
        concerns=[
            "Unable to complete AI security analysis",
            "Manual review recommended",
        ],
        recommendations=[
            "Review request manually",
            "Check for sensitive data requirements",
            "Verify legitimate business use case",
        ],
        is_safe=True,  # Allow processing but flag for review
    )
