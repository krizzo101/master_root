"""
AI-Powered Documentation Generation Module

Creates comprehensive, intelligent documentation based on code analysis and requirements.
Uses OpenAI to understand project structure and generate meaningful documentation.
"""

from __future__ import annotations

import ast
import logging
from typing import Any

from local_shared.openai_interfaces.responses_interface import get_openai_interface

# Model selector imported locally where needed
from project_templates import ProjectType
from pydantic import BaseModel, Field

from config import get_config
from schemas import ArchitectureSpec, RequirementsSpec

logger = logging.getLogger(__name__)


class DocumentationSection(BaseModel):
    """Represents a single documentation section."""

    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content in markdown")
    order: int = Field(..., description="Display order")


class APIEndpoint(BaseModel):
    """API endpoint documentation."""

    path: str = Field(..., description="Endpoint path")
    method: str = Field(..., description="HTTP method")
    description: str = Field(..., description="Endpoint description")
    parameters: str | None = Field(None, description="Parameters description")
    response: str | None = Field(None, description="Response description")


class APISchema(BaseModel):
    """API schema documentation."""

    name: str = Field(..., description="Schema name")
    description: str = Field(..., description="Schema description")
    properties: str | None = Field(None, description="Schema properties")


class APIExample(BaseModel):
    """API usage example."""

    title: str = Field(..., description="Example title")
    description: str = Field(..., description="Example description")
    code: str = Field(..., description="Example code")


class APIDocumentation(BaseModel):
    """API-specific documentation."""

    endpoints: list[APIEndpoint] = Field(
        default=[], description="API endpoint documentation"
    )
    schemas: list[APISchema] = Field(
        default=[], description="Data schema documentation"
    )
    examples: list[APIExample] = Field(default=[], description="Usage examples")


class DocumentationPackage(BaseModel):
    """Complete documentation package."""

    readme: str = Field(..., description="Main README.md content")
    api_docs: APIDocumentation | None = Field(None, description="API documentation")
    user_guide: str = Field(..., description="User guide content")
    developer_guide: str = Field(..., description="Developer/contributor guide")
    troubleshooting: str = Field(..., description="Common issues and solutions")
    changelog: str = Field(..., description="Version history and changes")
    additional_sections: list[DocumentationSection] = Field(
        default=[], description="Additional documentation sections"
    )


class AIDocumentationGenerator:
    """AI-powered documentation generator that analyzes code and creates comprehensive docs."""

    def __init__(self):
        self.interface = get_openai_interface()
        self.config = get_config()

    def generate_documentation(
        self,
        generated_files: list[dict[str, str]],
        test_files: list[dict[str, str]],
        requirements: RequirementsSpec,
        architecture: ArchitectureSpec,
        project_type: ProjectType,
        insights: str = "",
    ) -> DocumentationPackage:
        """
        Generate comprehensive documentation based on generated code and requirements.

        Args:
            generated_files: Main application files
            test_files: Generated test files
            requirements: Original requirements specification
            architecture: Architecture specification
            project_type: Type of project

        Returns:
            Complete documentation package
        """
        logger.info(
            f"Generating AI-powered documentation for {project_type.value} project"
        )

        # Analyze code structure for documentation
        code_analysis = self._analyze_code_for_docs(generated_files)

        # Select optimal model for documentation generation
        from local_shared.openai_interfaces.model_selector import ModelSelector

        model_selector = ModelSelector()
        model = model_selector.select_optimal_model(
            task_type="execution",
            require_structured_outputs=True,
            prefer_cost_effective=True,  # Documentation can use cost-effective model
        )

        # Create comprehensive prompt for documentation generation
        system_prompt = self._build_docs_system_prompt(project_type)
        user_prompt = self._build_docs_user_prompt(
            generated_files,
            test_files,
            code_analysis,
            requirements,
            architecture,
            project_type,
        )

        try:
            docs_package = self.interface.create_structured_response(
                prompt=user_prompt,
                response_model=DocumentationPackage,
                model=model,
                system_prompt=system_prompt,
            )

            logger.info(
                f"Generated documentation package with README, user guide, developer guide, "
                f"and {len(docs_package.additional_sections)} additional sections"
            )

            return docs_package

        except Exception as e:
            logger.error(f"AI documentation generation failed: {e}")
            # Fallback to basic documentation generation
            return self._fallback_documentation_generation(
                generated_files, requirements, architecture, project_type
            )

    def _analyze_code_for_docs(
        self, generated_files: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Analyze code structure for documentation purposes."""

        analysis = {
            "public_functions": [],
            "public_classes": [],
            "api_endpoints": [],
            "cli_commands": [],
            "configuration_options": [],
            "main_modules": [],
            "dependencies": [],
            "entry_points": [],
        }

        for file_info in generated_files:
            filename = file_info["filename"]
            content = file_info["content"]

            try:
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Only document public functions (not starting with _)
                        if not node.name.startswith("_"):
                            func_info = {
                                "name": node.name,
                                "file": filename,
                                "docstring": ast.get_docstring(node),
                                "args": [arg.arg for arg in node.args.args],
                                "decorators": [
                                    self._get_decorator_name(d)
                                    for d in node.decorator_list
                                ],
                                "is_async": isinstance(node, ast.AsyncFunctionDef),
                            }
                            analysis["public_functions"].append(func_info)

                            # Check for API endpoints
                            for decorator in node.decorator_list:
                                decorator_name = self._get_decorator_name(decorator)
                                if any(
                                    method in decorator_name.lower()
                                    for method in [
                                        "get",
                                        "post",
                                        "put",
                                        "delete",
                                        "patch",
                                    ]
                                ):
                                    analysis["api_endpoints"].append(func_info)

                    elif isinstance(node, ast.ClassDef):
                        # Only document public classes
                        if not node.name.startswith("_"):
                            class_info = {
                                "name": node.name,
                                "file": filename,
                                "docstring": ast.get_docstring(node),
                                "methods": [
                                    n.name
                                    for n in node.body
                                    if isinstance(n, ast.FunctionDef)
                                    and not n.name.startswith("_")
                                ],
                                "bases": [
                                    self._get_base_name(base) for base in node.bases
                                ],
                            }
                            analysis["public_classes"].append(class_info)

                    elif isinstance(node, ast.Import) or isinstance(
                        node, ast.ImportFrom
                    ):
                        # Track external dependencies
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                if not alias.name.startswith(
                                    "."
                                ):  # Not relative import
                                    analysis["dependencies"].append(
                                        alias.name.split(".")[0]
                                    )
                        else:
                            if node.module and not node.module.startswith("."):
                                analysis["dependencies"].append(
                                    node.module.split(".")[0]
                                )

                # Check for main entry point
                if 'if __name__ == "__main__"' in content:
                    analysis["entry_points"].append(filename)

                # Check for configuration patterns
                if any(
                    word in content.lower()
                    for word in ["config", "settings", "environment"]
                ):
                    analysis["main_modules"].append(filename)

            except SyntaxError as e:
                logger.warning(f"Could not parse {filename} for documentation: {e}")
                continue

        # Remove duplicates and clean up
        analysis["dependencies"] = list(set(analysis["dependencies"]))

        return analysis

    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_decorator_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        else:
            return str(decorator)

    def _get_base_name(self, base) -> str:
        """Extract base class name from AST node."""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{self._get_base_name(base.value)}.{base.attr}"
        else:
            return str(base)

    def _build_docs_system_prompt(self, project_type: ProjectType) -> str:
        """Build system prompt for documentation generation."""

        base_prompt = """You are an expert technical writer and documentation specialist. Generate comprehensive, professional documentation based on code analysis and project requirements.

CRITICAL DOCUMENTATION REQUIREMENTS:
- Generate COMPLETE, PROFESSIONAL documentation - not snippets or placeholders
- Include clear installation and setup instructions
- Provide comprehensive usage examples with code samples
- Document all public APIs, functions, and classes
- Include troubleshooting and common issues sections
- Follow markdown best practices and formatting
- Include proper code blocks with syntax highlighting
- Generate realistic examples and use cases
- Include configuration and customization options

DOCUMENTATION QUALITY STANDARDS:
- All sections must be well-structured and easy to navigate
- Include clear headings and subheadings
- Provide step-by-step instructions where appropriate
- Include code examples for all major features
- Add links between related sections
- Include badges, shields, and visual elements where helpful
- Write for both technical and non-technical audiences
- Include security considerations where applicable
- Add performance tips and best practices"""

        project_specific = {
            ProjectType.WEB_API: """
API DOCUMENTATION SPECIFIC REQUIREMENTS:
- Document all API endpoints with HTTP methods, parameters, and responses
- Include authentication and authorization documentation
- Provide OpenAPI/Swagger specification references
- Add request/response examples for each endpoint
- Include rate limiting and error handling documentation
- Document data models and schemas
- Add API versioning information
- Include SDK and client library information
- Provide testing and development environment setup""",
            ProjectType.CLI_TOOL: """
CLI DOCUMENTATION SPECIFIC REQUIREMENTS:
- Document all command-line options and arguments
- Include usage examples for common scenarios
- Provide configuration file documentation
- Add shell completion setup instructions
- Document environment variables and settings
- Include troubleshooting for common CLI issues
- Provide installation instructions for different platforms
- Add examples of scripting and automation usage""",
            ProjectType.WEB_APP: """
WEB APP DOCUMENTATION SPECIFIC REQUIREMENTS:
- Document deployment and hosting options
- Include environment setup and configuration
- Provide user interface and feature documentation
- Add database setup and migration instructions
- Document authentication and user management
- Include security configuration and best practices
- Provide performance optimization guidelines
- Add monitoring and logging setup instructions""",
            ProjectType.DATA_PROCESSOR: """
DATA PROCESSING DOCUMENTATION SPECIFIC REQUIREMENTS:
- Document supported data formats and sources
- Include data pipeline and workflow documentation
- Provide performance benchmarks and optimization tips
- Add data validation and quality control information
- Document output formats and destinations
- Include error handling and recovery procedures
- Provide scaling and distributed processing guidance
- Add data privacy and security considerations""",
            ProjectType.SIMPLE_SCRIPT: """
SCRIPT DOCUMENTATION SPECIFIC REQUIREMENTS:
- Document script purpose and use cases
- Include simple installation and execution instructions
- Provide configuration and customization options
- Add examples of different usage scenarios
- Document dependencies and requirements
- Include troubleshooting for common issues
- Provide extension and modification guidelines""",
        }

        return base_prompt + "\n\n" + project_specific.get(project_type, "")

    def _build_docs_user_prompt(
        self,
        generated_files: list[dict[str, str]],
        test_files: list[dict[str, str]],
        code_analysis: dict[str, Any],
        requirements: RequirementsSpec,
        architecture: ArchitectureSpec,
        project_type: ProjectType,
    ) -> str:
        """Build user prompt with code analysis and requirements for documentation."""

        # Prepare documentation summaries
        functions_summary = "\n".join(
            f"- {func['name']}() in {func['file']}"
            + (
                f": {func['docstring'][:100]}..."
                if func["docstring"]
                else " (no docstring)"
            )
            for func in code_analysis["public_functions"][:10]  # Limit for prompt size
        )

        classes_summary = "\n".join(
            f"- {cls['name']} in {cls['file']}"
            + (
                f": {cls['docstring'][:100]}..."
                if cls["docstring"]
                else " (no docstring)"
            )
            for cls in code_analysis["public_classes"][:10]
        )

        api_endpoints_summary = "\n".join(
            f"- {endpoint['name']}() in {endpoint['file']}"
            for endpoint in code_analysis["api_endpoints"][:10]
        )

        dependencies_summary = ", ".join(code_analysis["dependencies"][:15])

        prompt = f"""Generate comprehensive documentation for this {project_type.value.replace('_', ' ')} project:

PROJECT OVERVIEW:
- Title: {requirements.title}
- Description: {requirements.description}
- Original Request: {requirements.original_request}

FUNCTIONAL REQUIREMENTS:
{chr(10).join(f"- {req}" for req in requirements.functional_requirements)}

NON-FUNCTIONAL REQUIREMENTS:
{chr(10).join(f"- {req}" for req in requirements.non_functional_requirements)}

ARCHITECTURE OVERVIEW:
Technology Stack: {', '.join(architecture.technology_stack)}
Deployment Strategy: {architecture.deployment_strategy}

Components:
{chr(10).join(f"- {comp.name}: {comp.responsibility}" for comp in architecture.components)}

CODE STRUCTURE TO DOCUMENT:
Public Functions:
{functions_summary or "- No public functions detected"}

Public Classes:
{classes_summary or "- No public classes detected"}

API Endpoints:
{api_endpoints_summary or "- No API endpoints detected"}

Main Dependencies: {dependencies_summary or "Standard library only"}

Entry Points: {', '.join(code_analysis['entry_points']) or 'None detected'}

GENERATED FILES:
{chr(10).join(f"- {file_info['filename']}" for file_info in generated_files)}

Generate comprehensive documentation that includes:
1. Professional README with clear project description and quick start
2. Detailed user guide with examples and common use cases
3. Developer guide for contributors and advanced users
4. API documentation (if applicable) with endpoint details
5. Troubleshooting guide with common issues and solutions
6. Changelog template for version tracking

Make the documentation professional, comprehensive, and user-friendly for both technical and non-technical audiences."""

        return prompt

    def _fallback_documentation_generation(
        self,
        generated_files: list[dict[str, str]],
        requirements: RequirementsSpec,
        architecture: ArchitectureSpec,
        project_type: ProjectType,
    ) -> DocumentationPackage:
        """Fallback documentation generation when AI fails."""

        logger.warning("Using fallback documentation generation")

        readme_content = f"""# {requirements.title}

{requirements.description}

## Overview
This project was generated based on the following request:
> {requirements.original_request}

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Quick Start
1. Follow the installation instructions above
2. Run the main application
3. See the user guide for detailed usage instructions

## Project Structure

```
src/
├── {', '.join([f['filename'] for f in generated_files[:5]])}
...
tests/
└── test files...
```

## Requirements

### Functional Requirements
{chr(10).join(f"- {req}" for req in requirements.functional_requirements)}

### Non-Functional Requirements
{chr(10).join(f"- {req}" for req in requirements.non_functional_requirements)}

## Architecture

### Technology Stack
{chr(10).join(f"- {tech}" for tech in architecture.technology_stack)}

### Components
{chr(10).join(f"- **{comp.name}**: {comp.responsibility}" for comp in architecture.components)}

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
"""

        user_guide_content = f"""# User Guide - {requirements.title}

## Getting Started

This guide will help you get started with {requirements.title}.

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Installation
```bash
pip install -r requirements.txt
```

### Basic Usage
[Usage instructions will be added based on your specific project type]

## Configuration
[Configuration options will be documented here]

## Examples
[Usage examples will be provided here]

## FAQ
[Frequently asked questions will be added here]
"""

        developer_guide_content = f"""# Developer Guide - {requirements.title}

## Development Setup

### Environment Setup
```bash
# Clone the repository
git clone [repository-url]
cd {requirements.title.lower().replace(' ', '-')}

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### Running Tests
```bash
pytest tests/ -v
```

### Code Style
This project follows PEP 8 standards with automated formatting.

## Architecture

### Project Structure
{chr(10).join(f"- `{f['filename']}`: [Purpose to be documented]" for f in generated_files)}

### Key Components
{chr(10).join(f"- **{comp.name}**: {comp.responsibility}" for comp in architecture.components)}

## Contributing

### Development Workflow
1. Create a feature branch from main
2. Make your changes
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Code Review Process
[Code review guidelines will be added here]
"""

        troubleshooting_content = f"""# Troubleshooting - {requirements.title}

## Common Issues

### Installation Issues
**Problem**: Package installation fails
**Solution**: Ensure you have Python 3.10+ and pip is up to date

### Runtime Issues
**Problem**: Application fails to start
**Solution**: Check that all dependencies are installed and environment variables are set

## Getting Help

If you encounter issues not covered here:
1. Check the GitHub issues page
2. Create a new issue with detailed information
3. Include error messages and system information

## Debugging

### Enable Debug Mode
[Instructions for enabling debug logging]

### Common Error Messages
[List of common errors and their solutions]
"""

        changelog_content = f"""# Changelog - {requirements.title}

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project generation based on AI requirements analysis
- Core functionality implementation
- Comprehensive test suite
- Documentation package

### Changed
- [Changes will be documented here]

### Deprecated
- [Deprecated features will be listed here]

### Removed
- [Removed features will be listed here]

### Fixed
- [Bug fixes will be documented here]

### Security
- [Security updates will be documented here]

## [1.0.0] - {chr(10)[:10]}  # Current date placeholder

### Added
- Initial release
- Core functionality
- Basic documentation
"""

        return DocumentationPackage(
            readme=readme_content,
            user_guide=user_guide_content,
            developer_guide=developer_guide_content,
            troubleshooting=troubleshooting_content,
            changelog=changelog_content,
            additional_sections=[],
        )


def generate_ai_documentation(
    generated_files: list[dict[str, str]],
    test_files: list[dict[str, str]],
    requirements: RequirementsSpec,
    architecture: ArchitectureSpec,
    project_type: ProjectType,
    insights: str = "",
) -> DocumentationPackage:
    """
    Main function to generate AI-powered documentation.

    Args:
        generated_files: List of generated code files
        test_files: List of generated test files
        requirements: User requirements specification
        architecture: Generated architecture specification
        project_type: Type of project

    Returns:
        Complete documentation package
    """
    generator = AIDocumentationGenerator()
    return generator.generate_documentation(
        generated_files, test_files, requirements, architecture, project_type, insights
    )
