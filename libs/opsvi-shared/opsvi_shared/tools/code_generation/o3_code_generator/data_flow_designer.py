"""Data Flow Designer for O3 Code Generator

This module provides comprehensive data flow design capabilities using OpenAI's O3 models,
including data flow analysis, data model definition, integration specification, and file/diagram generation.
"""

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    setup_logger,
)

setup_logger(LogConfig())
import argparse
import json
from pathlib import Path
import time
from typing import Any

from openai import OpenAI

from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
    ConfigManager,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger
from src.tools.code_generation.o3_code_generator.prompts.architecture_prompts import (
    DATA_FLOW_SYSTEM_PROMPT,
)
from src.tools.code_generation.o3_code_generator.schemas.architecture_schemas import (
    DataFlowInput,
    DataFlowOutput,
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


class DataFlowAnalyzer:
    """Performs analysis of data flow requirements to identify dependencies and design insights."""

    def __init__(self) -> None:
        """Initialize the data flow analyzer and its logger."""
        self.logger = get_logger(__name__)

    def analyze_data_requirements(
        self, data_requirements: str, system_architecture: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze data flow requirements and extract design insights.

        Args:
            data_requirements: Raw textual requirements describing data flows.
            system_architecture: Contextual system architecture details.

        Returns:
            A dictionary containing extracted analysis insights.
        """
        self.logger.log_info("Starting data flow requirements analysis")
        text = data_requirements.lower()
        analysis: dict[str, Any] = {
            "data_sources": self._extract_data_sources(text),
            "data_destinations": self._extract_data_destinations(text),
            "data_transformations": self._extract_data_transformations(text),
            "data_volume_characteristics": self._analyze_data_volume(text),
            "data_velocity_characteristics": self._analyze_data_velocity(text),
            "data_variety_characteristics": self._analyze_data_variety(text),
            "integration_patterns": self._extract_integration_patterns(text),
            "data_quality_requirements": self._extract_data_quality_requirements(text),
            "data_security_requirements": self._extract_data_security_requirements(
                text
            ),
        }
        self.logger.log_info("Data flow requirements analysis completed")
        return analysis

    def _extract_data_sources(self, text: str) -> list[dict[str, Any]]:
        """Extract data sources from requirements."""
        sources: list[dict[str, Any]] = []
        if any(token in text for token in ("database", "sql", "nosql")):
            sources.append(
                {"type": "database", "name": "Primary Database", "format": "structured"}
            )
        else:
            pass
        if any(token in text for token in ("file", "csv", "json", "xml")):
            sources.append(
                {"type": "file", "name": "File System", "format": "semi-structured"}
            )
        else:
            pass
        if any(token in text for token in ("api", "rest", "graphql")):
            sources.append(
                {"type": "api", "name": "External API", "format": "structured"}
            )
        else:
            pass
        if any(token in text for token in ("message", "queue", "kafka")):
            sources.append(
                {
                    "type": "message_queue",
                    "name": "Message Queue",
                    "format": "streaming",
                }
            )
        else:
            pass
        return sources

    def _extract_data_destinations(self, text: str) -> list[dict[str, Any]]:
        """Extract data destinations from requirements."""
        destinations: list[dict[str, Any]] = []
        if any(token in text for token in ("warehouse", "analytics", "reporting")):
            destinations.append(
                {
                    "type": "data_warehouse",
                    "name": "Analytics Warehouse",
                    "purpose": "analytics",
                }
            )
        else:
            pass
        if any(token in text for token in ("lake", "storage", "archive")):
            destinations.append(
                {"type": "data_lake", "name": "Data Lake", "purpose": "storage"}
            )
        else:
            pass
        if any(token in text for token in ("cache", "redis", "memory")):
            destinations.append(
                {"type": "cache", "name": "Cache Store", "purpose": "performance"}
            )
        else:
            pass
        return destinations

    def _extract_data_transformations(self, text: str) -> list[dict[str, Any]]:
        """Extract data transformation requirements."""
        transformations: list[dict[str, Any]] = []
        if any(token in text for token in ("etl", "extract", "transform", "load")):
            transformations.append(
                {"type": "etl", "name": "ETL Pipeline", "complexity": "medium"}
            )
        else:
            pass
        if any(token in text for token in ("aggregation", "summarize", "group")):
            transformations.append(
                {"type": "aggregation", "name": "Data Aggregation", "complexity": "low"}
            )
        else:
            pass
        if any(token in text for token in ("enrichment", "join", "merge")):
            transformations.append(
                {
                    "type": "enrichment",
                    "name": "Data Enrichment",
                    "complexity": "medium",
                }
            )
        else:
            pass
        return transformations

    def _analyze_data_volume(self, text: str) -> dict[str, Any]:
        """Analyze data volume characteristics."""
        volume: dict[str, Any] = {
            "level": "medium",
            "scaling": "horizontal",
            "storage": "distributed",
        }
        if any(token in text for token in ("big data", "massive", "terabytes")):
            volume.update({"level": "massive", "scaling": "distributed"})
        else:
            pass
        return volume

    def _analyze_data_velocity(self, text: str) -> dict[str, Any]:
        """Analyze data velocity characteristics."""
        velocity: dict[str, Any] = {
            "type": "batch",
            "frequency": "daily",
            "latency": "hours",
        }
        if any(token in text for token in ("real-time", "streaming", "instant")):
            velocity.update({"type": "real-time", "latency": "milliseconds"})
        else:
            pass
        return velocity

    def _analyze_data_variety(self, text: str) -> dict[str, Any]:
        """Analyze data variety characteristics."""
        variety: dict[str, Any] = {
            "types": ["structured"],
            "formats": ["json"],
            "schemas": ["fixed"],
        }
        if any(token in text for token in ("unstructured", "text", "image")):
            variety["types"].append("unstructured")
        else:
            pass
        return variety

    def _extract_integration_patterns(self, text: str) -> list[str]:
        """Extract integration patterns from requirements."""
        patterns: list[str] = []
        if any(token in text for token in ("etl", "batch")):
            patterns.append("etl")
        else:
            pass
        if any(token in text for token in ("streaming", "real-time")):
            patterns.append("streaming")
        else:
            pass
        if any(token in text for token in ("event", "message")):
            patterns.append("event-driven")
        else:
            pass
        return patterns

    def _extract_data_quality_requirements(self, text: str) -> dict[str, Any]:
        """Extract data quality requirements."""
        quality: dict[str, Any] = {
            "validation": "basic",
            "cleansing": False,
            "monitoring": False,
        }
        if any(token in text for token in ("quality", "validation", "clean")):
            quality.update({"validation": "comprehensive", "cleansing": True})
        else:
            pass
        return quality

    def _extract_data_security_requirements(self, text: str) -> dict[str, Any]:
        """Extract data security requirements."""
        security: dict[str, Any] = {
            "encryption": "transport",
            "access_control": "basic",
            "audit": False,
        }
        if any(token in text for token in ("secure", "encrypt", "privacy")):
            security.update({"encryption": "end-to-end", "access_control": "advanced"})
        else:
            pass
        return security


class DataFlowDesigner:
    """Facilitates the design and modeling of data flow architectures based on analysis results."""

    def __init__(self, config_path: str | None = None) -> None:
        """
        Initialize the data flow designer.

        Args:
            config_path: Optional path to a configuration file.
        """
        self.logger = get_logger(__name__)
        self.config = ConfigManager(config_path)
        self.client = OpenAI(
            api_key=self.config.get("api.openai_api_key"),
            base_url=self.config.get("api.base_url", "https://api.openai.com/v1"),
        )
        self.directory_manager = DirectoryManager()
        self.file_generator = FileGenerator()
        self.output_formatter = OutputFormatter()
        self.prompt_builder = PromptBuilder()
        self.analyzer = DataFlowAnalyzer()
        self._create_directories()
        self.logger.log_info("Data Flow Designer initialized successfully")

    def _create_directories(self) -> None:
        """Create necessary output directories."""
        base_path = Path(self.config.get("paths.generated_files", "generated_files"))
        self.directory_manager.ensure_directory_exists(base_path)
        self.directory_manager.create_module_directories(
            module_name=str(base_path / "data_flows"),
            additional_dirs=["diagrams", "specifications"],
        )

    def design_data_flows(self, input_data: DataFlowInput) -> DataFlowOutput:
        """
        Design comprehensive data flows based on requirements.

        Args:
            input_data: Structured input for data flow design.

        Returns:
            A DataFlowOutput containing specifications, files, and diagrams.
        """
        start_time = time.time()
        self.logger.log_info("Starting data flow design")
        try:
            analysis = self.analyzer.analyze_data_requirements(
                data_requirements=input_data.data_requirements,
                system_architecture=input_data.system_architecture,
            )
            prompt = self.prompt_builder.build_generation_prompt(
                input_data=input_data,
                context=analysis,
                system_prompt=DATA_FLOW_SYSTEM_PROMPT,
                format_instructions=None,
            )
            response = self.client.chat.completions.create(
                model=input_data.model,
                messages=[
                    {"role": "system", "content": DATA_FLOW_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=input_data.max_tokens,
                response_format={"type": "json_object"},
            )
            specs: dict[str, Any] = json.loads(response.choices[0].message.content)
            diagrams: list[str] = []
            if input_data.include_diagrams:
                diagrams = self._generate_diagrams(specs)
            else:
                pass
            output_files = self._create_data_flow_files(specs, input_data)
            generation_time = time.time() - start_time
            self.logger.log_info(
                f"Data flow design completed in {generation_time:.2f} seconds"
            )
            return DataFlowOutput(
                success=True,
                data_flow_specifications=specs,
                output_files=output_files,
                diagrams=diagrams,
                generation_time=generation_time,
                model_used=input_data.model,
            )
        except Exception as e:
            self.logger.log_error(f"Error during data flow design: {e}")
            raise e from e
        else:
            pass
        finally:
            pass

    def _generate_diagrams(self, specs: dict[str, Any]) -> list[str]:
        """
        Generate visual diagrams for the data flow design.

        Args:
            specs: The data flow specifications to visualize.

        Returns:
            A list of file paths to generated diagram files.
        """
        return self.file_generator.create_analysis_files(
            analysis_data=specs,
            module_name="data_flow_diagrams",
            title="Diagrams",
            formats=["puml", "mmd"],
        )

    def _create_data_flow_files(
        self, specs: dict[str, Any], input_data: DataFlowInput
    ) -> list[str]:
        """
        Create data flow specification files in requested formats.

        Args:
            specs: The data flow specifications.
            input_data: Original input specifying format preferences.

        Returns:
            A list of file paths to generated specification files.
        """
        files: list[str] = []
        base = (
            Path(self.config.get("paths.generated_files", "generated_files"))
            / "data_flows"
            / "specifications"
        )
        self.directory_manager.ensure_directory_exists(base)
        json_content = self.output_formatter.to_json(data=specs, pretty=True)
        json_path = base / "data_flow_specification.json"
        self.file_generator.save_file(content=json_content, file_path=json_path)
        files.append(str(json_path))
        if input_data.output_format.lower() == "markdown":
            md_content = self.output_formatter.to_markdown(
                data=specs, title="Data Flow Specifications"
            )
            md_path = base / "data_flow_specification.md"
            self.file_generator.save_file(content=md_content, file_path=md_path)
            files.append(str(md_path))
        else:
            pass
        self.logger.log_info(f"Created {len(files)} data flow specification files")
        return files


def main() -> None:
    """Entry point for command-line usage."""
    logger = get_logger(__name__)
    parser = argparse.ArgumentParser(
        description="Data Flow Designer for O3 Code Generator"
    )
    parser.add_argument("input_file", help="Path to input JSON file")
    parser.add_argument("--config", help="Path to configuration file", default=None)
    args = parser.parse_args()
    try:
        loader = UniversalInputLoader()
        input_dict = loader.load_json_file(Path(args.input_file))
        input_data = DataFlowInput(**input_dict)
        designer = DataFlowDesigner(config_path=args.config)
        output = designer.design_data_flows(input_data)
        logger.log_info(
            f"Data flow design succeeded: {len(output.output_files)} files, {len(output.diagrams)} diagrams"
        )
    except Exception as e:
        logger.log_error(f"Data flow design failed: {e}")
        raise e from e
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
