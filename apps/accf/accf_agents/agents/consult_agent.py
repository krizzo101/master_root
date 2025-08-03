"""
Consult Agent - Refactored version for the new ACCF agents structure.

This module provides a refactored version of the original consult_agent.py,
split into smaller, more maintainable components.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from .base import BaseAgent, Task, Result


class ConsultAgent(BaseAgent):
    """
    ConsultAgent (Architect) using OpenAI Responses API (o3) with session management.

    Specialized in generating detailed, actionable prompts for GPT-4.1 development agents.
    Leverages o3's advanced reasoning capabilities to create comprehensive prompts
    that guide GPT-4.1 agents through complex development tasks.
    """

    def __init__(self, name: str, settings: Any):
        super().__init__(name, settings)
        self.model = "o3"
        self.assistant_name = "Architect_o3"
        self.session_timeout = 60 * 60  # 1 hour
        self.session_store: Dict[str, Dict] = {}

        # Set up comprehensive debug logging
        self.logger.setLevel(logging.DEBUG)
        self.logger.info("=== CONSULT AGENT INITIALIZED WITH DEBUG LOGGING ===")

    def can_handle(self, task_type: str) -> bool:
        """Check if this agent can handle the given task type."""
        return task_type in ["consult", "prompt_generation", "architect", "design"]

    def get_capabilities(self) -> List[str]:
        """Get list of task types this agent can handle."""
        return ["consult", "prompt_generation", "architect", "design"]

    async def execute(self, task: Task) -> Result:
        """Execute a consult task."""
        try:
            self.logger.info(f"Executing consult task: {task.id}")

            # Extract parameters
            prompt = task.parameters.get("prompt", "")
            session_id = task.parameters.get("session_id", "default")
            file_paths = task.parameters.get("file_paths", [])
            artifact_type = task.parameters.get("artifact_type")
            iterate = task.parameters.get("iterate")
            critic_enabled = task.parameters.get("critic_enabled", False)
            model = task.parameters.get("model")

            # Execute the consult logic
            response = await self._execute_consult(
                prompt=prompt,
                session_id=session_id,
                file_paths=file_paths,
                artifact_type=artifact_type,
                iterate=iterate,
                critic_enabled=critic_enabled,
                model=model,
            )

            return Result(
                task_id=task.id,
                status="success",
                data=response,
                execution_time=time.time(),
            )

        except Exception as e:
            self.logger.error(f"Error executing consult task {task.id}: {e}")
            return Result(
                task_id=task.id,
                status="error",
                data={},
                error_message=str(e),
                execution_time=time.time(),
            )

    async def _execute_consult(
        self,
        prompt: str,
        session_id: str = "default",
        file_paths: List[str] = None,
        artifact_type: str = None,
        iterate: int = None,
        critic_enabled: bool = False,
        model: str = None,
    ) -> Dict[str, Any]:
        """Execute the core consult logic."""
        self.logger.info(f"Processing consult request for session: {session_id}")

        # Get or create session
        session = self._get_or_create_session(session_id)

        # Build the enhanced prompt with artifact guidance
        enhanced_prompt = self._build_enhanced_prompt(prompt, artifact_type, file_paths)

        # Validate model parameter against @953-openai-api-standards.mdc
        APPROVED_MODELS = {"o4-mini", "o3", "gpt-4.1-mini", "gpt-4.1", "gpt-4.1-nano"}
        if model is not None and model not in APPROVED_MODELS:
            raise ValueError(
                f"UNAUTHORIZED MODEL: {model}. Only approved models are allowed: {', '.join(APPROVED_MODELS)}"
            )

        # Use provided model or default to o3
        selected_model = model if model is not None else self.model

        # Process the request (simplified for now - would integrate with o3 API)
        response = {
            "session_id": session_id,
            "response": f"Processed consult request: {prompt[:100]}...",
            "artifact_type": artifact_type,
            "enhanced_prompt": enhanced_prompt,
            "timestamp": time.time(),
            "session_active": True,
            "file_paths": file_paths or [],
            "iterate": iterate,
            "critic_enabled": critic_enabled,
            "model": selected_model,
        }

        return response

    def _build_enhanced_prompt(
        self, prompt: str, artifact_type: str = None, file_paths: List[str] = None
    ) -> str:
        """Build an enhanced prompt with artifact-specific guidance."""
        enhanced_prompt = prompt

        if artifact_type:
            artifact_guidance = self._get_artifact_guidance(artifact_type)
            if artifact_guidance:
                enhanced_prompt = f"{artifact_guidance}\n\n{enhanced_prompt}"

        if file_paths:
            file_context = f"\n\nAttached files: {', '.join(file_paths)}"
            enhanced_prompt += file_context

        return enhanced_prompt

    def _get_artifact_guidance(self, artifact_type: str) -> str:
        """
        Get artifact-specific guidance for prompt generation.

        Args:
            artifact_type: The type of artifact being generated

        Returns:
            str: Artifact-specific guidance text
        """
        guidance_map = {
            "answer": """
## ARTIFACT TYPE: GENERAL ANSWER
**Purpose**: General responses and analysis without specific output format requirements

## ROLE PROFILE: STRATEGIC ANALYST
**Skills**: Systems thinking, pattern recognition, strategic planning, risk assessment
**Experience**: 10+ years in software architecture, system design, and technical strategy
**Focus**: Holistic analysis, cross-cutting concerns, long-term implications, strategic recommendations
**Behavioral Characteristics**:
- Thinks in systems and patterns rather than isolated components
- Considers multiple perspectives and trade-offs
- Focuses on actionable insights and strategic implications
- Balances technical depth with business impact
- Identifies root causes and systemic issues

**Requirements**:
- Provide comprehensive analysis and recommendations
- Include relevant context and background information
- Structure response logically with clear sections
- Include actionable insights and next steps
- Consider multiple perspectives and edge cases
**Output Format**: Well-structured markdown response with clear organization""",
            "plan": """
## ARTIFACT TYPE: PROJECT PLAN (.md)
**Purpose**: Comprehensive project planning and execution roadmaps

## ROLE PROFILE: PROJECT MANAGER & TECHNICAL ARCHITECT
**Skills**: Project planning, technical architecture, risk management, resource allocation, timeline management
**Experience**: 10+ years in project management, technical leadership, and software delivery
**Focus**: Strategic planning, execution feasibility, risk mitigation, stakeholder alignment, delivery excellence
**Behavioral Characteristics**:
- Thinks in terms of project phases, dependencies, and critical paths
- Prioritizes realistic timelines, resource constraints, and risk management
- Considers stakeholder needs, technical constraints, and business objectives
- Focuses on measurable outcomes, milestones, and success criteria
- Anticipates potential blockers, dependencies, and mitigation strategies
- Balances scope, timeline, and quality requirements
- Considers team dynamics, skill gaps, and capacity planning
- Plans for contingencies, rollback strategies, and change management

**Requirements**:
- Include project overview, objectives, and success criteria
- Define phases, milestones, and deliverables with timelines
- Identify risks, dependencies, and mitigation strategies
- Specify resource requirements, roles, and responsibilities
- Include technical architecture, design decisions, and constraints
- Provide stakeholder communication and governance structure
- Include quality gates, testing strategy, and deployment approach
- Specify monitoring, metrics, and success measurement criteria
**Output Format**: Comprehensive project plan in markdown with clear structure, timelines, and actionable items""",
            "code": """
## ARTIFACT TYPE: CODE (.py)
**Purpose**: Python scripts for specific functionality

## ROLE PROFILE: SENIOR PYTHON DEVELOPER
**Skills**: Python mastery, software engineering, debugging, performance optimization, testing
**Experience**: 8+ years in Python development, production systems, and software architecture
**Focus**: Code quality, maintainability, performance, security, production readiness
**Behavioral Characteristics**:
- Writes defensive, production-ready code with comprehensive error handling
- Prioritizes code clarity and maintainability over cleverness
- Thinks about edge cases, failure modes, and debugging scenarios
- Considers performance implications and resource usage
- Follows established patterns and best practices religiously
- Documents code for future maintainers

## DIRECT ARTIFACT GENERATION
You are a Senior Python Developer. Generate the actual Python code that the user has requested.

**Your Task**: Create production-quality Python code that:
- Includes proper imports and dependencies
- Has comprehensive error handling and logging
- Follows PEP 8 standards and type hints
- Includes docstrings and comments
- Is ready to run with minimal setup

**Output**: Return the complete Python code in a code block, ready to use.""",
            "prompt": """
## ARTIFACT TYPE: PROMPT (markdown)
**Purpose**: LLM prompts for specific tasks

## ROLE PROFILE: PROMPT ENGINEER
**Skills**: LLM optimization, prompt design, model behavior, human-AI interaction
**Experience**: 5+ years in prompt engineering, LLM optimization, and AI interaction design
**Focus**: Clarity, effectiveness, model alignment, user experience, prompt optimization
**Behavioral Characteristics**:
- Thinks in terms of model behavior, capabilities, and limitations
- Prioritizes clarity, specificity, and effective communication with AI
- Considers model context windows, token limits, and optimization strategies
- Focuses on prompt structure, examples, and verification mechanisms
- Anticipates model confusion, hallucination, and edge cases
- Balances detail with token efficiency
- Considers the target model's strengths and weaknesses
- Plans for prompt evolution and model updates

**Requirements**:
- Specify target model and expected output format
- Include clear constraints and examples
- Define role, objective, and audience
- Use structured formatting with clear sections
- Include verification steps and quality criteria
**Output Format**: Markdown-formatted prompt with examples""",
            "test": """
## ARTIFACT TYPE: TEST (.py)
**Purpose**: Test files for functionality validation

## ROLE PROFILE: TEST ENGINEER
**Skills**: Test automation, quality assurance, debugging, test design, coverage analysis
**Experience**: 6+ years in test engineering, quality assurance, and test automation
**Focus**: Quality, reliability, maintainability, comprehensive coverage, automation
**Behavioral Characteristics**:
- Thinks in terms of test scenarios, edge cases, and failure modes
- Prioritizes test reliability, maintainability, and comprehensive coverage
- Considers both positive and negative test cases
- Thinks about test data, fixtures, and test environment setup
- Anticipates potential failures and debugging scenarios
- Focuses on test automation and repeatability
- Considers test performance and execution time
- Plans for test maintenance and evolution

**Requirements**:
- Include unit tests, integration tests, and edge cases
- Use pytest framework and best practices
- Mock external dependencies appropriately
- Include test data and fixtures
- Specify test coverage requirements
**Output Format**: Python test file with comprehensive test cases""",
            "doc": """
## ARTIFACT TYPE: DOCUMENTATION (.md)
**Purpose**: Documentation with markdown formatting

## ROLE PROFILE: TECHNICAL WRITER
**Skills**: Technical communication, information architecture, user experience, visual design
**Experience**: 5+ years in technical writing, developer documentation, and user experience
**Focus**: Clarity, accessibility, user journey, information hierarchy, visual communication
**Behavioral Characteristics**:
- Thinks from the user's perspective and experience level
- Structures information for easy scanning and comprehension
- Uses visual elements (diagrams, tables, code blocks) to enhance understanding
- Anticipates user questions and provides answers proactively
- Balances completeness with conciseness
- Considers multiple learning styles and accessibility needs
- Creates documentation that ages well and stays relevant

**Requirements**:
- Use markdown formatting with clear structure
- Include mermaid diagrams where appropriate for visual clarity
- Provide usage examples and code snippets
- Include installation and setup instructions
- Specify target audience and technical depth
**Output Format**: Markdown documentation with diagrams and examples""",
            "design": """
## ARTIFACT TYPE: DESIGN (.md/.mdd)
**Purpose**: System design, architecture, and technical design documents

## ROLE PROFILE: SOLUTION ARCHITECT & SYSTEM DESIGNER
**Skills**: System architecture, design patterns, scalability, performance, security, integration
**Experience**: 12+ years in solution architecture, system design, and technical leadership
**Focus**: Scalability, maintainability, performance, security, integration, operational excellence
**Behavioral Characteristics**:
- Thinks in terms of systems, components, and their interactions
- Prioritizes scalability, performance, and operational concerns
- Considers multiple architectural patterns and trade-offs
- Focuses on long-term maintainability and evolution
- Anticipates failure modes, bottlenecks, and scaling challenges
- Balances technical excellence with practical constraints
- Considers security, compliance, and risk management
- Plans for system evolution and technology changes

**Requirements**:
- Include system overview and architecture diagrams
- Define components, interfaces, and data flows
- Specify design patterns and architectural decisions
- Include performance, scalability, and security considerations
- Provide implementation guidance and constraints
- Include monitoring, logging, and operational aspects
- Consider failure modes and recovery strategies
- Specify technology stack and integration points
**Output Format**: Comprehensive design document with diagrams and implementation guidance""",
            "diagram": """
## ARTIFACT TYPE: DIAGRAM (.mdd)
**Purpose**: Mermaid diagrams for visual representation

## ROLE PROFILE: SOLUTION ARCHITECT
**Skills**: System design, visual communication, information architecture, technical visualization
**Experience**: 8+ years in solution architecture, system design, and technical communication
**Focus**: Clarity, accuracy, visual hierarchy, accessibility, effective communication
**Behavioral Characteristics**:
- Thinks in terms of systems, components, and their interactions
- Prioritizes visual clarity and information hierarchy
- Considers the audience's technical background and needs
- Uses appropriate diagram types for different purposes (flow, sequence, architecture)
- Ensures diagrams are self-contained and understandable
- Balances detail with readability
- Considers accessibility and different viewing contexts
- Creates diagrams that serve multiple purposes (documentation, planning, communication)

**Requirements**:
- Use Mermaid syntax exclusively
- High contrast: Light text/lines on dark background OR dark text/lines on light background
- Ensure accessibility and readability
- Include proper labels and relationships
- Use appropriate diagram types (flowchart, sequence, class, etc.)
**Output Format**: Mermaid diagram with high contrast styling""",
            "query": """
## ARTIFACT TYPE: DATABASE QUERY (SQL/Cypher)
**Purpose**: Database queries for data operations

## ROLE PROFILE: DATABASE ADMINISTRATOR
**Skills**: Database optimization, query performance, data modeling, indexing strategies
**Experience**: 10+ years in database administration, query optimization, and data architecture
**Focus**: Performance, scalability, data integrity, security, optimization
**Behavioral Characteristics**:
- Thinks in terms of data relationships, indexes, and query execution plans
- Prioritizes query performance and resource efficiency
- Considers data volume, growth patterns, and scalability implications
- Thinks about data integrity, constraints, and validation
- Anticipates edge cases in data and query patterns
- Considers security implications and access patterns
- Plans for maintenance, monitoring, and troubleshooting

**Requirements**:
- ALWAYS include database schema in the request
- Provide table structures, relationships, and sample data
- Include proper error handling and optimization
- Specify query performance requirements
- Include expected output format and data types
**Output Format**: SQL or Cypher query with schema context""",
            "rule": """
## ARTIFACT TYPE: CURSOR RULE (.mdc)
**Purpose**: Cursor rules for development standards

## ROLE PROFILE: DEVELOPMENT STANDARDS ENGINEER
**Skills**: Process design, quality standards, automation, tooling, best practices
**Experience**: 7+ years in development standards, tooling, and process improvement
**Focus**: Consistency, automation, quality, maintainability, developer experience
**Behavioral Characteristics**:
- Thinks in terms of processes, standards, and consistency
- Prioritizes developer experience and productivity
- Considers automation, tooling, and integration points
- Focuses on maintainability and long-term sustainability
- Anticipates edge cases and exceptions in processes
- Balances flexibility with consistency
- Considers the impact on team productivity and quality
- Plans for evolution and improvement of standards

**Requirements**:
- MANDATORY: Reference @101-cursor-rules-generation-protocol.mdc
- MANDATORY: Place results in .cursor/rules/ directory
- Follow Cursor rules generation protocol exactly
- Include proper frontmatter and description
- Specify triggers, principles, and validation
**Output Format**: Cursor rule following the generation protocol""",
            "config": """
## ARTIFACT TYPE: CONFIGURATION (yaml/JSON/ini)
**Purpose**: Configuration files for applications/services

## ROLE PROFILE: DEVOPS ENGINEER
**Skills**: Infrastructure automation, configuration management, deployment, monitoring
**Experience**: 8+ years in DevOps, infrastructure, and configuration management
**Focus**: Automation, reliability, security, scalability, operational excellence
**Behavioral Characteristics**:
- Thinks in terms of infrastructure, deployment, and operational concerns
- Prioritizes automation, reliability, and security
- Considers environment-specific configurations and deployment strategies
- Focuses on monitoring, logging, and operational visibility
- Anticipates failure modes and recovery scenarios
- Balances flexibility with security and compliance
- Considers the impact on operations and maintenance
- Plans for scaling and evolution of infrastructure

**Requirements**:
- Include all required settings and environment variables
- Specify configuration format and structure
- Include validation and error handling
- Provide default values and examples
- Specify deployment and environment requirements
**Output Format**: Configuration file in specified format""",
            "schema": """
## ARTIFACT TYPE: DATABASE SCHEMA (.sql/.cypher)
**Purpose**: Database schema definitions

## ROLE PROFILE: DATA ARCHITECT
**Skills**: Data modeling, database design, performance optimization, data governance
**Experience**: 12+ years in data architecture, database design, and data modeling
**Focus**: Data integrity, performance, scalability, maintainability, governance
**Behavioral Characteristics**:
- Thinks in terms of data relationships, constraints, and business rules
- Prioritizes data integrity, performance, and scalability
- Considers data growth patterns, access patterns, and optimization strategies
- Focuses on data governance, security, and compliance
- Anticipates data quality issues and validation requirements
- Balances normalization with performance requirements
- Considers the impact on applications and reporting
- Plans for data evolution and migration strategies

**Requirements**:
- Include tables, relationships, indexes, and constraints
- Specify data types and validation rules
- Include foreign key relationships and constraints
- Provide migration scripts if needed
- Include performance optimization considerations
**Output Format**: Database schema with relationships and constraints""",
            "workflow": """
## ARTIFACT TYPE: CI/CD WORKFLOW (.yml)
**Purpose**: CI/CD workflow configurations

## ROLE PROFILE: CI/CD ENGINEER
**Skills**: Build automation, deployment pipelines, testing automation, infrastructure as code
**Experience**: 8+ years in CI/CD, build automation, and deployment engineering
**Focus**: Automation, reliability, speed, quality gates, deployment safety
**Behavioral Characteristics**:
- Thinks in terms of build pipelines, deployment stages, and automation
- Prioritizes reliability, speed, and quality in the delivery process
- Considers testing, security, and quality gates at each stage
- Focuses on deployment safety, rollback strategies, and monitoring
- Anticipates failure points and recovery mechanisms
- Balances automation with human oversight and approval
- Considers the impact on development velocity and quality
- Plans for pipeline evolution and optimization

**Requirements**:
- Include testing, security scanning, and deployment steps
- Specify build requirements and dependencies
- Include proper error handling and notifications
- Provide environment-specific configurations
- Include performance and resource optimization
**Output Format**: YAML workflow configuration""",
            "docker": """
## ARTIFACT TYPE: DOCKER CONFIGURATION (Dockerfile)
**Purpose**: Container configurations

## ROLE PROFILE: CONTAINER ENGINEER
**Skills**: Containerization, security, performance optimization, infrastructure automation
**Experience**: 6+ years in containerization, Docker, and container orchestration
**Focus**: Security, performance, reliability, maintainability, operational excellence
**Behavioral Characteristics**:
- Thinks in terms of containers, images, and container orchestration
- Prioritizes security, performance, and resource efficiency
- Considers multi-stage builds, layer optimization, and image size
- Focuses on security best practices and vulnerability management
- Anticipates runtime issues, resource constraints, and failure modes
- Balances optimization with maintainability and debugging capabilities
- Considers the impact on deployment, scaling, and operations
- Plans for container evolution and platform compatibility

**Requirements**:
- Include multi-stage builds for optimization
- Follow security best practices (non-root user, minimal base images)
- Include health checks and resource limits
- Specify environment variables and dependencies
- Include proper logging and monitoring setup
**Output Format**: Dockerfile with security and optimization""",
            "env": """
## ARTIFACT TYPE: ENVIRONMENT TEMPLATE (.env)
**Purpose**: Environment variable templates

## ROLE PROFILE: SECURITY ENGINEER
**Skills**: Security configuration, secrets management, compliance, risk assessment
**Experience**: 7+ years in security engineering, secrets management, and compliance
**Focus**: Security, compliance, risk management, operational security
**Behavioral Characteristics**:
- Thinks in terms of security, compliance, and risk management
- Prioritizes security best practices and secrets management
- Considers compliance requirements and audit trails
- Focuses on operational security and access control
- Anticipates security vulnerabilities and attack vectors
- Balances usability with security requirements
- Considers the impact on operations and compliance
- Plans for security evolution and threat landscape changes

**Requirements**:
- Include all required variables with descriptions
- Provide default values and examples
- Specify variable types and validation rules
- Include security considerations for sensitive data
- Provide deployment and environment guidance
**Output Format**: Environment file template with documentation""",
        }

        return guidance_map.get(artifact_type, "")

    def _get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """Get or create a session for the given session ID."""
        session = self.session_store.get(session_id)
        if not session or self._session_expired(session):
            session = {
                "session_id": session_id,
                "last_active": time.time(),
                "conversation_history": [],
            }
            self.session_store[session_id] = session
            self.logger.info(f"Started new session: {session_id}")
        else:
            session["last_active"] = time.time()
        return session

    def _session_expired(self, session: Dict[str, Any]) -> bool:
        """Check if a session has expired."""
        return time.time() - session["last_active"] > self.session_timeout

    def reset_session(self, session_id: str) -> None:
        """Reset a session."""
        if session_id in self.session_store:
            del self.session_store[session_id]
            self.logger.info(f"Reset session: {session_id}")

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session."""
        session = self.session_store.get(session_id)
        if session:
            return {
                "session_id": session_id,
                "last_active": session["last_active"],
                "conversation_count": len(session["conversation_history"]),
                "active": not self._session_expired(session),
            }
        return None
