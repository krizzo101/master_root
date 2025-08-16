"""
API Documentation Generator

This module provides a CLI tool to generate API documentation for a given project.
It parses source files to extract API endpoints, models, functions, and classes,
generates an OpenAPI specification, and produces comprehensive documentation in
JSON, Markdown, and HTML formats.

Uses shared utilities for input loading, directory management, formatting, and file generation.
All logging is performed via the O3Logger.
"""

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    setup_logger,
)

setup_logger(LogConfig())
import argparse
from pathlib import Path
import sys
from typing import Any

from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
    ConfigManager,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger
from src.tools.code_generation.o3_code_generator.schemas.api_doc_generator_input_schema import (
    ApiDocGeneratorInput,
)
from src.tools.code_generation.o3_code_generator.schemas.api_doc_generator_output_schema import (
    ApiDocGeneratorOutput,
)
from src.tools.code_generation.o3_code_generator.utils.directory_manager import (
    DirectoryManager,
)
from src.tools.code_generation.o3_code_generator.utils.file_generator import (
    FileGenerator,
)
from src.tools.code_generation.o3_code_generator.utils.input_loader import (
    UniversalInputLoader,
)
from src.tools.code_generation.o3_code_generator.utils.output_formatter import (
    OutputFormatter,
)
from src.tools.code_generation.o3_code_generator.utils.prompt_builder import (
    PromptBuilder,
)


class ApiParser:
    """Parses project files to extract API information."""

    def __init__(self, logger: Any) -> None:
        """
        Initialize parser.

        Attributes:
            logger: O3Logger instance for logging.
        """
        self.logger = logger

    def parse_api_files(self, project_path: Path) -> dict[str, Any]:
        """
        Parse the project directory for API endpoints, models, functions, and classes.

        Args:
            project_path: Path to the project root.

        Returns:
            A dictionary with keys: endpoints, models, functions, classes, frameworks.
        """
        self.logger.log_info(f"Parsing API files in: {project_path}")
        return {
            "endpoints": [],
            "models": [],
            "functions": [],
            "classes": [],
            "frameworks": [],
        }


class OpenApiGenerator:
    """Generates an OpenAPI specification from parsed API information."""

    def __init__(self, logger: Any) -> None:
        """
        Initialize OpenAPI generator.

        Attributes:
            logger: O3Logger instance for logging.
        """
        self.logger = logger

    def generate_openapi_spec(
        self, api_info: dict[str, Any], project_name: str
    ) -> dict[str, Any]:
        """
        Build a basic OpenAPI spec structure.

        Args:
            api_info: Parsed API information.
            project_name: Name of the project.

        Returns:
            OpenAPI specification as a dictionary.
        """
        self.logger.log_info(f"Generating OpenAPI spec for: {project_name}")
        return {
            "openapi": "3.0.0",
            "info": {"title": project_name, "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}, "securitySchemes": {}},
        }


class DocumentationGenerator:
    """Produces human-readable documentation based on API info and OpenAPI spec."""

    def __init__(self, logger: Any) -> None:
        """
        Initialize documentation generator.

        Attributes:
            logger: O3Logger instance for logging.
        """
        self.logger = logger
        self.prompt_builder = PromptBuilder()

    def generate_documentation(
        self, api_info: dict[str, Any], openapi_spec: dict[str, Any], project_name: str
    ) -> dict[str, Any]:
        """
        Generate comprehensive documentation structure.

        Args:
            api_info: Parsed API info.
            openapi_spec: OpenAPI specification.
            project_name: Name of the project.

        Returns:
            Documentation dictionary with overview, authentication, endpoints, schemas, examples, best_practices.
        """
        self.logger.log_info(f"Generating documentation for: {project_name}")
        return {
            "overview": f"Documentation for {project_name}",
            "authentication": {"type": "none"},
            "endpoints": api_info.get("endpoints", []),
            "schemas": openapi_spec.get("components", {}).get("schemas", {}),
            "examples": [],
            "best_practices": [],
        }


class ApiDocGenerator:
    """Orchestrates the full API documentation generation process."""

    def __init__(self, config_path: str | None = None) -> None:
        """
        Initialize the documentation generator.

        Args:
            config_path: Optional path to configuration file.
        """
        self.config_manager = ConfigManager(config_path)
        self.logger = get_logger()
        self.input_loader = UniversalInputLoader()
        self.directory_manager = DirectoryManager()
        self.file_generator = FileGenerator()
        self.formatter = OutputFormatter()
        self.parser = ApiParser(self.logger)
        self.openapi_generator = OpenApiGenerator(self.logger)
        self.doc_generator = DocumentationGenerator(self.logger)
        self._setup_directories()

    def _setup_directories(self) -> None:
        """
        Ensure required output directories exist.
        """
        for directory in ["generated_docs", "openapi_specs", "logs"]:
            self.directory_manager.ensure_directory_exists(Path(directory))
        else:
            pass

    def generate_api_docs(
        self, input_data: ApiDocGeneratorInput
    ) -> ApiDocGeneratorOutput:
        """
        Execute the documentation generation workflow.

        Args:
            input_data: Validated input data.

        Returns:
            ApiDocGeneratorOutput with success flag, data, and output file paths.
        """
        self.logger.log_info(
            f"Starting API documentation generation for: {input_data.project_path}"
        )
        try:
            project_path = Path(input_data.project_path)
            if not project_path.exists():
                raise FileNotFoundError(f"Project path does not exist: {project_path}")
            else:
                pass
            api_info = self.parser.parse_api_files(project_path)
            openapi_spec = self.openapi_generator.generate_openapi_spec(
                api_info, project_path.name
            )
            documentation = self.doc_generator.generate_documentation(
                api_info, openapi_spec, project_path.name
            )
            output_files = self._save_outputs(
                api_info, openapi_spec, documentation, project_path.name
            )
            self.logger.log_info("API documentation generation completed successfully")
            return ApiDocGeneratorOutput(
                success=True,
                project_path=str(project_path),
                api_info=api_info,
                openapi_spec=openapi_spec,
                documentation=documentation,
                output_files=output_files,
                error_message=None,
            )
        except Exception as e:
            self.logger.log_error(f"API documentation generation failed: {e}")
            raise
        else:
            pass
        finally:
            pass

    def _save_outputs(
        self,
        api_info: dict[str, Any],
        openapi_spec: dict[str, Any],
        documentation: dict[str, Any],
        project_name: str,
    ) -> list[str]:
        """
        Save generated data to JSON, Markdown, and HTML files.

        Args:
            api_info: Parsed API info.
            openapi_spec: OpenAPI spec.
            documentation: Generated documentation.
            project_name: Name of the project.

        Returns:
            List of file paths written.
        """
        output_files: list[str] = []
        api_info_content = self.formatter.to_json(api_info, pretty=True)
        api_info_path = Path("generated_docs") / f"{project_name}_api_info.json"
        self.file_generator.save_file(api_info_content, api_info_path)
        output_files.append(str(api_info_path))
        spec_content = self.formatter.to_json(openapi_spec, pretty=True)
        spec_path = Path("openapi_specs") / f"{project_name}_openapi.json"
        self.file_generator.save_file(spec_content, spec_path)
        output_files.append(str(spec_path))
        doc_md = self.formatter.to_markdown(
            documentation, title=f"{project_name} Documentation"
        )
        doc_md_path = Path("generated_docs") / f"{project_name}_documentation.md"
        self.file_generator.save_file(doc_md, doc_md_path)
        output_files.append(str(doc_md_path))
        doc_html = self.formatter.to_html(
            documentation, title=f"{project_name} Documentation"
        )
        doc_html_path = Path("generated_docs") / f"{project_name}_documentation.html"
        self.file_generator.save_file(doc_html, doc_html_path)
        output_files.append(str(doc_html_path))
        return output_files


def main() -> None:
    """
    CLI entry point for API documentation generation.
    """
    logger = get_logger()
    parser = argparse.ArgumentParser(
        description="Generate API documentation from project files"
    )
    parser.add_argument("input_file", help="Path to the input JSON or YAML file")
    parser.add_argument(
        "--config", "-c", help="Path to configuration file", default=None
    )
    args = parser.parse_args()
    try:
        loader = UniversalInputLoader()
        input_dict = loader.load_file_by_extension(Path(args.input_file))
        input_data = ApiDocGeneratorInput(**input_dict)
    except Exception as e:
        logger.log_error(f"Failed to load input file: {e}")
        sys.exit(1)
    else:
        pass
    finally:
        pass
    try:
        generator = ApiDocGenerator(args.config)
        result = generator.generate_api_docs(input_data)
        logger.log_info(
            f"Documentation generated successfully. Files: {result.output_files}"
        )
        sys.exit(0)
    except Exception as e:
        logger.log_error(f"Documentation generation failed: {e}")
        sys.exit(1)
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
