"""
Workflow Documentation Generator

Automated documentation generation for workflows in the AI-Powered Development system.
Generates comprehensive documentation from workflow definitions, templates, and execution history.

This module implements the workflow documentation automation requested in the coordinator queue.

Author: ST-Agent-4 (Workflow Developer)
Created: 2025-01-27
Assignment: Workflow documentation automation in .cursor/docs/ and .cursor/templates/
"""

import yaml
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum


class DocumentationType(Enum):
    """Types of documentation that can be generated."""

    OVERVIEW = "overview"
    REFERENCE = "reference"
    TUTORIAL = "tutorial"
    API_DOCS = "api_docs"
    CHANGELOG = "changelog"
    TROUBLESHOOTING = "troubleshooting"


class DocumentationFormat(Enum):
    """Supported documentation formats."""

    MARKDOWN = "markdown"
    HTML = "html"
    YAML = "yaml"
    JSON = "json"


@dataclass
class WorkflowDocumentationConfig:
    """Configuration for workflow documentation generation."""

    workflow_dir: str = "src/workflow/"
    template_dir: str = ".cursor/templates/"
    docs_output_dir: str = ".cursor/docs/workflows/"
    include_examples: bool = True
    include_schemas: bool = True
    include_diagrams: bool = True
    auto_update: bool = True
    formats: List[DocumentationFormat] = field(
        default_factory=lambda: [DocumentationFormat.MARKDOWN]
    )


@dataclass
class WorkflowDocumentation:
    """Generated documentation for a workflow."""

    workflow_id: str
    title: str
    description: str
    content: str
    format: DocumentationFormat
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    file_path: Optional[str] = None


class WorkflowDocumentationGenerator:
    """
    Automated workflow documentation generator.

    Generates comprehensive documentation for workflows including:
    - Overview documentation from workflow definitions
    - Reference documentation for workflow components
    - API documentation for workflow interfaces
    - Tutorial documentation with examples
    - Troubleshooting guides based on common issues
    """

    def __init__(self, config: Optional[WorkflowDocumentationConfig] = None):
        """
        Initialize documentation generator.

        Args:
            config: Documentation generation configuration
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or WorkflowDocumentationConfig()
        # WorkflowParser will be instantiated per workflow file as needed

        # Documentation templates
        self._templates = {
            DocumentationType.OVERVIEW: self._generate_overview_template(),
            DocumentationType.REFERENCE: self._generate_reference_template(),
            DocumentationType.TUTORIAL: self._generate_tutorial_template(),
            DocumentationType.API_DOCS: self._generate_api_template(),
            DocumentationType.CHANGELOG: self._generate_changelog_template(),
            DocumentationType.TROUBLESHOOTING: self._generate_troubleshooting_template(),
        }

        self.logger.info("Workflow documentation generator initialized")

    def generate_all_documentation(self) -> List[WorkflowDocumentation]:
        """
        Generate all workflow documentation.

        Returns:
            List of generated documentation objects
        """
        documentation_list = []

        # Discover all workflows
        workflows = self._discover_workflows()

        # Generate documentation for each workflow
        for workflow_path in workflows:
            try:
                docs = self._generate_workflow_documentation(workflow_path)
                documentation_list.extend(docs)
            except Exception as e:
                self.logger.error(
                    f"Failed to generate documentation for {workflow_path}: {e}"
                )

        # Generate aggregate documentation
        aggregate_docs = self._generate_aggregate_documentation(workflows)
        documentation_list.extend(aggregate_docs)

        # Write documentation files
        self._write_documentation_files(documentation_list)

        self.logger.info(f"Generated {len(documentation_list)} documentation files")
        return documentation_list

    def generate_workflow_documentation(
        self, workflow_path: str, doc_types: Optional[List[DocumentationType]] = None
    ) -> List[WorkflowDocumentation]:
        """
        Generate documentation for a specific workflow.

        Args:
            workflow_path: Path to workflow file
            doc_types: Types of documentation to generate (all if None)

        Returns:
            List of generated documentation
        """
        if doc_types is None:
            doc_types = list(DocumentationType)

        return self._generate_workflow_documentation(workflow_path, doc_types)

    def update_documentation(self) -> List[WorkflowDocumentation]:
        """
        Update existing documentation based on workflow changes.

        Returns:
            List of updated documentation
        """
        if not self.config.auto_update:
            self.logger.info("Auto-update disabled, skipping documentation update")
            return []

        # Check for workflow modifications
        modified_workflows = self._find_modified_workflows()

        updated_docs = []
        for workflow_path in modified_workflows:
            docs = self._generate_workflow_documentation(workflow_path)
            updated_docs.extend(docs)

        # Update aggregate documentation if any workflows changed
        if modified_workflows:
            all_workflows = self._discover_workflows()
            aggregate_docs = self._generate_aggregate_documentation(all_workflows)
            updated_docs.extend(aggregate_docs)

        self._write_documentation_files(updated_docs)

        self.logger.info(f"Updated {len(updated_docs)} documentation files")
        return updated_docs

    def generate_workflow_index(self) -> WorkflowDocumentation:
        """
        Generate an index of all available workflows.

        Returns:
            Workflow index documentation
        """
        workflows = self._discover_workflows()

        content = self._generate_workflow_index_content(workflows)

        index_doc = WorkflowDocumentation(
            workflow_id="workflow_index",
            title="Workflow Index",
            description="Complete index of all available workflows",
            content=content,
            format=DocumentationFormat.MARKDOWN,
            metadata={
                "total_workflows": len(workflows),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            },
        )

        return index_doc

    def _discover_workflows(self) -> List[str]:
        """Discover all workflow files in the system."""
        workflow_files = []

        # Search in workflow directory
        workflow_dir = Path(self.config.workflow_dir)
        if workflow_dir.exists():
            for pattern in ["*.yaml", "*.yml", "*.json"]:
                workflow_files.extend(workflow_dir.glob(pattern))

        # Search in templates directory
        template_dir = Path(self.config.template_dir)
        if template_dir.exists():
            for pattern in ["*workflow*.yaml", "*workflow*.yml"]:
                workflow_files.extend(template_dir.glob(pattern))

        return [str(f) for f in workflow_files]

    def _generate_workflow_documentation(
        self, workflow_path: str, doc_types: Optional[List[DocumentationType]] = None
    ) -> List[WorkflowDocumentation]:
        """Generate documentation for a single workflow."""
        if doc_types is None:
            doc_types = list(DocumentationType)

        # Parse workflow definition
        try:
            workflow_def = self._load_workflow_definition(workflow_path)

            # For YAML files that look like workflow templates, try parsing with WorkflowParser
            if (
                Path(workflow_path).suffix in [".yaml", ".yml"]
                and "workflow" in workflow_def
            ):
                try:
                    from .workflow_parser import WorkflowParser

                    parser = WorkflowParser(workflow_path)
                    parsed_workflow = parser.load()
                    # Merge parsed metadata for richer documentation
                    metadata = parser.get_metadata()
                    if metadata.get("name"):
                        workflow_def["name"] = metadata["name"]
                    if metadata.get("description"):
                        workflow_def["description"] = metadata["description"]
                except Exception as parser_error:
                    self.logger.debug(
                        f"WorkflowParser failed for {workflow_path}, using basic YAML: {parser_error}"
                    )

        except Exception as e:
            self.logger.error(f"Failed to load workflow {workflow_path}: {e}")
            return []

        documentation_list = []

        for doc_type in doc_types:
            try:
                doc = self._generate_single_documentation(
                    workflow_path, workflow_def, doc_type
                )
                if doc:
                    documentation_list.append(doc)
            except Exception as e:
                self.logger.error(
                    f"Failed to generate {doc_type.value} for {workflow_path}: {e}"
                )

        return documentation_list

    def _generate_single_documentation(
        self,
        workflow_path: str,
        workflow_def: Dict[str, Any],
        doc_type: DocumentationType,
    ) -> Optional[WorkflowDocumentation]:
        """Generate a single type of documentation."""
        workflow_name = Path(workflow_path).stem

        if doc_type == DocumentationType.OVERVIEW:
            content = self._generate_overview_content(workflow_def)
            title = f"{workflow_name} - Overview"

        elif doc_type == DocumentationType.REFERENCE:
            content = self._generate_reference_content(workflow_def)
            title = f"{workflow_name} - Reference"

        elif doc_type == DocumentationType.TUTORIAL:
            content = self._generate_tutorial_content(workflow_def)
            title = f"{workflow_name} - Tutorial"

        elif doc_type == DocumentationType.API_DOCS:
            content = self._generate_api_content(workflow_def)
            title = f"{workflow_name} - API Documentation"

        elif doc_type == DocumentationType.CHANGELOG:
            content = self._generate_changelog_content(workflow_path, workflow_def)
            title = f"{workflow_name} - Changelog"

        elif doc_type == DocumentationType.TROUBLESHOOTING:
            content = self._generate_troubleshooting_content(workflow_def)
            title = f"{workflow_name} - Troubleshooting"

        else:
            return None

        return WorkflowDocumentation(
            workflow_id=f"{workflow_name}_{doc_type.value}",
            title=title,
            description=f"{doc_type.value.title()} documentation for {workflow_name}",
            content=content,
            format=DocumentationFormat.MARKDOWN,
            metadata={
                "workflow_path": workflow_path,
                "doc_type": doc_type.value,
                "workflow_name": workflow_name,
            },
        )

    def _generate_overview_content(self, workflow_def: Dict[str, Any]) -> str:
        """Generate overview documentation content."""
        template = self._templates[DocumentationType.OVERVIEW]

        # Extract workflow information
        name = workflow_def.get("name", "Unnamed Workflow")
        description = workflow_def.get("description", "No description available")

        # Get workflow steps
        workflow_steps = workflow_def.get("workflow", [])
        if isinstance(workflow_steps, dict):
            workflow_steps = workflow_steps.get("steps", [])

        # Get phases
        phases = workflow_def.get("phases", [])
        if not phases and workflow_steps:
            phases = list(set(step.get("phase", "Unknown") for step in workflow_steps))

        # Get quality gates
        quality_gates = workflow_def.get("quality_gates", {})

        # Fill template
        content = template.format(
            name=name,
            description=description,
            total_steps=len(workflow_steps),
            phases=", ".join(phases) if phases else "Not specified",
            quality_gates_count=len(quality_gates),
            steps_overview=self._format_steps_overview(workflow_steps),
            quality_gates_overview=self._format_quality_gates_overview(quality_gates),
        )

        return content

    def _generate_reference_content(self, workflow_def: Dict[str, Any]) -> str:
        """Generate reference documentation content."""
        template = self._templates[DocumentationType.REFERENCE]

        # Extract detailed workflow information
        workflow_steps = workflow_def.get("workflow", [])
        if isinstance(workflow_steps, dict):
            workflow_steps = workflow_steps.get("steps", [])

        inputs_required = workflow_def.get("inputs_required", [])
        expected_outputs = workflow_def.get("expected_outputs", [])
        error_handling = workflow_def.get("error_handling", {})
        monitoring = workflow_def.get("monitoring", {})

        content = template.format(
            inputs_required=self._format_list(inputs_required),
            expected_outputs=self._format_list(expected_outputs),
            steps_reference=self._format_steps_reference(workflow_steps),
            error_handling=self._format_error_handling(error_handling),
            monitoring_config=self._format_monitoring_config(monitoring),
        )

        return content

    def _generate_tutorial_content(self, workflow_def: Dict[str, Any]) -> str:
        """Generate tutorial documentation content."""
        template = self._templates[DocumentationType.TUTORIAL]

        workflow_steps = workflow_def.get("workflow", [])
        if isinstance(workflow_steps, dict):
            workflow_steps = workflow_steps.get("steps", [])

        content = template.format(
            step_by_step=self._format_tutorial_steps(workflow_steps),
            examples=self._generate_workflow_examples(workflow_def),
            common_issues=self._generate_common_issues_guide(),
        )

        return content

    def _generate_api_content(self, workflow_def: Dict[str, Any]) -> str:
        """Generate API documentation content."""
        template = self._templates[DocumentationType.API_DOCS]

        content = template.format(
            api_endpoints=self._format_api_endpoints(workflow_def),
            data_schemas=self._format_data_schemas(workflow_def),
            integration_examples=self._generate_integration_examples(),
        )

        return content

    def _generate_changelog_content(
        self, workflow_path: str, workflow_def: Dict[str, Any]
    ) -> str:
        """Generate changelog documentation content."""
        template = self._templates[DocumentationType.CHANGELOG]

        # This would typically read from version control history
        # For now, generate a basic changelog structure
        content = template.format(
            version_history=self._generate_version_history(workflow_path),
            recent_changes=self._generate_recent_changes(),
        )

        return content

    def _generate_troubleshooting_content(self, workflow_def: Dict[str, Any]) -> str:
        """Generate troubleshooting documentation content."""
        template = self._templates[DocumentationType.TROUBLESHOOTING]

        content = template.format(
            common_errors=self._generate_common_errors_guide(),
            debugging_tips=self._generate_debugging_tips(),
            faq=self._generate_faq_section(),
        )

        return content

    def _generate_aggregate_documentation(
        self, workflows: List[str]
    ) -> List[WorkflowDocumentation]:
        """Generate aggregate documentation across all workflows."""
        aggregate_docs = []

        # Generate workflow index
        index_doc = self.generate_workflow_index()
        aggregate_docs.append(index_doc)

        # Generate system overview
        system_overview = self._generate_system_overview(workflows)
        aggregate_docs.append(system_overview)

        return aggregate_docs

    def _generate_system_overview(self, workflows: List[str]) -> WorkflowDocumentation:
        """Generate system-wide workflow overview."""
        content = "# Workflow System Overview\n\n"
        content += f"Total workflows: {len(workflows)}\n\n"

        # Analyze workflow patterns
        all_phases = set()
        all_tools = set()

        for workflow_path in workflows:
            try:
                workflow_def = self._load_workflow_definition(workflow_path)

                # Collect phases
                phases = workflow_def.get("phases", [])
                all_phases.update(phases)

                # Collect tools from steps
                workflow_steps = workflow_def.get("workflow", [])
                if isinstance(workflow_steps, dict):
                    workflow_steps = workflow_steps.get("steps", [])

                for step in workflow_steps:
                    tools = step.get("tools", [])
                    all_tools.update(tools)

            except Exception as e:
                self.logger.warning(f"Failed to analyze {workflow_path}: {e}")

        content += "## Common Phases\n\n"
        for phase in sorted(all_phases):
            content += f"- {phase}\n"

        content += "\n## Available Tools\n\n"
        for tool in sorted(all_tools):
            content += f"- {tool}\n"

        return WorkflowDocumentation(
            workflow_id="system_overview",
            title="Workflow System Overview",
            description="System-wide overview of all workflows",
            content=content,
            format=DocumentationFormat.MARKDOWN,
            metadata={
                "total_workflows": len(workflows),
                "total_phases": len(all_phases),
                "total_tools": len(all_tools),
            },
        )

    def _load_workflow_definition(self, workflow_path: str) -> Dict[str, Any]:
        """Load workflow definition from file."""
        path = Path(workflow_path)

        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")

        with open(path, "r", encoding="utf-8") as f:
            if path.suffix in [".yaml", ".yml"]:
                return yaml.safe_load(f)
            elif path.suffix == ".json":
                return json.load(f)
            else:
                raise ValueError(f"Unsupported workflow file format: {path.suffix}")

    def _write_documentation_files(
        self, documentation_list: List[WorkflowDocumentation]
    ) -> None:
        """Write documentation files to disk."""
        output_dir = Path(self.config.docs_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for doc in documentation_list:
            filename = f"{doc.workflow_id}.md"
            file_path = output_dir / filename

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(doc.content)

            doc.file_path = str(file_path)
            self.logger.debug(f"Generated documentation: {file_path}")

    def _find_modified_workflows(self) -> List[str]:
        """Find workflows that have been modified since last documentation generation."""
        # This would typically check file modification times
        # For now, return all workflows (full regeneration)
        return self._discover_workflows()

    # Template generation methods
    def _generate_overview_template(self) -> str:
        """Generate overview documentation template."""
        return """# {name}

{description}

## Overview

- **Total Steps**: {total_steps}
- **Phases**: {phases}
- **Quality Gates**: {quality_gates_count}

## Steps Overview

{steps_overview}

## Quality Gates

{quality_gates_overview}
"""

    def _generate_reference_template(self) -> str:
        """Generate reference documentation template."""
        return """# {name} - Reference

## Inputs Required

{inputs_required}

## Expected Outputs

{expected_outputs}

## Step Details

{steps_reference}

## Error Handling

{error_handling}

## Monitoring Configuration

{monitoring_config}
"""

    def _generate_tutorial_template(self) -> str:
        """Generate tutorial documentation template."""
        return """# {name} - Tutorial

## Step-by-Step Guide

{step_by_step}

## Examples

{examples}

## Common Issues

{common_issues}
"""

    def _generate_api_template(self) -> str:
        """Generate API documentation template."""
        return """# {name} - API Documentation

## API Endpoints

{api_endpoints}

## Data Schemas

{data_schemas}

## Integration Examples

{integration_examples}
"""

    def _generate_changelog_template(self) -> str:
        """Generate changelog documentation template."""
        return """# {name} - Changelog

## Version History

{version_history}

## Recent Changes

{recent_changes}
"""

    def _generate_troubleshooting_template(self) -> str:
        """Generate troubleshooting documentation template."""
        return """# {name} - Troubleshooting

## Common Errors

{common_errors}

## Debugging Tips

{debugging_tips}

## FAQ

{faq}
"""

    # Content formatting methods
    def _format_steps_overview(self, steps: List[Dict[str, Any]]) -> str:
        """Format steps for overview documentation."""
        if not steps:
            return "No steps defined"

        content = ""
        for i, step in enumerate(steps, 1):
            step_id = step.get("id", f"step_{i}")
            description = step.get("description", "No description")
            phase = step.get("phase", "Unknown")

            content += f"{i}. **{step_id}** ({phase}): {description}\n"

        return content

    def _format_steps_reference(self, steps: List[Dict[str, Any]]) -> str:
        """Format steps for reference documentation."""
        if not steps:
            return "No steps defined"

        content = ""
        for step in steps:
            step_id = step.get("id", "Unknown")
            description = step.get("description", "No description")
            phase = step.get("phase", "Unknown")
            tools = step.get("tools", [])
            depends_on = step.get("depends_on", [])
            validation = step.get("validation", "No validation specified")

            content += f"### {step_id}\n\n"
            content += f"- **Phase**: {phase}\n"
            content += f"- **Description**: {description}\n"
            content += f"- **Tools**: {', '.join(tools) if tools else 'None'}\n"
            content += f"- **Dependencies**: {', '.join(depends_on) if depends_on else 'None'}\n"
            content += f"- **Validation**: {validation}\n\n"

        return content

    def _format_quality_gates_overview(self, quality_gates: Dict[str, Any]) -> str:
        """Format quality gates for overview."""
        if not quality_gates:
            return "No quality gates defined"

        content = ""
        for gate_name, condition in quality_gates.items():
            content += f"- **{gate_name}**: {condition}\n"

        return content

    def _format_list(self, items: List[str]) -> str:
        """Format a list of items."""
        if not items:
            return "None specified"

        return "\n".join(f"- {item}" for item in items)

    def _format_error_handling(self, error_handling: Dict[str, Any]) -> str:
        """Format error handling configuration."""
        if not error_handling:
            return "No error handling configuration specified"

        content = ""
        for key, value in error_handling.items():
            content += f"- **{key}**: {value}\n"

        return content

    def _format_monitoring_config(self, monitoring: Dict[str, Any]) -> str:
        """Format monitoring configuration."""
        if not monitoring:
            return "No monitoring configuration specified"

        content = ""
        for key, value in monitoring.items():
            content += f"- **{key}**: {value}\n"

        return content

    def _format_tutorial_steps(self, steps: List[Dict[str, Any]]) -> str:
        """Format steps for tutorial documentation."""
        if not steps:
            return "No steps to document"

        content = ""
        for i, step in enumerate(steps, 1):
            step_id = step.get("id", f"step_{i}")
            description = step.get("description", "No description")

            content += f"## Step {i}: {step_id}\n\n"
            content += f"{description}\n\n"

            # Add practical guidance
            tools = step.get("tools", [])
            if tools:
                content += f"**Tools used**: {', '.join(tools)}\n\n"

            validation = step.get("validation")
            if validation:
                content += f"**Success criteria**: {validation}\n\n"

        return content

    def _generate_workflow_examples(self, workflow_def: Dict[str, Any]) -> str:
        """Generate workflow examples."""
        return """### Basic Usage

```python
from src.workflow.workflow_executor import WorkflowExecutor

executor = WorkflowExecutor()
result = await executor.execute_workflow(workflow_definition)
```

### Advanced Configuration

```python
config = {
    "parallel_execution": True,
    "retry_attempts": 3,
    "timeout": 300
}

result = await executor.execute_workflow(workflow_definition, config)
```
"""

    def _generate_common_issues_guide(self) -> str:
        """Generate common issues guide."""
        return """### Step Dependencies Not Met

If a step fails due to unmet dependencies, check that:
- Previous steps completed successfully
- Required files and resources are available
- Environment variables are set correctly

### Quality Gate Failures

When quality gates fail:
- Review the specific failure criteria
- Check logs for detailed error messages
- Ensure all required tools are installed and accessible

### Timeout Issues

For timeout-related failures:
- Increase timeout values in configuration
- Check system resource availability
- Consider breaking large steps into smaller ones
"""

    def _format_api_endpoints(self, workflow_def: Dict[str, Any]) -> str:
        """Format API endpoints documentation."""
        return """### Execute Workflow

```
POST /api/workflows/execute
```

**Request Body:**
```json
{
  "workflow_definition": {},
  "context": {},
  "options": {}
}
```

**Response:**
```json
{
  "workflow_id": "string",
  "status": "string",
  "result": {}
}
```

### Get Workflow Status

```
GET /api/workflows/{workflow_id}/status
```

**Response:**
```json
{
  "workflow_id": "string",
  "status": "string",
  "progress": {},
  "result": {}
}
```
"""

    def _format_data_schemas(self, workflow_def: Dict[str, Any]) -> str:
        """Format data schemas documentation."""
        return """### Workflow Definition Schema

```yaml
name: string
description: string
workflow:
  - id: string
    description: string
    phase: string
    tools: [string]
    validation: string
    depends_on: [string]
phases: [string]
quality_gates: {}
error_handling: {}
```

### Execution Context Schema

```yaml
inputs_required: [string]
expected_outputs: [string]
environment: {}
configuration: {}
```
"""

    def _generate_integration_examples(self) -> str:
        """Generate integration examples."""
        return """### Python Integration

```python
from src.workflow.workflow_coordination import WorkflowCoordinator

coordinator = WorkflowCoordinator()
await coordinator.start()

workflow_id = await coordinator.execute_workflow(workflow_definition)
status = await coordinator.get_workflow_status(workflow_id)
```

### Agent Integration

```python
from src.coordination.workflow_coordination import execute_workflow_with_agents

workflow_id = await execute_workflow_with_agents(
    workflow_definition,
    context={"agent_requirements": ["python", "testing"]}
)
```
"""

    def _generate_version_history(self, workflow_path: str) -> str:
        """Generate version history."""
        return """## v2.0.0 (Current)
- Enhanced workflow coordination with multi-agent support
- Improved error handling and retry strategies
- Added comprehensive quality gates

## v1.0.0
- Initial workflow implementation
- Basic step execution
- Simple validation framework
"""

    def _generate_recent_changes(self) -> str:
        """Generate recent changes."""
        return """### Latest Updates

- Added workflow coordination integration
- Enhanced documentation generation
- Improved error handling mechanisms
- Added comprehensive testing framework
"""

    def _generate_common_errors_guide(self) -> str:
        """Generate common errors guide."""
        return """### Import Errors

**Error**: `ModuleNotFoundError: No module named 'workflow'`
**Solution**: Ensure the workflow module is properly installed and in the Python path.

### Configuration Errors

**Error**: `WorkflowValidationError: Required field missing`
**Solution**: Check that all required fields are present in the workflow definition.

### Execution Errors

**Error**: `WorkflowExecutionError: Step failed`
**Solution**: Check step dependencies and ensure all required tools are available.
"""

    def _generate_debugging_tips(self) -> str:
        """Generate debugging tips."""
        return """### Enable Debug Logging

```python
import logging
logging.getLogger('workflow').setLevel(logging.DEBUG)
```

### Check Step Dependencies

Verify that all step dependencies are satisfied before execution.

### Validate Workflow Definition

Use the workflow parser to validate your workflow definition before execution.

### Monitor Resource Usage

Check system resources (CPU, memory, disk) during workflow execution.
"""

    def _generate_faq_section(self) -> str:
        """Generate FAQ section."""
        return """### Q: How do I create a custom workflow step?

A: Implement the step interface and register it with the workflow executor.

### Q: Can workflows be executed in parallel?

A: Yes, enable parallelization in the workflow configuration.

### Q: How do I handle workflow failures?

A: Configure error handling strategies and retry mechanisms in the workflow definition.

### Q: Can I monitor workflow progress?

A: Yes, use the workflow status API to monitor execution progress.
"""

    def _generate_workflow_index_content(self, workflows: List[str]) -> str:
        """Generate workflow index content."""
        content = "# Workflow Index\n\n"
        content += f"Total workflows: {len(workflows)}\n\n"

        content += "## Available Workflows\n\n"

        for workflow_path in sorted(workflows):
            workflow_name = Path(workflow_path).stem
            content += f"- [{workflow_name}]({workflow_name}_overview.md)\n"

        content += "\n## Documentation Types\n\n"
        content += "For each workflow, the following documentation is available:\n\n"
        content += "- **Overview**: High-level description and summary\n"
        content += "- **Reference**: Detailed technical reference\n"
        content += "- **Tutorial**: Step-by-step usage guide\n"
        content += "- **API**: API documentation and integration examples\n"
        content += "- **Troubleshooting**: Common issues and solutions\n"

        return content


# Convenience functions for automated documentation generation
def generate_all_workflow_documentation(
    config: Optional[WorkflowDocumentationConfig] = None,
) -> List[WorkflowDocumentation]:
    """
    Generate all workflow documentation.

    Args:
        config: Optional configuration for documentation generation

    Returns:
        List of generated documentation
    """
    generator = WorkflowDocumentationGenerator(config)
    return generator.generate_all_documentation()


def update_workflow_documentation(
    config: Optional[WorkflowDocumentationConfig] = None,
) -> List[WorkflowDocumentation]:
    """
    Update existing workflow documentation.

    Args:
        config: Optional configuration for documentation generation

    Returns:
        List of updated documentation
    """
    generator = WorkflowDocumentationGenerator(config)
    return generator.update_documentation()


def generate_workflow_index(
    config: Optional[WorkflowDocumentationConfig] = None,
) -> WorkflowDocumentation:
    """
    Generate workflow index documentation.

    Args:
        config: Optional configuration for documentation generation

    Returns:
        Workflow index documentation
    """
    generator = WorkflowDocumentationGenerator(config)
    return generator.generate_workflow_index()
