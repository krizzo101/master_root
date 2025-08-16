"""
Technical Specification Generator - AI-powered technical specification generation using OpenAI's O3 models.

This script generates comprehensive technical specifications including system architecture,
API specifications, database schemas, integration specifications, and performance requirements
using OpenAI's latest O3 and O3-mini models with structured input/output schemas.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)
else:
    pass
try:
    from openai import OpenAI
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass
try:
    from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
        ConfigManager,
    )
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass
try:
    from o3_logger.logger import get_logger, setup_logger
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass
try:
    from schemas.technical_spec_schemas import (
        OutputFormat,
        SpecificationType,
        TechnicalSpecInput,
        TechnicalSpecOutput,
    )
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass
try:
    from prompts.technical_spec_prompts import TECHNICAL_SPEC_SYSTEM_PROMPT
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass


class InputFileLoader:
    """Load and validate input files for technical specification generation."""

    def __init__(self, logger):
        self.logger = logger

    def load_input_file(self, file_path: str) -> dict[str, Any]:
        """
        Load input file in JSON or YAML format.

        Args:
            file_path: Path to the input file

        Returns:
            Dictionary containing input data

        Raises:
            ValueError: If file format is not supported or file is invalid
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise ValueError(f"Input file not found: {file_path}")
            else:
                pass
            self.logger.log_info(f"Loading input file: {file_path}")
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            if file_path.suffix.lower() in [".json"]:
                data = json.loads(content)
            elif file_path.suffix.lower() in [".yaml", ".yml"]:
                import yaml

                data = yaml.safe_load(content)
            else:
                raise ValueError(
                    f"Unsupported file format: {file_path.suffix}. Use .json, .yaml, or .yml"
                )
            cleaned_data = self._clean_template_data(data)
            self._validate_required_fields(cleaned_data)
            return cleaned_data
        except Exception as e:
            self.logger.log_error(e, f"Failed to load input file: {file_path}")
            raise
        else:
            pass
        finally:
            pass

    def _clean_template_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remove template comments and metadata from data."""
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if not k.startswith("_")}
        else:
            pass
        return data

    def _validate_required_fields(self, data: dict[str, Any]) -> None:
        """Validate that required fields are present."""
        required_fields = ["system_architecture", "technology_stack"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        else:
            pass


class OutputFileManager:
    """Manage output file generation and organization."""

    def __init__(self, logger):
        self.logger = logger
        self.output_dir = Path("generated_files/technical_specs")
        self._ensure_output_directory()

    def _ensure_output_directory(self) -> None:
        """Ensure output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.log_info(f"Output directory ensured: {self.output_dir}")

    def save_specification(
        self,
        specification: dict[str, Any],
        output_format: OutputFormat,
        base_filename: str,
    ) -> list[str]:
        """
        Save specification in the specified format.

        Args:
            specification: The specification data to save
            output_format: The format to save in
            base_filename: Base filename for the output

        Returns:
            List of generated file paths
        """
        generated_files = []
        try:
            if output_format == OutputFormat.JSON:
                file_path = self.output_dir / f"{base_filename}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(specification, f, indent=2)
                generated_files.append(str(file_path))
            elif output_format == OutputFormat.MARKDOWN:
                file_path = self.output_dir / f"{base_filename}.md"
                markdown_content = self._convert_to_markdown(specification)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                generated_files.append(str(file_path))
            elif output_format == OutputFormat.YAML:
                import yaml

                file_path = self.output_dir / f"{base_filename}.yaml"
                with open(file_path, "w", encoding="utf-8") as f:
                    yaml.dump(specification, f, default_flow_style=False, indent=2)
                generated_files.append(str(file_path))
            elif output_format == OutputFormat.HTML:
                file_path = self.output_dir / f"{base_filename}.html"
                html_content = self._convert_to_html(specification)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                generated_files.append(str(file_path))
            elif output_format == OutputFormat.OPENAPI:
                if "api_specifications" in specification:
                    openapi_file = self.output_dir / f"{base_filename}_openapi.json"
                    with open(openapi_file, "w", encoding="utf-8") as f:
                        json.dump(
                            specification["api_specifications"]["openapi_spec"],
                            f,
                            indent=2,
                        )
                    generated_files.append(str(openapi_file))
                else:
                    pass
                file_path = self.output_dir / f"{base_filename}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(specification, f, indent=2)
                generated_files.append(str(file_path))
            else:
                pass
            self.logger.log_info(f"Saved specification to: {generated_files}")
            return generated_files
        except Exception as e:
            self.logger.log_error(
                e, f"Failed to save specification in {output_format} format"
            )
            raise
        else:
            pass
        finally:
            pass

    def _convert_to_markdown(self, specification: dict[str, Any]) -> str:
        """Convert specification to Markdown format."""
        markdown_lines = []
        if "system_overview" in specification:
            markdown_lines.extend(
                ["# System Overview", "", specification["system_overview"], ""]
            )
        else:
            pass
        if "api_specifications" in specification:
            markdown_lines.extend(["# API Specifications", "", "## Endpoints", ""])
            for endpoint in specification["api_specifications"].get("endpoints", []):
                markdown_lines.extend(
                    [
                        f"### {endpoint.get('method', 'GET')} {endpoint.get('path', '')}",
                        f"**Summary:** {endpoint.get('summary', '')}",
                        "",
                    ]
                )
            else:
                pass
        else:
            pass
        if "database_schemas" in specification:
            markdown_lines.extend(["# Database Schemas", "", "## Tables", ""])
            for table in specification["database_schemas"].get("table_definitions", []):
                markdown_lines.extend(
                    [
                        f"### {table.get('table_name', '')}",
                        "",
                        "| Column | Type | Constraints |",
                        "|--------|------|-------------|",
                    ]
                )
                for column in table.get("columns", []):
                    markdown_lines.append(
                        f"| {column.get('name', '')} | {column.get('type', '')} | {column.get('constraints', '')} |"
                    )
                else:
                    pass
                markdown_lines.append("")
            else:
                pass
        else:
            pass
        if "implementation_guidelines" in specification:
            markdown_lines.extend(["# Implementation Guidelines", ""])
            for category, guidelines in specification[
                "implementation_guidelines"
            ].items():
                markdown_lines.extend([f"## {category.replace('_', ' ').title()}", ""])
                if isinstance(guidelines, list):
                    for guideline in guidelines:
                        if isinstance(guideline, dict):
                            markdown_lines.extend(
                                [f"### {guideline.get('category', 'Guideline')}", ""]
                            )
                            for item in guideline.get("guidelines", []):
                                markdown_lines.append(f"- {item}")
                            else:
                                pass
                            markdown_lines.append("")
                        else:
                            markdown_lines.append(f"- {guideline}")
                    else:
                        pass
                else:
                    pass
                markdown_lines.append("")
            else:
                pass
        else:
            pass
        return "\n".join(markdown_lines)

    def _convert_to_html(self, specification: dict[str, Any]) -> str:
        """Convert specification to HTML format."""
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "    <title>Technical Specification</title>",
            "    <style>",
            "        body { font-family: Arial, sans-serif; margin: 40px; }",
            "        h1 { color: #333; }",
            "        h2 { color: #666; margin-top: 30px; }",
            "        h3 { color: #888; }",
            "        .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; }",
            "        .table { border-collapse: collapse; width: 100%; }",
            "        .table th, .table td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "        .table th { background-color: #f2f2f2; }",
            "    </style>",
            "</head>",
            "<body>",
            "    <h1>Technical Specification</h1>",
            "",
        ]
        if "system_overview" in specification:
            html_lines.extend(
                [
                    "    <h2>System Overview</h2>",
                    f"    <p>{specification['system_overview']}</p>",
                    "",
                ]
            )
        else:
            pass
        if "api_specifications" in specification:
            html_lines.extend(
                ["    <h2>API Specifications</h2>", "    <h3>Endpoints</h3>", ""]
            )
            for endpoint in specification["api_specifications"].get("endpoints", []):
                html_lines.extend(
                    [
                        "    <div class='endpoint'>",
                        f"        <h4>{endpoint.get('method', 'GET')} {endpoint.get('path', '')}</h4>",
                        f"        <p><strong>Summary:</strong> {endpoint.get('summary', '')}</p>",
                        "    </div>",
                        "",
                    ]
                )
            else:
                pass
        else:
            pass
        if "database_schemas" in specification:
            html_lines.extend(
                ["    <h2>Database Schemas</h2>", "    <h3>Tables</h3>", ""]
            )
            for table in specification["database_schemas"].get("table_definitions", []):
                html_lines.extend(
                    [
                        f"    <h4>{table.get('table_name', '')}</h4>",
                        "    <table class='table'>",
                        "        <tr><th>Column</th><th>Type</th><th>Constraints</th></tr>",
                    ]
                )
                for column in table.get("columns", []):
                    html_lines.append(
                        f"        <tr><td>{column.get('name', '')}</td><td>{column.get('type', '')}</td><td>{column.get('constraints', '')}</td></tr>"
                    )
                else:
                    pass
                html_lines.extend(["    </table>", ""])
            else:
                pass
        else:
            pass
        html_lines.extend(["</body>", "</html>"])
        return "\n".join(html_lines)


class TechnicalSpecGenerator:
    """Main technical specification generator using OpenAI O3 models."""

    def __init__(self, config_path: str | None = None):
        """
        Initialize the TechnicalSpecGenerator.

        Args:
            config_path: Optional path to configuration file
        """
        self.config_manager = ConfigManager(config_path)
        log_config = self.config_manager.get_logging_config()
        setup_logger(log_config)
        self.logger = get_logger()
        self.logger.log_system_event("TechnicalSpecGenerator initialized")
        api_config = self.config_manager.get_api_config()
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"), base_url=api_config.base_url
        )
        self.input_loader = InputFileLoader(self.logger)
        self.output_manager = OutputFileManager(self.logger)
        self._create_directories()
        self.logger.log_info("TechnicalSpecGenerator initialization complete")

    def _create_directories(self) -> None:
        """Create necessary directories for the generator."""
        directories = [
            "generated_files/technical_specs",
            "logs",
            "config",
            "schemas",
            "prompts",
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            self.logger.log_debug(f"Directory created/verified: {directory}")
        else:
            pass

    def generate_technical_specs(
        self, input_data: TechnicalSpecInput
    ) -> TechnicalSpecOutput:
        """
        Generate comprehensive technical specifications.

        Args:
            input_data: Input data for specification generation

        Returns:
            TechnicalSpecOutput containing generated specifications
        """
        start_time = time.time()
        try:
            self.logger.log_info("Starting technical specification generation")
            self.logger.log_user_action(
                "technical_spec_generation_started",
                {
                    "specification_type": input_data.specification_type.value,
                    "output_format": input_data.output_format.value,
                    "model": input_data.model,
                },
            )
            prompt = self._build_prompt(input_data)
            self.logger.log_info(f"Calling O3 model: {input_data.model}")
            self.logger.log_api_call_start(input_data.model, len(prompt))
            response = self.client.chat.completions.create(
                model=input_data.model,
                messages=[
                    {
                        "role": "system",
                        "content": TECHNICAL_SPEC_SYSTEM_PROMPT,
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            generation_time = time.time() - start_time
            try:
                response_text = response.choices[0].message.content
                self.logger.log_api_call_success(
                    input_data.model, len(response_text), generation_time
                )
                specifications = json.loads(response_text)
            except json.JSONDecodeError as e:
                self.logger.log_error(e, "Failed to parse O3 model response as JSON")
                raise ValueError(f"Invalid JSON response from O3 model: {e}")
            except (IndexError, AttributeError) as e:
                self.logger.log_error(e, "Failed to parse O3 model response structure")
                raise ValueError(f"Error processing response data: {e}")
            else:
                pass
            finally:
                pass
            base_filename = f"technical_spec_{int(time.time())}"
            output_files = self.output_manager.save_specification(
                specifications["technical_specifications"],
                input_data.output_format,
                base_filename,
            )
            output = TechnicalSpecOutput(
                success=True,
                technical_specifications=specifications["technical_specifications"],
                system_overview=specifications["technical_specifications"].get(
                    "system_overview", ""
                ),
                api_specifications=specifications["technical_specifications"].get(
                    "api_specifications"
                ),
                database_schemas=specifications["technical_specifications"].get(
                    "database_schemas"
                ),
                integration_specifications=specifications[
                    "technical_specifications"
                ].get("integration_specifications"),
                performance_specifications=specifications[
                    "technical_specifications"
                ].get("performance_specifications"),
                security_specifications=specifications["technical_specifications"].get(
                    "security_specifications"
                ),
                implementation_guidelines=specifications[
                    "technical_specifications"
                ].get("implementation_guidelines", {}),
                output_files=output_files,
                generation_time=generation_time,
                model_used=input_data.model,
            )
            self.logger.log_info(
                f"Technical specification generation completed in {generation_time:.2f}s"
            )
            self.logger.log_user_action(
                "technical_spec_generation_completed",
                {"output_files": output_files, "generation_time": generation_time},
            )
            return output
        except Exception as e:
            generation_time = time.time() - start_time
            self.logger.log_error(e, "Technical specification generation failed")
            return TechnicalSpecOutput(
                success=False,
                technical_specifications={},
                system_overview="",
                implementation_guidelines={},
                output_files=[],
                generation_time=generation_time,
                model_used=input_data.model,
                error_message=str(e),
            )
        else:
            pass
        finally:
            pass

    def _build_prompt(self, input_data: TechnicalSpecInput) -> str:
        """
        Build the prompt for O3 model based on input data.

        Args:
            input_data: Input data for specification generation

        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            f"System Architecture: {input_data.system_architecture}",
            f"Specification Type: {input_data.specification_type.value}",
            f"Technology Stack: {input_data.technology_stack.language}",
        ]
        if input_data.technology_stack.framework:
            prompt_parts.append(f"Framework: {input_data.technology_stack.framework}")
        else:
            pass
        if input_data.technology_stack.database:
            prompt_parts.append(f"Database: {input_data.technology_stack.database}")
        else:
            pass
        if input_data.technology_stack.cache:
            prompt_parts.append(f"Cache: {input_data.technology_stack.cache}")
        else:
            pass
        if input_data.technology_stack.message_queue:
            prompt_parts.append(
                f"Message Queue: {input_data.technology_stack.message_queue}"
            )
        else:
            pass
        if input_data.technology_stack.containerization:
            prompt_parts.append(
                f"Containerization: {input_data.technology_stack.containerization}"
            )
        else:
            pass
        if input_data.technology_stack.cloud_platform:
            prompt_parts.append(
                f"Cloud Platform: {input_data.technology_stack.cloud_platform}"
            )
        else:
            pass
        if input_data.technology_stack.monitoring:
            prompt_parts.append(f"Monitoring: {input_data.technology_stack.monitoring}")
        else:
            pass
        if input_data.api_specs:
            prompt_parts.extend(
                [
                    "",
                    "API Specifications:",
                    f"- REST API: {input_data.api_specs.include_rest}",
                    f"- GraphQL: {input_data.api_specs.include_graphql}",
                    f"- WebSocket: {input_data.api_specs.include_websocket}",
                    f"- Authentication Methods: {', '.join(input_data.api_specs.authentication_methods)}",
                    f"- Rate Limiting: {input_data.api_specs.rate_limiting}",
                    f"- API Versioning: {input_data.api_specs.versioning}",
                    f"- Documentation: {input_data.api_specs.documentation}",
                ]
            )
        else:
            pass
        if input_data.database_specs:
            prompt_parts.extend(
                [
                    "",
                    "Database Specifications:",
                    f"- Database Type: {input_data.database_specs.database_type}",
                    f"- Include Schema: {input_data.database_specs.include_schema}",
                    f"- Include Migrations: {input_data.database_specs.include_migrations}",
                    f"- Include Indexes: {input_data.database_specs.include_indexes}",
                    f"- Include Constraints: {input_data.database_specs.include_constraints}",
                    f"- Include Triggers: {input_data.database_specs.include_triggers}",
                    f"- Include Stored Procedures: {input_data.database_specs.include_stored_procedures}",
                ]
            )
        else:
            pass
        if input_data.integration_specs:
            prompt_parts.extend(
                [
                    "",
                    "Integration Specifications:",
                    f"- External APIs: {', '.join(input_data.integration_specs.external_apis)}",
                    f"- Message Queues: {', '.join(input_data.integration_specs.message_queues)}",
                    f"- Event Streams: {', '.join(input_data.integration_specs.event_streams)}",
                    f"- Data Sync: {input_data.integration_specs.data_sync}",
                    f"- Service Mesh: {input_data.integration_specs.service_mesh}",
                    f"- API Gateway: {input_data.integration_specs.api_gateway}",
                ]
            )
        else:
            pass
        if input_data.performance_specs:
            prompt_parts.extend(
                [
                    "",
                    "Performance Specifications:",
                    f"- Load Testing: {input_data.performance_specs.load_testing}",
                    f"- Performance Benchmarks: {input_data.performance_specs.performance_benchmarks}",
                    f"- Scalability Requirements: {input_data.performance_specs.scalability_requirements}",
                    f"- Resource Utilization: {input_data.performance_specs.resource_utilization}",
                    f"- Monitoring and Alerting: {input_data.performance_specs.monitoring_alerting}",
                    f"- Optimization Guidelines: {input_data.performance_specs.optimization_guidelines}",
                ]
            )
        else:
            pass
        if input_data.security_specs:
            prompt_parts.extend(
                [
                    "",
                    "Security Specifications:",
                    f"- Authentication: {input_data.security_specs.authentication}",
                    f"- Authorization: {input_data.security_specs.authorization}",
                    f"- Data Encryption: {input_data.security_specs.data_encryption}",
                    f"- Network Security: {input_data.security_specs.network_security}",
                    f"- Compliance: {', '.join(input_data.security_specs.compliance)}",
                    f"- Vulnerability Scanning: {input_data.security_specs.vulnerability_scanning}",
                ]
            )
        else:
            pass
        if input_data.additional_requirements:
            prompt_parts.extend(
                ["", "Additional Requirements:", input_data.additional_requirements]
            )
        else:
            pass
        if input_data.context_files:
            prompt_parts.extend(
                ["", "Context Files:", ", ".join(input_data.context_files)]
            )
        else:
            pass
        if input_data.variables:
            prompt_parts.extend(
                ["", "Variables:", json.dumps(input_data.variables, indent=2)]
            )
        else:
            pass
        return "\n".join(prompt_parts)

    def define_system_requirements(
        self, architecture: str, technology_stack: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Define system requirements based on architecture and technology stack.

        Args:
            architecture: System architecture description
            technology_stack: Technology stack configuration

        Returns:
            Dictionary containing system requirements
        """
        self.logger.log_info("Defining system requirements")
        prompt = f"\n        System Architecture: {architecture}\n        Technology Stack: {json.dumps(technology_stack, indent=2)}\n\n        Define comprehensive system requirements including:\n        1. Functional requirements\n        2. Non-functional requirements\n        3. Performance requirements\n        4. Security requirements\n        5. Scalability requirements\n        6. Availability requirements\n        7. Compliance requirements\n        "
        try:
            response = self.client.chat.completions.create(
                model="o3-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert system requirements analyst. Generate comprehensive system requirements in JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=4000,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            self.logger.log_error(e, "Failed to define system requirements")
            raise
        else:
            pass
        finally:
            pass

    def specify_implementation_details(
        self, specifications: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Specify detailed implementation details for the technical specifications.

        Args:
            specifications: Generated technical specifications

        Returns:
            Dictionary containing implementation details
        """
        self.logger.log_info("Specifying implementation details")
        prompt = f"\n        Technical Specifications: {json.dumps(specifications, indent=2)}\n\n        Provide detailed implementation details including:\n        1. Development guidelines\n        2. Code examples\n        3. Configuration examples\n        4. Deployment procedures\n        5. Testing strategies\n        6. Monitoring setup\n        7. Security implementation\n        8. Performance optimization\n        "
        try:
            response = self.client.chat.completions.create(
                model="o3-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert implementation specialist. Generate detailed implementation details in JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=4000,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            self.logger.log_error(e, "Failed to specify implementation details")
            raise
        else:
            pass
        finally:
            pass


def main() -> None:
    """Main entry point for the TechnicalSpecGenerator."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive technical specifications using O3 models"
    )
    parser.add_argument(
        "input_file", help="Input JSON/YAML file with specification requirements"
    )
    parser.add_argument(
        "--save-file",
        action="store_true",
        help="Save generated specifications to files",
    )
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()
    try:
        generator = TechnicalSpecGenerator(args.config)
        input_data_dict = generator.input_loader.load_input_file(args.input_file)
        input_data = TechnicalSpecInput(**input_data_dict)
        output = generator.generate_technical_specs(input_data)
        if output.success:
            if args.save_file:
                pass
            else:
                pass
        else:
            pass
            sys.exit(1)
    except Exception:
        sys.exit(1)
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
