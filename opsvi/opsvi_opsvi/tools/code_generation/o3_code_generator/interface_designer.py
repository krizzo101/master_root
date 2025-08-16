"""
Interface Designer for O3 Code Generator

This module provides comprehensive interface design capabilities using OpenAI's O3 models,
including API specifications, protocol definitions, authentication schemes, and documentation generation.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)
else:
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
    from o3_logger.logger import LogConfig, setup_logger
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass

try:
    from schemas.architecture_schemas import InterfaceInput, InterfaceOutput
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass


class InterfaceAnalyzer:
    """Analyzes interface requirements and generates design insights."""

    def __init__(self, logger: Any) -> None:
        """Initialize the interface analyzer."""
        self.logger = logger

    def analyze_interface_requirements(
        self, interface_requirements: str, component_specifications: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze interface requirements and extract design insights.

        Args:
            interface_requirements: Natural language interface requirements
            component_specifications: Component specifications

        Returns:
            Dictionary containing interface analysis
        """
        self.logger.log_info("Starting interface requirements analysis")
        analysis: dict[str, Any] = {
            "interface_patterns": [],
            "protocol_requirements": [],
            "authentication_schemes": [],
            "documentation_needs": [],
            "performance_requirements": {},
            "security_requirements": {},
            "compatibility_requirements": [],
            "complexity_estimates": {},
        }

        analysis["interface_patterns"] = self._analyze_interface_patterns(
            interface_requirements
        )
        analysis["protocol_requirements"] = self._extract_protocol_requirements(
            interface_requirements
        )
        analysis["authentication_schemes"] = self._extract_authentication_requirements(
            interface_requirements
        )
        analysis["documentation_needs"] = self._extract_documentation_requirements(
            interface_requirements
        )
        analysis["performance_requirements"] = self._analyze_performance_requirements(
            interface_requirements
        )
        analysis["security_requirements"] = self._analyze_security_requirements(
            interface_requirements
        )
        analysis[
            "compatibility_requirements"
        ] = self._extract_compatibility_requirements(
            interface_requirements, component_specifications
        )
        analysis["complexity_estimates"] = self._estimate_complexity(
            interface_requirements
        )

        return analysis

    def _analyze_interface_patterns(self, requirements: str) -> list[dict[str, Any]]:
        """Analyze interface patterns from requirements."""
        patterns = []
        if "rest" in requirements.lower() or "http" in requirements.lower():
            patterns.append(
                {
                    "pattern_type": "REST",
                    "description": "RESTful API interface",
                    "methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                }
            )
        if "graphql" in requirements.lower():
            patterns.append(
                {
                    "pattern_type": "GraphQL",
                    "description": "GraphQL query interface",
                    "operations": ["query", "mutation", "subscription"],
                }
            )
        if "grpc" in requirements.lower():
            patterns.append(
                {
                    "pattern_type": "gRPC",
                    "description": "gRPC service interface",
                    "features": ["streaming", "bidirectional"],
                }
            )
        return patterns

    def _extract_protocol_requirements(self, requirements: str) -> list[str]:
        """Extract protocol requirements from interface requirements."""
        protocols = []
        if "https" in requirements.lower():
            protocols.append("HTTPS")
        if "http" in requirements.lower():
            protocols.append("HTTP")
        if "tcp" in requirements.lower():
            protocols.append("TCP")
        if "udp" in requirements.lower():
            protocols.append("UDP")
        return protocols

    def _extract_authentication_requirements(self, requirements: str) -> list[str]:
        """Extract authentication requirements from interface requirements."""
        auth_schemes = []
        if "oauth" in requirements.lower():
            auth_schemes.append("OAuth2")
        if "jwt" in requirements.lower() or "token" in requirements.lower():
            auth_schemes.append("JWT")
        if "api-key" in requirements.lower() or "apikey" in requirements.lower():
            auth_schemes.append("API Key")
        if "basic" in requirements.lower():
            auth_schemes.append("Basic Auth")
        return auth_schemes

    def _extract_documentation_requirements(self, requirements: str) -> list[str]:
        """Extract documentation requirements from interface requirements."""
        doc_types = []
        if "openapi" in requirements.lower() or "swagger" in requirements.lower():
            doc_types.append("OpenAPI")
        if "markdown" in requirements.lower():
            doc_types.append("Markdown")
        if "html" in requirements.lower():
            doc_types.append("HTML")
        return doc_types

    def _analyze_performance_requirements(self, requirements: str) -> dict[str, Any]:
        """Analyze performance requirements from interface requirements."""
        return {
            "response_time": "medium",
            "throughput": "standard",
            "concurrency": "moderate",
            "caching": "recommended",
        }

    def _analyze_security_requirements(self, requirements: str) -> dict[str, Any]:
        """Analyze security requirements from interface requirements."""
        return {
            "authentication": "required",
            "authorization": "role-based",
            "encryption": "transport",
            "rate_limiting": "recommended",
        }

    def _extract_compatibility_requirements(
        self, requirements: str, component_specs: dict[str, Any]
    ) -> list[str]:
        """Extract compatibility requirements."""
        return ["backward_compatible", "versioned"]

    def _estimate_complexity(self, requirements: str) -> dict[str, Any]:
        """Estimate interface complexity."""
        return {
            "overall_complexity": "medium",
            "implementation_effort": "moderate",
            "maintenance_effort": "low",
        }


class InterfaceDiagramGenerator:
    """Generates interface diagrams and visualizations."""

    def __init__(self, logger: Any) -> None:
        """Initialize the diagram generator."""
        self.logger = logger

    def generate_interface_diagram(
        self, interface_specifications: dict[str, Any], diagram_type: str = "plantuml"
    ) -> str:
        """
        Generate interface diagram.

        Args:
            interface_specifications: Interface specifications
            diagram_type: Type of diagram to generate

        Returns:
            Generated diagram content
        """
        if diagram_type == "plantuml":
            return self._generate_plantuml_diagram(interface_specifications)
        elif diagram_type == "mermaid":
            return self._generate_mermaid_diagram(interface_specifications)
        else:
            return self._generate_plantuml_diagram(interface_specifications)

    def _generate_plantuml_diagram(
        self, interface_specifications: dict[str, Any]
    ) -> str:
        """Generate PlantUML interface diagram."""
        diagram = """@startuml Interface Design
!theme plain
skinparam backgroundColor #FFFFFF
skinparam componentStyle rectangle

title Interface Design

"""

        # Add components
        for component in interface_specifications.get("components", []):
            diagram += f'rectangle "{component["name"]}" as {component["name"].replace(" ", "_")}\n'

        # Add interfaces
        for interface in interface_specifications.get("interfaces", []):
            diagram += f'interface "{interface["name"]}" as {interface["name"].replace(" ", "_")}\n'

        # Add relationships
        for relationship in interface_specifications.get("relationships", []):
            diagram += f'{relationship["from"]} --> {relationship["to"]} : {relationship["type"]}\n'

        diagram += "@enduml"
        return diagram

    def _generate_mermaid_diagram(
        self, interface_specifications: dict[str, Any]
    ) -> str:
        """Generate Mermaid interface diagram."""
        diagram = """graph TD
    subgraph "Interface Design"
"""

        # Add components
        for component in interface_specifications.get("components", []):
            diagram += f'        {component["name"].replace(" ", "_")}["{component["name"]}"]\n'

        # Add interfaces
        for interface in interface_specifications.get("interfaces", []):
            diagram += f'        {interface["name"].replace(" ", "_")}["{interface["name"]}"]\n'

        # Add relationships
        for relationship in interface_specifications.get("relationships", []):
            diagram += f'        {relationship["from"]} -->|{relationship["type"]}| {relationship["to"]}\n'

        diagram += "    end"
        return diagram


class InterfaceDesigner:
    """Main interface designer class."""

    def __init__(self, config_path: str | None = None):
        """Initialize the interface designer.

        Args:
            config_path: Optional path to configuration file
        """
        self.config = ConfigManager(config_path)
        log_config = LogConfig(
            level=self.config.get("logging.level", "INFO"),
            log_dir=self.config.get("paths.logs", "logs"),
            standard_log_file="interface_designer.log",
            debug_log_file="interface_designer_debug.log",
            error_log_file="interface_designer_error.log",
        )
        self.logger = setup_logger(log_config)
        self.client = OpenAI(
            api_key=self.config.get("api.openai_api_key"),
            base_url=self.config.get("api.base_url", "https://api.openai.com/v1"),
        )
        self.analyzer = InterfaceAnalyzer(self.logger)
        self.diagram_generator = InterfaceDiagramGenerator(self.logger)
        self._create_directories()
        self.logger.log_info("Interface Designer initialized successfully")

    def _create_directories(self) -> None:
        """Create necessary output directories."""
        directories = [
            self.config.get("paths.generated_files", "generated_files"),
            f"{self.config.get('paths.generated_files', 'generated_files')}/interfaces",
            f"{self.config.get('paths.generated_files', 'generated_files')}/interfaces/diagrams",
            f"{self.config.get('paths.generated_files', 'generated_files')}/interfaces/specifications",
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            self.logger.log_debug(f"Directory created/verified: {directory}")

    def design_apis(self, input_data: InterfaceInput) -> InterfaceOutput:
        """
        Design comprehensive interface specifications based on requirements.

        Args:
            input_data: Interface design input specification

        Returns:
            Interface design output with specifications and diagrams
        """
        start_time = time.time()
        self.logger.log_info("Starting interface design")

        try:
            interface_analysis = self.analyzer.analyze_interface_requirements(
                input_data.interface_requirements, input_data.component_specifications
            )

            interface_specifications = self._generate_with_o3_model(
                input_data, interface_analysis
            )

            diagrams = []
            if input_data.include_diagrams:
                diagrams = self._generate_diagrams(interface_specifications, input_data)

            output_files = self._create_interface_files(
                interface_specifications, input_data
            )

            generation_time = time.time() - start_time
            self.logger.log_info(
                f"Interface design completed in {generation_time:.2f} seconds"
            )

            return InterfaceOutput(
                success=True,
                interface_specifications=interface_specifications,
                output_files=output_files,
                diagrams=diagrams,
                generation_time=generation_time,
                model_used=input_data.model,
            )

        except Exception as e:
            self.logger.log_error(e, "Error during interface design")
            return InterfaceOutput(
                success=False,
                interface_specifications={},
                output_files=[],
                diagrams=[],
                generation_time=time.time() - start_time,
                model_used=input_data.model,
                error_message=str(e),
            )

    def _generate_with_o3_model(
        self, input_data: InterfaceInput, interface_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Generate interface specifications using O3 model.

        Args:
            input_data: Interface input data
            interface_analysis: Interface analysis results

        Returns:
            Generated interface specifications
        """
        prompt = self._build_prompt(input_data, interface_analysis)

        messages = [
            {
                "role": "system",
                "content": "You are an expert interface designer. Generate comprehensive interface specifications including API definitions, protocols, authentication schemes, and documentation requirements.",
            },
            {"role": "user", "content": prompt},
        ]

        response = self.client.chat.completions.create(
            model=input_data.model,
            messages=messages,
            max_tokens=input_data.max_tokens,
            temperature=0.1,
        )

        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            # Fallback to structured response
            return self._parse_structured_response(response.choices[0].message.content)

    def _build_prompt(
        self, input_data: InterfaceInput, interface_analysis: dict[str, Any]
    ) -> str:
        """Build the prompt for interface design."""
        prompt = f"""
Design comprehensive interface specifications for the following requirements:

Interface Requirements: {input_data.interface_requirements}
Interface Type: {input_data.interface_type}
Protocol Requirements: {', '.join(input_data.protocol_requirements)}
Authentication Requirements: {', '.join(input_data.authentication_requirements)}
Documentation Requirements: {', '.join(input_data.documentation_requirements)}

Component Specifications: {json.dumps(input_data.component_specifications, indent=2)}

Interface Analysis: {json.dumps(interface_analysis, indent=2)}

Generate a comprehensive interface specification including:
1. API endpoints and methods
2. Request/response schemas
3. Authentication mechanisms
4. Error handling
5. Documentation structure
6. Performance considerations
7. Security measures

Return the response as valid JSON.
"""
        return prompt

    def _parse_structured_response(self, response: str) -> dict[str, Any]:
        """Parse structured response when JSON parsing fails."""
        return {
            "interfaces": [],
            "api_endpoints": [],
            "authentication": {},
            "documentation": {},
            "error_handling": {},
            "raw_response": response,
        }

    def _generate_diagrams(
        self, interface_specifications: dict[str, Any], input_data: InterfaceInput
    ) -> list[str]:
        """Generate interface diagrams."""
        diagrams = []

        try:
            # Generate PlantUML diagram
            plantuml_content = self.diagram_generator.generate_interface_diagram(
                interface_specifications, "plantuml"
            )
            plantuml_path = f"{self.config.get('paths.generated_files', 'generated_files')}/interfaces/diagrams/interface_design.puml"
            Path(plantuml_path).write_text(plantuml_content)
            diagrams.append(plantuml_path)

            # Generate Mermaid diagram
            mermaid_content = self.diagram_generator.generate_interface_diagram(
                interface_specifications, "mermaid"
            )
            mermaid_path = f"{self.config.get('paths.generated_files', 'generated_files')}/interfaces/diagrams/interface_design.md"
            Path(mermaid_path).write_text(f"```mermaid\n{mermaid_content}\n```")
            diagrams.append(mermaid_path)

        except Exception as e:
            self.logger.log_error(e, "Error generating diagrams")

        return diagrams

    def _create_interface_files(
        self, interface_specifications: dict[str, Any], input_data: InterfaceInput
    ) -> list[str]:
        """Create interface specification files."""
        output_files = []

        try:
            # Create JSON specification
            json_path = f"{self.config.get('paths.generated_files', 'generated_files')}/interfaces/specifications/interface_spec.json"
            Path(json_path).write_text(json.dumps(interface_specifications, indent=2))
            output_files.append(json_path)

            # Create Markdown documentation
            markdown_content = self._convert_to_markdown(interface_specifications)
            markdown_path = f"{self.config.get('paths.generated_files', 'generated_files')}/interfaces/specifications/interface_documentation.md"
            Path(markdown_path).write_text(markdown_content)
            output_files.append(markdown_path)

            # Create OpenAPI specification if REST interface
            if input_data.interface_type.lower() == "rest":
                openapi_spec = self._generate_openapi_spec(interface_specifications)
                openapi_path = f"{self.config.get('paths.generated_files', 'generated_files')}/interfaces/specifications/openapi.yaml"
                Path(openapi_path).write_text(openapi_spec)
                output_files.append(openapi_path)

        except Exception as e:
            self.logger.log_error(e, "Error creating interface files")

        return output_files

    def _convert_to_markdown(self, interface_specifications: dict[str, Any]) -> str:
        """Convert interface specifications to Markdown."""
        markdown = """# Interface Design Specification

## Overview
This document describes the interface design for the system.

## API Endpoints
"""

        for endpoint in interface_specifications.get("api_endpoints", []):
            markdown += f"""
### {endpoint.get('method', 'GET')} {endpoint.get('path', '/')}
**Description:** {endpoint.get('description', 'No description')}

**Parameters:**
"""
            for param in endpoint.get("parameters", []):
                markdown += f"- {param.get('name', '')}: {param.get('type', '')} - {param.get('description', '')}\n"

            markdown += f"""
**Response:**
```json
{json.dumps(endpoint.get('response', {}), indent=2)}
```
"""

        return markdown

    def _generate_openapi_spec(self, interface_specifications: dict[str, Any]) -> str:
        """Generate OpenAPI specification."""
        openapi = """openapi: 3.0.0
info:
  title: Interface API
  version: 1.0.0
  description: Generated interface specification

paths:
"""

        for endpoint in interface_specifications.get("api_endpoints", []):
            path = endpoint.get("path", "/")
            method = endpoint.get("method", "get").lower()

            openapi += f"""
  {path}:
    {method}:
      summary: {endpoint.get('description', 'No description')}
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
"""

        return openapi


def main() -> None:
    """Main entry point for the interface designer."""
    parser = argparse.ArgumentParser(
        description="Interface Designer - AI-powered interface design"
    )
    parser.add_argument(
        "input_file",
        help="Path to input file (JSON or YAML) containing interface design parameters",
    )
    parser.add_argument("--config", help="Path to configuration file", default=None)
    args = parser.parse_args()

    try:
        designer = InterfaceDesigner(args.config)

        # Load input data
        with open(args.input_file) as f:
            input_data = json.load(f)

        # Create InterfaceInput object
        interface_input = InterfaceInput(**input_data)

        # Generate interface design
        output = designer.design_apis(interface_input)

        if output.success:
            print("Interface design completed successfully!")
            print(f"Output files: {output.output_files}")
            print(f"Diagrams: {output.diagrams}")
        else:
            print(f"Interface design failed: {output.error_message}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
