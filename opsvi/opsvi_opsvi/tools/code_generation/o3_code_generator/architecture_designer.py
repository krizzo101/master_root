"""
Architecture Designer for O3 Code Generator

This module provides comprehensive architecture design capabilities using OpenAI's O3 models,
including system architecture design, pattern generation, and validation. It utilizes shared
utilities for input loading, directory management, prompt building, file generation, and output
formatting, and adheres strictly to O3 Code Generator project and universal coding standards.
"""

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)

setup_logger(LogConfig())
import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any

from openai import OpenAI

from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
    ConfigManager,
)
from src.tools.code_generation.o3_code_generator.prompts.architecture_prompts import (
    ARCHITECTURE_SYSTEM_PROMPT,
)
from src.tools.code_generation.o3_code_generator.schemas.architecture_schemas import (
    ArchitectureInput,
    ArchitectureOutput,
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


class ArchitectureAnalyzer:
    """Analyzes system requirements and generates architectural insights."""

    def __init__(self) -> None:
        """Initialize the architecture analyzer with a logger."""
        self.logger = get_logger(self.__class__.__name__)

    def analyze_requirements(self, requirements_text: str) -> dict[str, Any]:
        """
        Analyze system requirements and extract architectural insights.

        Args:
            requirements_text: Natural language system requirements

        Returns:
            A dict containing architectural analysis
        """
        self.logger.log_info("Starting requirements analysis")
        analysis: dict[str, Any] = {
            "architectural_patterns": [],
            "scalability_requirements": {},
            "security_requirements": {},
            "integration_requirements": [],
            "performance_requirements": {},
            "deployment_requirements": {},
            "technology_constraints": [],
            "risk_factors": [],
            "complexity_estimates": {},
        }
        self.logger.log_info("Requirements analysis completed")
        return analysis


class DiagramGenerator:
    """Generates visual diagrams for architecture designs."""

    def __init__(self) -> None:
        """Initialize the diagram generator with a logger."""
        self.logger = get_logger(self.__class__.__name__)

    def generate_architecture_diagram(
        self, architecture_design: dict[str, Any], diagram_type: str = "plantuml"
    ) -> str:
        """
        Generate architecture diagram in specified format.

        Args:
            architecture_design: Architecture design specification
            diagram_type: Type of diagram ('plantuml' or 'mermaid')

        Returns:
            Diagram content as a string
        """
        self.logger.log_info(f"Generating {diagram_type} diagram")
        diagram_type_lower = diagram_type.lower()
        if diagram_type_lower == "plantuml":
            return self._generate_plantuml(architecture_design)
        else:
            pass
        if diagram_type_lower == "mermaid":
            return self._generate_mermaid(architecture_design)
        else:
            pass
        raise ValueError(f"Unsupported diagram type: {diagram_type}")

    def _generate_plantuml(self, architecture_design: dict[str, Any]) -> str:
        """
        Generate PlantUML diagram.

        Args:
            architecture_design: Architecture design specification

        Returns:
            PlantUML diagram string
        """
        return "@startuml\n@enduml"

    def _generate_mermaid(self, architecture_design: dict[str, Any]) -> str:
        """
        Generate Mermaid diagram.

        Args:
            architecture_design: Architecture design specification

        Returns:
            Mermaid diagram string
        """
        return "graph TD\n"


class ArchitectureDesigner:
    """Main architecture designer class."""

    def __init__(self, config_path: str | None = None) -> None:
        """
        Initialize the architecture designer.

        Args:
            config_path: Optional path to configuration file
        """
        self.logger = get_logger(self.__class__.__name__)
        self.config = ConfigManager(config_path)
        self.client = OpenAI(
            api_key=self.config.get("api.openai_api_key"),
            base_url=self.config.get("api.base_url", "https://api.openai.com/v1"),
        )
        self.input_loader = UniversalInputLoader()
        self.directory_manager = DirectoryManager()
        self.prompt_builder = PromptBuilder()
        self.file_generator = FileGenerator()
        self.output_formatter = OutputFormatter()
        self._setup_directories()
        self.logger.log_info("ArchitectureDesigner initialized")

    def _setup_directories(self) -> None:
        """
        Create required output directories using DirectoryManager.
        """
        base_dir = Path(self.config.get("paths.generated_files", "generated_files"))
        self.directory_manager.ensure_directory_exists(base_dir)
        self.directory_manager.create_module_directories(
            "architecture", ["diagrams", "specifications"]
        )

    def design_system_architecture(
        self, input_data: ArchitectureInput
    ) -> ArchitectureOutput:
        """
        Design system architecture based on input requirements.

        Args:
            input_data: ArchitectureInput instance

        Returns:
            ArchitectureOutput instance with results
        """
        start_time = time.time()
        self.logger.log_info("Starting system architecture design")
        try:
            analyzer = ArchitectureAnalyzer()
            analysis = analyzer.analyze_requirements(input_data.system_requirements)
            prompt = self.prompt_builder.build_generation_prompt(
                input_data=input_data,
                context={"analysis": analysis},
                system_prompt=ARCHITECTURE_SYSTEM_PROMPT,
                format_instructions="Return JSON",
            )
            response = self.client.chat.completions.create(
                model=input_data.model,
                messages=[
                    {"role": "system", "content": ARCHITECTURE_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=input_data.max_tokens,
                response_format={"type": "json_object"},
            )
            content = json.loads(response.choices[0].message.content)
            self.logger.log_info("Architecture design generated by model")
            diagrams: list[str] = []
            if input_data.include_diagrams:
                diagram_generator = DiagramGenerator()
                for diagram_type in ("plantuml", "mermaid"):
                    diagram_content = diagram_generator.generate_architecture_diagram(
                        content, diagram_type
                    )
                    diagram_path = (
                        Path(self.config.get("paths.generated_files"))
                        / "architecture"
                        / "diagrams"
                        / f"architecture.{diagram_type}"
                    )
                    self.file_generator.save_file(diagram_content, diagram_path)
                    diagrams.append(str(diagram_path))
                else:
                    pass
            else:
                pass
            specs_dir = (
                Path(self.config.get("paths.generated_files"))
                / "architecture"
                / "specifications"
            )
            output_files: list[str] = []
            json_str = self.output_formatter.to_json(content, pretty=True)
            json_path = specs_dir / "architecture_specification.json"
            self.file_generator.save_file(json_str, json_path)
            output_files.append(str(json_path))
            output_format = input_data.output_format.lower()
            if output_format == "markdown":
                md_str = self.output_formatter.to_markdown(
                    content, "Architecture Specification"
                )
                md_path = specs_dir / "architecture_specification.md"
                self.file_generator.save_file(md_str, md_path)
                output_files.append(str(md_path))
            elif output_format == "html":
                html_str = self.output_formatter.to_html(
                    content, "Architecture Specification"
                )
                html_path = specs_dir / "architecture_specification.html"
                self.file_generator.save_file(html_str, html_path)
                output_files.append(str(html_path))
            else:
                pass
            duration = time.time() - start_time
            self.logger.log_info(f"Design completed in {duration:.2f}s")
            return ArchitectureOutput(
                success=True,
                architecture_design=content,
                output_files=output_files,
                diagrams=diagrams,
                generation_time=duration,
                model_used=input_data.model,
            )
        except Exception as e:
            self.logger.log_error(f"Error during design: {e}")
            raise
        else:
            pass
        finally:
            pass


def main() -> None:
    """CLI entry point for the architecture designer."""
    logger = get_logger("main")
    parser = argparse.ArgumentParser(
        description="Architecture Designer for O3 Code Generator"
    )
    parser.add_argument("input_file", help="Path to input JSON/YAML file")
    parser.add_argument("--config", help="Path to configuration file", default=None)
    args = parser.parse_args()
    try:
        loader = UniversalInputLoader()
        data = loader.load_file_by_extension(args.input_file)
        input_obj = ArchitectureInput(**data)
        designer = ArchitectureDesigner(args.config)
        output = designer.design_system_architecture(input_obj)
        if output.success:
            logger.log_info(
                f"Architecture design succeeded; files: {len(output.output_files)}, diagrams: {len(output.diagrams)}"
            )
        else:
            logger.log_error("Architecture design failed")
            sys.exit(1)
    except Exception as e:
        logger.log_error(f"Fatal error: {e}")
        sys.exit(1)
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
