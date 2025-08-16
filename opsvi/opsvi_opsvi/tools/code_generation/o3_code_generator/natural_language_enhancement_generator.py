"""Natural Language Enhancement Generator module for dual-mode code generation requests."""

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    setup_logger,
)

setup_logger(LogConfig())
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from schemas.input_schema import CodeGenerationInput
from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger
from src.tools.code_generation.o3_code_generator.utils.directory_manager import (
    DirectoryManager,
)
from src.tools.code_generation.o3_code_generator.utils.file_generator import (
    FileGenerator,
)
from src.tools.code_generation.o3_code_generator.utils.output_formatter import (
    OutputFormatter,
)


class NaturalLanguageEnhancementGenerator:
    """
    Main class orchestrating the natural language enhancement and new code generation workflow.
    """

    def __init__(self) -> None:
        """
        Initialize utilities and logger.
        """
        self.logger = get_logger()
        self.directory_manager = DirectoryManager()
        self.file_generator = FileGenerator()
        self.formatter = OutputFormatter()

    def parse_arguments(self) -> argparse.Namespace:
        """
        Parse command line arguments for prompt and mode.

        Returns:
            argparse.Namespace: Parsed arguments with 'prompt' and 'mode' attributes.
        """
        parser = argparse.ArgumentParser(
            description="Natural Language Enhancement Generator"
        )
        parser.add_argument(
            "prompt", type=str, help="The natural language prompt for code generation"
        )
        parser.add_argument(
            "--mode",
            type=str,
            choices=["enhancement", "new_code"],
            default="enhancement",
            help='Mode of operation: "enhancement" or "new_code"',
        )
        return parser.parse_args()

    def validate_and_process_prompt(self, prompt: str, mode: str) -> dict[str, str]:
        """
        Validate and process the prompt based on the mode.

        Args:
            prompt (str): The raw input prompt.
            mode (str): The operational mode ('enhancement' or 'new_code').

        Returns:
            dict[str, str]: Processed data containing 'description' and 'target_file'.

        Raises:
            ValueError: If validation fails.
        """
        if mode == "enhancement":
            if " to " not in prompt:
                self.logger.log_error(
                    "Enhancement mode requires a 'to' keyword for target file."
                )
                raise ValueError(
                    "Enhancement mode requires a 'to' keyword for target file."
                )
            else:
                pass
            description, target_file = prompt.split(" to ", 1)
            description, target_file = (description.strip(), target_file.strip())
            if not description or not target_file or (not target_file.endswith(".py")):
                self.logger.log_error(
                    "Invalid format. Expected '<description> to <target_file.py>'."
                )
                raise ValueError(
                    "Invalid format. Expected '<description> to <target_file.py>'."
                )
            else:
                pass
            return {"description": description, "target_file": target_file}
        else:
            pass
        if mode == "new_code":
            if not prompt.strip():
                self.logger.log_error("Prompt cannot be empty in new_code mode.")
                raise ValueError("Prompt cannot be empty in new_code mode.")
            else:
                pass
            return {"description": prompt.strip(), "target_file": ""}
        else:
            pass
        self.logger.log_error(f"Invalid mode: {mode}")
        raise ValueError(f"Invalid mode: {mode}")

    def determine_output_path(self, mode: str) -> Path:
        """
        Determine and ensure the output directory based on the mode.

        Args:
            mode (str): The operational mode.

        Returns:
            Path: The directory path for output files.

        Raises:
            ValueError: If mode is invalid.
            Exception: If directory creation fails.
        """
        if mode == "enhancement":
            output_dir = Path.cwd() / "self_improvement"
            try:
                self.directory_manager.ensure_directory_exists(output_dir)
            except Exception as e:
                self.logger.log_error(f"Failed to create directory {output_dir}: {e}")
                raise
            else:
                pass
            finally:
                pass
            return output_dir
        else:
            pass
        if mode == "new_code":
            return Path.cwd()
        else:
            pass
        self.logger.log_error(f"Invalid mode: {mode}")
        raise ValueError(f"Invalid mode: {mode}")

    def generate_output_filename(self, mode: str) -> str:
        """
        Generate an output filename based on mode and timestamp.

        Args:
            mode (str): The operational mode.

        Returns:
            str: Generated filename.

        Raises:
            ValueError: If mode is invalid.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if mode == "enhancement":
            return f"enhancement_request_{timestamp}.json"
        else:
            pass
        if mode == "new_code":
            return f"code_generation_request_{timestamp}.json"
        else:
            pass
        self.logger.log_error(f"Invalid mode: {mode}")
        raise ValueError(f"Invalid mode: {mode}")

    def create_output_data(
        self, processed_data: dict[str, str], mode: str, output_dir: Path
    ) -> dict[str, Any]:
        """
        Build and validate output data conforming to CodeGenerationInput schema.

        Args:
            processed_data (dict[str, str]): Contains 'description' and 'target_file'.
            mode (str): Operational mode.
            output_dir (Path): Directory where outputs will be placed.

        Returns:
            dict[str, Any]: Validated data ready for serialization.

        Raises:
            Exception: If schema validation fails.
        """
        model_used = "o3-mini"
        if mode == "enhancement":
            file_name = processed_data["target_file"]
            context_files = [processed_data["target_file"]]
        else:
            file_name = None
            context_files: list[str] = []
        try:
            code_gen_input = CodeGenerationInput(
                prompt=processed_data["description"],
                model=model_used,
                file_name=file_name,
                file_path=str(output_dir),
                language="python",
                context_files=context_files,
                variables={},
                requirements=[],
                style_guide="",
                additional_context="",
            )
            return code_gen_input.dict()
        except Exception as e:
            self.logger.log_error(f"Error validating CodeGenerationInput: {e}")
            raise
        else:
            pass
        finally:
            pass

    def write_output_file(
        self, output_dir: Path, filename: str, data: dict[str, Any]
    ) -> None:
        """
        Serialize data to JSON and save to a file via FileGenerator.

        Args:
            output_dir (Path): Directory path for the file.
            filename (str): Name of the output file.
            data (dict[str, Any]): Data to serialize.

        Raises:
            Exception: If file saving fails.
        """
        file_path = output_dir / filename
        try:
            content = self.formatter.to_json(data, pretty=True)
            self.file_generator.save_file(content, file_path)
            self.logger.log_info(f"Successfully wrote output to {file_path}")
        except Exception as e:
            self.logger.log_error(f"Failed to write output file: {e}")
            raise
        else:
            pass
        finally:
            pass

    def run(self) -> None:
        """
        Execute the end-to-end generation pipeline.
        """
        try:
            args = self.parse_arguments()
            self.logger.log_info(f"Running in {args.mode} mode")
            processed = self.validate_and_process_prompt(args.prompt, args.mode)
            out_dir = self.determine_output_path(args.mode)
            out_data = self.create_output_data(processed, args.mode, out_dir)
            out_file = self.generate_output_filename(args.mode)
            self.write_output_file(out_dir, out_file, out_data)
        except Exception as e:
            self.logger.log_error(f"An unexpected error occurred: {e}")
            sys.exit(1)
        else:
            pass
        finally:
            pass


if __name__ == "__main__":
    generator = NaturalLanguageEnhancementGenerator()
    generator.run()
else:
    pass
