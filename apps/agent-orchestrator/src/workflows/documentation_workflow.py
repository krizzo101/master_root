#!/usr/bin/env python3
"""
Documentation Workflow System for Agent Orchestrator

Provides standardized documentation generation workflow with specialized agents.
Supports system-documentation task type with automatic agent orchestration.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..generic_orchestrator import AgentTask, GenericOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class DocumentationConfig:
    """Configuration for documentation generation workflow"""

    app_name: str
    app_root: Path
    output_dir: Path
    include_api_docs: bool = True
    include_architecture: bool = True
    include_deployment: bool = True
    include_user_guide: bool = True
    include_developer_guide: bool = True
    detail_level: str = "comprehensive"  # minimal, standard, comprehensive

    # Optional customizations
    custom_sections: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    include_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "app_name": self.app_name,
            "app_root": str(self.app_root),
            "output_dir": str(self.output_dir),
            "include_api_docs": self.include_api_docs,
            "include_architecture": self.include_architecture,
            "include_deployment": self.include_deployment,
            "include_user_guide": self.include_user_guide,
            "include_developer_guide": self.include_developer_guide,
            "detail_level": self.detail_level,
            "custom_sections": self.custom_sections,
            "exclude_patterns": self.exclude_patterns,
            "include_patterns": self.include_patterns,
        }


class DocumentationWorkflow:
    """
    Orchestrates documentation generation using specialized agents
    """

    def __init__(self, orchestrator: GenericOrchestrator):
        self.orchestrator = orchestrator
        self.specialized_agents = {
            "technical-writer": self._create_technical_writer_agent,
            "api-documenter": self._create_api_documenter_agent,
            "architecture-analyst": self._create_architecture_analyst_agent,
            "user-guide-writer": self._create_user_guide_writer_agent,
            "deployment-specialist": self._create_deployment_specialist_agent,
            "code-analyzer": self._create_code_analyzer_agent,
            "integration-validator": self._create_integration_validator_agent,
        }

    def _create_technical_writer_agent(
        self, config: DocumentationConfig, context: Dict[str, Any]
    ) -> AgentTask:
        """Create README.md and main documentation overview"""

        prompt = f"""You are a technical writing specialist tasked with creating comprehensive README.md documentation for {config.app_name}.

TASK: Create a professional, well-structured README.md file that serves as the primary entry point for users and developers.

APP DETAILS:
- Name: {config.app_name}
- Root Directory: {config.app_root}
- Detail Level: {config.detail_level}

REQUIREMENTS:
1. **Project Overview**: Clear description of what the application does
2. **Quick Start**: Essential setup and usage instructions
3. **Installation**: Step-by-step installation guide
4. **Basic Usage**: Common use cases with examples
5. **Key Features**: Highlight main capabilities
6. **Directory Structure**: Overview of main directories/files
7. **Contributing**: Guidelines for contributors
8. **License**: License information if available

CONTEXT FROM ANALYSIS:
{json.dumps(context, indent=2)}

FORMATTING GUIDELINES:
- Use clear, professional markdown formatting
- Include code examples where appropriate
- Add badges if relevant (build status, version, etc.)
- Use tables for structured information
- Include links to detailed documentation sections

OUTPUT: Save the complete README.md file to {config.output_dir}/README.md

Focus on making this accessible to both new users and experienced developers."""

        return AgentTask(
            task_id="readme_writer",
            task_type="technical-writer",
            prompt=prompt,
            context={"config": config.to_dict(), "analysis": context},
            dependencies=["code_analyzer"],
            work_dir_name=f"docs_{config.app_name}",
        )

    def _create_api_documenter_agent(
        self, config: DocumentationConfig, context: Dict[str, Any]
    ) -> AgentTask:
        """Create API reference documentation"""

        prompt = f"""You are an API documentation specialist creating comprehensive API reference documentation for {config.app_name}.

TASK: Generate complete API reference documentation covering all public APIs, endpoints, functions, and classes.

APP DETAILS:
- Name: {config.app_name}
- Root Directory: {config.app_root}
- Detail Level: {config.detail_level}

ANALYSIS CONTEXT:
{json.dumps(context, indent=2)}

REQUIREMENTS:
1. **API Overview**: High-level API architecture and design patterns
2. **Authentication**: API authentication methods if applicable
3. **Endpoints/Functions**: Complete documentation of:
   - HTTP endpoints (if web API)
   - Python functions/classes (if library)
   - CLI commands (if command-line tool)
4. **Request/Response Schemas**: Data structures and formats
5. **Error Handling**: Error codes, exceptions, and handling strategies
6. **Rate Limits**: Usage limits and throttling information
7. **Examples**: Practical usage examples for each API
8. **SDKs/Client Libraries**: Available client implementations

DOCUMENTATION FORMAT:
- Use clear section hierarchies
- Include code examples in multiple languages where applicable
- Document all parameters, return values, and exceptions
- Add response/request examples
- Use tables for structured parameter documentation

OUTPUT: Save complete API documentation to {config.output_dir}/API_REFERENCE.md

Ensure documentation is developer-friendly with practical examples."""

        return AgentTask(
            task_id="api_documenter",
            task_type="api-documenter",
            prompt=prompt,
            context={"config": config.to_dict(), "analysis": context},
            dependencies=["code_analyzer"],
            work_dir_name=f"docs_{config.app_name}",
        )

    def _create_architecture_analyst_agent(
        self, config: DocumentationConfig, context: Dict[str, Any]
    ) -> AgentTask:
        """Create system architecture documentation"""

        prompt = f"""You are a system architecture analyst creating comprehensive architecture documentation for {config.app_name}.

TASK: Document the complete system architecture, design patterns, and technical decisions.

APP DETAILS:
- Name: {config.app_name}
- Root Directory: {config.app_root}
- Detail Level: {config.detail_level}

ANALYSIS CONTEXT:
{json.dumps(context, indent=2)}

REQUIREMENTS:
1. **System Overview**: High-level architecture diagram and description
2. **Component Architecture**: Major components and their responsibilities
3. **Data Flow**: How data moves through the system
4. **Design Patterns**: Key design patterns and architectural decisions
5. **Technology Stack**: Technologies, frameworks, and dependencies used
6. **Database Design**: Schema and data relationships (if applicable)
7. **Security Architecture**: Security measures and considerations
8. **Scalability**: Performance considerations and scaling strategies
9. **Integration Points**: External services and APIs
10. **Decision Records**: Key architectural decisions and rationale

DOCUMENTATION STYLE:
- Include diagrams using mermaid syntax where helpful
- Use clear technical language
- Explain the "why" behind architectural decisions
- Document trade-offs and alternatives considered
- Include performance and scalability considerations

OUTPUT: Save architecture documentation to {config.output_dir}/ARCHITECTURE.md

Focus on helping developers understand the system design and make informed changes."""

        return AgentTask(
            task_id="architecture_analyst",
            task_type="architecture-analyst",
            prompt=prompt,
            context={"config": config.to_dict(), "analysis": context},
            dependencies=["code_analyzer"],
            work_dir_name=f"docs_{config.app_name}",
        )

    def _create_user_guide_writer_agent(
        self, config: DocumentationConfig, context: Dict[str, Any]
    ) -> AgentTask:
        """Create comprehensive user guide"""

        prompt = f"""You are a user guide specialist creating comprehensive end-user documentation for {config.app_name}.

TASK: Create user-friendly documentation that helps end users effectively use the application.

APP DETAILS:
- Name: {config.app_name}
- Root Directory: {config.app_root}
- Detail Level: {config.detail_level}

ANALYSIS CONTEXT:
{json.dumps(context, indent=2)}

REQUIREMENTS:
1. **Getting Started**: Step-by-step guide for new users
2. **Core Features**: Detailed walkthrough of main features
3. **Common Tasks**: How to accomplish typical use cases
4. **Configuration**: Settings and customization options
5. **Troubleshooting**: Common issues and solutions
6. **Best Practices**: Recommended usage patterns
7. **FAQ**: Frequently asked questions
8. **Advanced Usage**: Power user features and tips

WRITING STYLE:
- Use clear, non-technical language when possible
- Include screenshots or examples where helpful
- Structure content with clear headings and navigation
- Provide step-by-step instructions
- Focus on user goals and outcomes
- Include warnings and tips where appropriate

OUTPUT: Save user guide to {config.output_dir}/USER_GUIDE.md

Prioritize clarity and usability over technical completeness."""

        return AgentTask(
            task_id="user_guide_writer",
            task_type="user-guide-writer",
            prompt=prompt,
            context={"config": config.to_dict(), "analysis": context},
            dependencies=["code_analyzer"],
            work_dir_name=f"docs_{config.app_name}",
        )

    def _create_deployment_specialist_agent(
        self, config: DocumentationConfig, context: Dict[str, Any]
    ) -> AgentTask:
        """Create deployment and operations documentation"""

        prompt = f"""You are a deployment specialist creating comprehensive deployment and operations documentation for {config.app_name}.

TASK: Document deployment procedures, operational considerations, and maintenance tasks.

APP DETAILS:
- Name: {config.app_name}
- Root Directory: {config.app_root}
- Detail Level: {config.detail_level}

ANALYSIS CONTEXT:
{json.dumps(context, indent=2)}

REQUIREMENTS:
1. **Deployment Methods**: All supported deployment approaches
   - Local development setup
   - Docker containerization
   - Cloud platform deployment
   - CI/CD pipeline integration
2. **Environment Configuration**:
   - Environment variables
   - Configuration files
   - Secrets management
3. **Dependencies**: System requirements and dependencies
4. **Database Setup**: Database installation and migration procedures
5. **Monitoring**: Health checks, logging, and monitoring setup
6. **Backup & Recovery**: Data backup and disaster recovery procedures
7. **Scaling**: Horizontal and vertical scaling considerations
8. **Security**: Security configuration and hardening
9. **Maintenance**: Regular maintenance tasks and updates
10. **Troubleshooting**: Common deployment issues and solutions

DOCUMENTATION FOCUS:
- Provide concrete, executable instructions
- Include example configuration files
- Document environment-specific considerations
- Add checklists for deployment verification
- Include rollback procedures
- Address common deployment failures

OUTPUT: Save deployment documentation to {config.output_dir}/DEPLOYMENT.md

Ensure operations teams can successfully deploy and maintain the system."""

        return AgentTask(
            task_id="deployment_specialist",
            task_type="deployment-specialist",
            prompt=prompt,
            context={"config": config.to_dict(), "analysis": context},
            dependencies=["architecture_analyst"],
            work_dir_name=f"docs_{config.app_name}",
        )

    def _create_code_analyzer_agent(
        self, config: DocumentationConfig, context: Dict[str, Any]
    ) -> AgentTask:
        """Analyze codebase to gather information for other agents"""

        prompt = f"""You are a code analysis specialist tasked with comprehensively analyzing {config.app_name} to provide context for documentation generation.

TASK: Perform deep codebase analysis to extract key information needed for documentation.

APP DETAILS:
- Name: {config.app_name}
- Root Directory: {config.app_root}
- Detail Level: {config.detail_level}

ANALYSIS REQUIREMENTS:
1. **Project Structure**:
   - Directory layout and organization
   - Key files and their purposes
   - Configuration files
   - Documentation that already exists

2. **Technology Stack**:
   - Programming languages used
   - Frameworks and libraries
   - Build systems and tools
   - Database technologies

3. **Code Architecture**:
   - Main modules/packages
   - Key classes and functions
   - Design patterns in use
   - Entry points and main workflows

4. **API Surface**:
   - Public APIs, endpoints, or interfaces
   - CLI commands and options
   - Configuration options
   - Data models/schemas

5. **Dependencies & Requirements**:
   - External dependencies
   - System requirements
   - Development dependencies
   - Optional features

6. **Deployment Artifacts**:
   - Containerization (Dockerfile, docker-compose)
   - CI/CD configuration
   - Cloud deployment configs
   - Installation scripts

7. **Testing & Quality**:
   - Test structure and coverage
   - Code quality tools
   - Linting and formatting

OUTPUT FORMAT:
Return a comprehensive JSON analysis containing all discovered information organized by category. This will be used by other documentation agents.

Use all available tools to thoroughly examine the codebase at {config.app_root}."""

        return AgentTask(
            task_id="code_analyzer",
            task_type="code-analyzer",
            prompt=prompt,
            context={"config": config.to_dict()},
            dependencies=[],
            work_dir_name=f"docs_{config.app_name}",
        )

    def _create_integration_validator_agent(
        self, config: DocumentationConfig, context: Dict[str, Any]
    ) -> AgentTask:
        """Validate and integrate all generated documentation"""

        prompt = f"""You are a documentation integration specialist responsible for validating and finalizing the complete documentation suite for {config.app_name}.

TASK: Review, validate, and create a cohesive documentation suite from all generated documents.

APP DETAILS:
- Name: {config.app_name}
- Documentation Directory: {config.output_dir}

INTEGRATION REQUIREMENTS:
1. **Validation**:
   - Verify all required documents were created
   - Check for consistency across documents
   - Validate internal links and references
   - Ensure no duplicate or conflicting information

2. **Cross-References**:
   - Add proper cross-references between documents
   - Create navigation links
   - Ensure consistent terminology

3. **Documentation Index**:
   - Create comprehensive index/table of contents
   - Add document summaries
   - Create quick reference guide

4. **Quality Checks**:
   - Check markdown formatting
   - Verify code examples work
   - Ensure professional presentation
   - Validate completeness against requirements

5. **Integration**:
   - Create DEVELOPER_GUIDE.md that ties everything together
   - Add navigation between documents
   - Ensure logical flow for readers

FINAL DELIVERABLES:
- Validate all core documents exist and are complete
- Create DEVELOPER_GUIDE.md as integration guide
- Generate documentation index
- Create any missing critical sections
- Ensure professional, cohesive documentation suite

OUTPUT: Save integration report and any additional documents to {config.output_dir}/

Focus on creating a professional, complete documentation experience."""

        return AgentTask(
            task_id="integration_validator",
            task_type="integration-validator",
            prompt=prompt,
            context={"config": config.to_dict()},
            dependencies=[
                "readme_writer",
                "api_documenter",
                "architecture_analyst",
                "user_guide_writer",
                "deployment_specialist",
            ],
            work_dir_name=f"docs_{config.app_name}",
        )

    def create_documentation_tasks(
        self, config: DocumentationConfig
    ) -> List[AgentTask]:
        """Create all documentation tasks based on configuration"""

        tasks = []
        context = {}  # Will be populated by code analyzer

        # Always include code analyzer as foundation
        tasks.append(self._create_code_analyzer_agent(config, context))

        # Add requested documentation types
        if config.include_api_docs:
            tasks.append(self._create_api_documenter_agent(config, context))

        if config.include_architecture:
            tasks.append(self._create_architecture_analyst_agent(config, context))

        if config.include_user_guide:
            tasks.append(self._create_user_guide_writer_agent(config, context))

        if config.include_developer_guide or config.include_deployment:
            tasks.append(self._create_deployment_specialist_agent(config, context))

        # Always include README and technical writer
        tasks.append(self._create_technical_writer_agent(config, context))

        # Always include integration validator as final step
        tasks.append(self._create_integration_validator_agent(config, context))

        return tasks

    async def execute_documentation_workflow(
        self, config: DocumentationConfig
    ) -> Dict[str, Any]:
        """Execute complete documentation workflow"""

        logger.info(f"Starting documentation workflow for {config.app_name}")

        # Ensure output directory exists
        config.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate tasks
        tasks = self.create_documentation_tasks(config)

        # Set up orchestrator hooks for documentation workflow
        self.orchestrator.pre_execute_hook = self._pre_execute_hook
        self.orchestrator.post_execute_hook = self._post_execute_hook

        # Execute tasks
        results = await self.orchestrator.execute_batch(tasks)

        # Create execution summary
        summary = {
            "workflow": "system-documentation",
            "app_name": config.app_name,
            "output_dir": str(config.output_dir),
            "tasks_executed": len(results),
            "tasks_completed": len([r for r in results if r["status"] == "completed"]),
            "tasks_failed": len([r for r in results if r["status"] == "failed"]),
            "documentation_files": list(config.output_dir.glob("*.md")),
            "timestamp": datetime.now().isoformat(),
        }

        # Save workflow summary
        summary_file = config.output_dir / "documentation_workflow_summary.json"
        summary_file.write_text(json.dumps(summary, indent=2, default=str))

        logger.info(
            f"Documentation workflow completed: {summary['tasks_completed']}/{summary['tasks_executed']} tasks successful"
        )

        return summary

    async def _pre_execute_hook(self, task: AgentTask):
        """Pre-execution hook for documentation tasks"""
        logger.info(f"Starting documentation task: {task.task_id} ({task.task_type})")

    async def _post_execute_hook(self, task: AgentTask):
        """Post-execution hook for documentation tasks"""
        if task.status == "completed":
            logger.info(f"Completed documentation task: {task.task_id}")
        else:
            logger.warning(f"Failed documentation task: {task.task_id} - {task.error}")


def create_system_documentation_task(
    app_name: str, app_root: str, output_dir: str = None, **kwargs
) -> Dict[str, Any]:
    """
    Factory function to create system-documentation task configuration

    Args:
        app_name: Name of the application
        app_root: Root directory of the application
        output_dir: Output directory for documentation (default: {app_root}/docs)
        **kwargs: Additional configuration options

    Returns:
        Task configuration dictionary
    """

    app_root_path = Path(app_root)
    if output_dir is None:
        output_dir = app_root_path / "docs"
    else:
        output_dir = Path(output_dir)

    config = DocumentationConfig(
        app_name=app_name, app_root=app_root_path, output_dir=output_dir, **kwargs
    )

    return {
        "task_type": "system-documentation",
        "app_name": app_name,
        "app_root": str(app_root_path),
        "output_dir": str(output_dir),
        "config": config.to_dict(),
    }
