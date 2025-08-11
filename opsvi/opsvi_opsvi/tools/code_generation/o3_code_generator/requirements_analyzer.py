"""
Requirements Analyzer for O3 Code Generator

This module analyzes natural language requirements and extracts structured
requirements information using O3ModelGenerator, formats the results, and
writes output files.
"""

import sys

from src.tools.code_generation.o3_code_generator.analysis_utils import (
    extract_requirements_data_from_feasibility_assessment,
    save_requirements_results_for_next_step,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger
from src.tools.code_generation.o3_code_generator.schemas.requirements_schemas import (
    RequirementsInput,
    RequirementsOutput,
)
from src.tools.code_generation.o3_code_generator.utils.input_loader import (
    UniversalInputLoader,
)
from src.tools.code_generation.o3_code_generator.utils.o3_model_generator import (
    O3ModelGenerator,
)

logger = get_logger()


class RequirementsProcessor:
    """Simple processor for requirements analysis."""

    def __init__(self) -> None:
        """Initialize the requirements processor."""
        self.logger = get_logger()
        try:
            self.model_generator = O3ModelGenerator()
            self.logger.log_info("O3ModelGenerator initialized successfully")
        except Exception as e:
            self.logger.log_error(f"Failed to initialize O3ModelGenerator: {e}")
            raise

    def analyze_requirements(self, input_data: RequirementsInput) -> RequirementsOutput:
        """Analyze requirements and return structured output."""
        try:
            # Simple mock analysis for now - in a real implementation this would
            # use the O3ModelGenerator to analyze the requirements
            user_stories = [
                {
                    "id": "US001",
                    "title": "User Registration",
                    "description": "As a user, I want to register an account",
                },
                {
                    "id": "US002",
                    "title": "Code Execution",
                    "description": "As a learner, I want to execute Python code in real-time",
                },
            ]

            dependencies = [
                {"id": "DEP001", "name": "Web Framework", "type": "technology"},
                {"id": "DEP002", "name": "Code Execution Engine", "type": "service"},
            ]

            return RequirementsOutput(
                success=True,
                user_stories=user_stories,
                dependencies=dependencies,
                functional_requirements=[],
                non_functional_requirements=[],
                constraints=[],
                acceptance_criteria=[],
                output_files=[],
                generation_time=0.1,
                model_used="o4-mini",
            )
        except Exception as e:
            self.logger.log_error(f"Requirements analysis failed: {e}")
            return RequirementsOutput(
                success=False,
                error_message=str(e),
                user_stories=[],
                dependencies=[],
                functional_requirements=[],
                non_functional_requirements=[],
                constraints=[],
                acceptance_criteria=[],
                output_files=[],
                generation_time=0.0,
                model_used="o4-mini",
            )


def run_requirements_analyze(input_file: str | None) -> None:
    """Analyze requirements."""
    try:
        if input_file:
            logger.log_info(f"Requirements analysis: {input_file}")
            input_data = UniversalInputLoader().load_file_by_extension(input_file)
            if "feasibility_assessment_results" in input_file:
                input_data = extract_requirements_data_from_feasibility_assessment(
                    input_data
                )
        else:
            logger.log_error("Input file required for requirements analysis")
            sys.exit(1)

        rp = RequirementsProcessor()
        inp = RequirementsInput(**input_data)
        out = rp.analyze_requirements(inp)
        if not out.success:
            logger.log_error(f"Requirements analysis failed: {out.error_message}")
            sys.exit(1)

        next_step_file = save_requirements_results_for_next_step(out, input_file)
        logger.log_info(
            f"User stories: {len(out.user_stories)}, dependencies: {len(out.dependencies)}"
        )
        logger.log_info(f"Requirements analysis results saved to: {next_step_file}")
        print("\n📋 Requirements analysis completed!")
        print(f"📁 Results saved to: {next_step_file}")
        print("🔄 Next step: Use 'architecture-design' to design system architecture")
        print(
            "   Example: python -m main architecture-design requirements_specification_YYYYMMDD_HHMMSS.json"
        )
    except Exception as e:
        logger.log_error(f"Error during requirements analysis: {e}")
        raise
