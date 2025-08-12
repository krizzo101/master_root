"""
Module Name: base_processor.py

Purpose: Centralized processing workflow for O3 Code Generator modules.

This module provides standardized processing workflows for analysis and generation,
integrating directory management, input loading, prompt building, model generation,
output formatting, and file generation. It includes methods for loading and validating
input, generating analysis and generation outputs, creating summary reports, and
cleaning up old files. All operations are logged using O3Logger.

Usage:
    from src.tools.code_generation.o3_code_generator.utils.base_processor import BaseProcessor

    processor = BaseProcessor(config_manager, module_name="my_module")
    analysis_result = processor.process_analysis(input_data, system_prompt, output_schema, "My Analysis")
    generation_result = processor.process_generation(input_data, system_prompt, "My Generation")

Author: O3 Code Generator
Version: 1.0.1
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger
from src.tools.code_generation.o3_code_generator.utils.directory_manager import (
    DirectoryManager,
)
from src.tools.code_generation.o3_code_generator.utils.file_generator import (
    FileGenerator,
)
from src.tools.code_generation.o3_code_generator.utils.input_loader import (
    UniversalInputLoader,
)
from src.tools.code_generation.o3_code_generator.utils.o3_model_generator import (
    O3ModelGenerator,
)
from src.tools.code_generation.o3_code_generator.utils.output_formatter import (
    OutputFormatter,
)
from src.tools.code_generation.o3_code_generator.utils.prompt_builder import (
    PromptBuilder,
)


class BaseProcessor:
    """
    Comprehensive class for centralized processing workflows in the O3 Code Generator.

    Attributes:
        config_manager: Configuration manager instance.
        logger: O3Logger instance.
        module_name: Name of the current module for directory management.
        directory_manager: DirectoryManager instance for filesystem operations.
        input_loader: UniversalInputLoader instance for loading input files.
        prompt_builder: PromptBuilder instance for constructing prompts.
        o3_model_generator: O3ModelGenerator instance for interacting with models.
        output_formatter: OutputFormatter instance for formatting outputs.
        file_generator: FileGenerator instance for file creation.
    """

    def __init__(
        self, config_manager: Any, module_name: str = "base_processor"
    ) -> None:
        """
        Initialize BaseProcessor.

        Args:
            config_manager: Configuration manager instance.
            module_name: Name of the module for directory management.
        """
        self.config_manager = config_manager
        self.module_name = module_name
        self.logger = get_logger()
        self.logger.log_info(
            f"Initializing BaseProcessor for module '{self.module_name}'"
        )
        self.directory_manager = DirectoryManager()
        self.input_loader = UniversalInputLoader()
        self.prompt_builder = PromptBuilder()
        self.o3_model_generator = O3ModelGenerator(self.config_manager)
        self.output_formatter = OutputFormatter()
        self.file_generator = FileGenerator(self.output_formatter)
        try:
            self.directory_manager.create_module_directories(self.module_name)
        except Exception as e:
            self.logger.log_error(
                f"Error initializing directories for module '{self.module_name}': {e}"
            )
            raise
        else:
            pass
        finally:
            pass

    def process_analysis(
        self,
        input_data: Any,
        system_prompt: str,
        output_schema: Any,
        title: str,
        instructions: str | None = None,
        context_files: list[str] | None = None,
        output_formats: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Process analysis with standardized workflow.

        Args:
            input_data: Input data object containing analysis parameters.
            system_prompt: System prompt for the analysis.
            output_schema: Pydantic schema for structured output.
            title: Title for the analysis and output files.
            instructions: Optional additional instructions.
            context_files: Optional list of context file paths.
            output_formats: Optional list of output formats. Defaults to ['json', 'markdown', 'html'].

        Returns:
            Dictionary containing the analysis results and file paths.

        Raises:
            ValueError: If required parameters are missing or invalid.
            Exception: If processing fails.
        """
        if input_data is None:
            raise ValueError("Input data cannot be None")
        else:
            pass
        if not system_prompt.strip():
            raise ValueError("System prompt cannot be empty")
        else:
            pass
        if not title.strip():
            raise ValueError("Title cannot be empty")
        else:
            pass
        try:
            self.logger.log_info(f"Starting analysis processing for '{title}'")
            analysis_context = self._prepare_analysis_context(input_data)
            prompt = self.prompt_builder.build_analysis_prompt(
                input_data, analysis_context, system_prompt, instructions
            )
            if context_files:
                context_text = self._load_context_files(context_files)
                prompt = f"{prompt}\n\n{context_text}"
            else:
                pass
            result = self.o3_model_generator.generate_structured_output(
                input_data=input_data, prompt=prompt, output_schema=output_schema
            )
            formats = output_formats or ["json", "markdown", "html"]
            file_paths = self.file_generator.create_analysis_files(
                analysis_data=result,
                module_name=self.module_name,
                title=title,
                formats=formats,
            )
            final_result: dict[str, Any] = {
                "analysis_result": result,
                "file_paths": file_paths,
                "processing_info": {
                    "module_name": self.module_name,
                    "title": title,
                    "output_formats": formats,
                    "context_files_count": len(context_files or []),
                },
            }
            self.logger.log_info(f"Completed analysis processing for '{title}'")
            return final_result
        except Exception as e:
            self.logger.log_error(f"Unexpected error in process_analysis: {e}")
            raise
        else:
            pass
        finally:
            pass

    def process_generation(
        self,
        input_data: Any,
        system_prompt: str,
        title: str,
        context: dict[str, Any] | None = None,
        format_instructions: str | None = None,
        context_files: list[str] | None = None,
        output_formats: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Process code generation with standardized workflow.

        Args:
            input_data: Input data object containing generation parameters.
            system_prompt: System prompt for the generation.
            title: Title for the generation and output files.
            context: Optional context dictionary for generation.
            format_instructions: Optional format instructions.
            context_files: Optional list of context file paths.
            output_formats: Optional list of output formats. Defaults to ['json', 'markdown'].

        Returns:
            Dictionary containing the generation results and file paths.

        Raises:
            ValueError: If required parameters are missing or invalid.
            Exception: If processing fails.
        """
        if input_data is None:
            raise ValueError("Input data cannot be None")
        else:
            pass
        if not system_prompt.strip():
            raise ValueError("System prompt cannot be empty")
        else:
            pass
        if not title.strip():
            raise ValueError("Title cannot be empty")
        else:
            pass
        try:
            self.logger.log_info(f"Starting generation processing for '{title}'")
            prompt = self.prompt_builder.build_generation_prompt(
                input_data, context, system_prompt, format_instructions
            )
            if context_files:
                context_text = self._load_context_files(context_files)
                prompt = f"{prompt}\n\n{context_text}"
            else:
                pass
            generated_text = self.o3_model_generator.generate_text_output(prompt=prompt)
            params = (
                input_data.dict() if hasattr(input_data, "dict") else str(input_data)
            )
            result_data: dict[str, Any] = {
                "generated_content": generated_text,
                "input_parameters": params,
                "context": context or {},
                "format_instructions": format_instructions,
            }
            formats = output_formats or ["json", "markdown"]
            file_paths = self.file_generator.create_analysis_files(
                analysis_data=result_data,
                module_name=self.module_name,
                title=title,
                formats=formats,
            )
            final_result: dict[str, Any] = {
                "generation_result": result_data,
                "file_paths": file_paths,
                "processing_info": {
                    "module_name": self.module_name,
                    "title": title,
                    "output_formats": formats,
                    "context_files_count": len(context_files or []),
                },
            }
            self.logger.log_info(f"Completed generation processing for '{title}'")
            return final_result
        except Exception as e:
            self.logger.log_error(f"Unexpected error in process_generation: {e}")
            raise
        else:
            pass
        finally:
            pass

    def load_and_validate_input(
        self, file_path: str | Path, required_fields: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Load and validate input file.

        Args:
            file_path: Path to the input file.
            required_fields: Optional list of required fields to validate.

        Returns:
            Dictionary containing the loaded data.

        Raises:
            ValueError: If file loading or validation fails.
            Exception: If unexpected errors occur.
        """
        try:
            data = self.input_loader.load_file_by_extension(file_path)
            if required_fields:
                missing = [f for f in required_fields if f not in data]
                if missing:
                    msg = f"Missing required fields: {missing}"
                    self.logger.log_error(msg)
                    raise ValueError(msg)
                else:
                    pass
            else:
                pass
            self.logger.log_info("Successfully loaded and validated input data")
            return data
        except ValueError:
            raise
        except Exception as e:
            self.logger.log_error(f"Unexpected error in load_and_validate_input: {e}")
            raise
        else:
            pass
        finally:
            pass

    def create_summary_report(self, data: dict[str, Any], title: str) -> str:
        """
        Create a summary report in markdown format.

        Args:
            data: Data to include in the summary report.
            title: Title for the report.

        Returns:
            Markdown formatted summary report.

        Raises:
            ValueError: If data is not a dictionary or title is empty.
            Exception: If report generation fails.
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        else:
            pass
        if not title.strip():
            raise ValueError("Title cannot be empty")
        else:
            pass
        try:
            report = self.output_formatter.to_markdown(data, title)
            self.logger.log_info(f"Created summary report for '{title}'")
            return report
        except Exception as e:
            self.logger.log_error(f"Unexpected error in create_summary_report: {e}")
            raise
        else:
            pass
        finally:
            pass

    def cleanup_old_files(self, days_old: int = 30) -> None:
        """
        Clean up old files in the module's output directory.

        Args:
            days_old: Age threshold in days for file deletion.

        Raises:
            Exception: If cleanup operation fails.
        """
        try:
            output_dir = self.directory_manager.get_module_output_path(self.module_name)
            threshold = datetime.now() - timedelta(days=days_old)
            for item in Path(output_dir).iterdir():
                if item.is_file():
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if mtime < threshold:
                        try:
                            item.unlink()
                            self.logger.log_info(f"Deleted old file: {item}")
                        except Exception as e:
                            self.logger.log_error(f"Error deleting file {item}: {e}")
                        else:
                            pass
                        finally:
                            pass
                    else:
                        pass
                else:
                    pass
            else:
                pass
            self.logger.log_info(
                f"Cleanup completed for files older than {days_old} days"
            )
        except Exception as e:
            self.logger.log_error(f"Unexpected error in cleanup_old_files: {e}")
            raise
        else:
            pass
        finally:
            pass

    def _prepare_analysis_context(self, input_data: Any) -> dict[str, Any]:
        """
        Prepare analysis context from input data.

        Args:
            input_data: Input data object.

        Returns:
            Dictionary containing analysis context.

        Raises:
            Exception: If context preparation fails.
        """
        try:
            if hasattr(input_data, "dict"):
                input_dict = input_data.dict()
            elif hasattr(input_data, "__dict__"):
                input_dict = input_data.__dict__
            elif isinstance(input_data, dict):
                input_dict = input_data
            else:
                input_dict = {"data": input_data}
            context: dict[str, Any] = {
                "input_parameters": input_dict,
                "module_name": self.module_name,
                "processing_timestamp": datetime.now().isoformat(),
            }
            return context
        except Exception as e:
            self.logger.log_error(f"Unexpected error in _prepare_analysis_context: {e}")
            raise
        else:
            pass
        finally:
            pass

    def _load_context_files(self, file_paths: list[str]) -> str:
        """
        Load and concatenate context files for prompt inclusion.

        Args:
            file_paths: List of file paths to include.

        Returns:
            Concatenated content of all context files.

        Raises:
            Exception: If file reading fails.
        """
        contents: list[str] = []
        try:
            for path_str in file_paths:
                path = Path(path_str)
                text = path.read_text()
                contents.append(f"### Context from {path.name}\n\n{text}")
            else:
                pass
            return "\n\n".join(contents)
        except Exception as e:
            self.logger.log_error(f"Unexpected error in _load_context_files: {e}")
            raise
        else:
            pass
        finally:
            pass
