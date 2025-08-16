"""
Module to generate and save CodeGenerationInput JSON files for the self-improvement system.
"""

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    setup_logger,
)

setup_logger(LogConfig())
import argparse
from pathlib import Path
import sys

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


class IntegratedO3Analyzer:
    """
    Class to generate and save CodeGenerationInput JSON files using shared O3 utilities.

    Attributes:
        logger: O3Logger instance for logging.
        output_formatter: Instance of OutputFormatter for formatting data.
        file_generator: Instance of FileGenerator for writing files.
        directory_manager: Instance of DirectoryManager for directory operations.
    """

    def __init__(self) -> None:
        """
        Initialize the analyzer with logger, formatter, file generator, and directory manager.
        """
        self.logger = get_logger()
        self.output_formatter = OutputFormatter()
        self.file_generator = FileGenerator()
        self.directory_manager = DirectoryManager()

    @staticmethod
    def parse_arguments() -> argparse.Namespace:
        """
        Parse command-line arguments for the code generation input.

        Returns:
            argparse.Namespace: Parsed arguments including target_file, improvements, user_guidance, and output.
        """
        parser = argparse.ArgumentParser(
            description="Generate a CodeGenerationInput JSON file for the self-improvement system."
        )
        parser.add_argument(
            "--target_file",
            type=str,
            help="The target file for which improvements are to be made.",
            required=False,
        )
        parser.add_argument(
            "--improvements",
            type=str,
            help="The improvements description.",
            required=False,
        )
        parser.add_argument(
            "--user_guidance",
            type=str,
            help="Additional user guidance for the self-improvement process.",
            default="",
            required=False,
        )
        parser.add_argument(
            "--output",
            type=str,
            help="Output JSON file path.",
            default="code_generation_input.json",
            required=False,
        )
        return parser.parse_args()

    @staticmethod
    def get_input(prompt_text: str) -> str:
        """
        Prompt the user for input via the command line.

        Args:
            prompt_text: The prompt to display to the user.

        Returns:
            The user input string.

        Raises:
            SystemExit: If no input is received (EOF).
        """
        try:
            return input(prompt_text).strip()
        except EOFError:
            sys.exit(1)
        else:
            pass
        finally:
            pass

    @staticmethod
    def build_input_dict(
        target_file: str, improvements: str, user_guidance: str
    ) -> dict[str, str]:
        """
        Build the code generation input dictionary.

        Args:
            target_file: Target file name.
            improvements: Description of improvements.
            user_guidance: Additional user guidance.

        Returns:
            A dictionary conforming to the CodeGenerationInput schema.
        """
        return {
            "target_file": target_file,
            "improvements": improvements,
            "user_guidance": user_guidance,
        }

    @staticmethod
    def validate_input(data: dict[str, str]) -> None:
        """
        Validate that the input contains necessary information.

        Args:
            data: The input data dictionary.

        Raises:
            ValueError: If required fields are missing or empty.
        """
        if not data.get("target_file"):
            raise ValueError("The target_file field must be provided and non-empty.")
        else:
            pass
        if not data.get("improvements"):
            raise ValueError("The improvements field must be provided and non-empty.")
        else:
            pass

    def run(self) -> None:
        """
        Execute the main logic: parse arguments, collect input, validate, format, and save JSON.
        """
        args = self.parse_arguments()
        target_file = args.target_file or self.get_input("Enter the target file: ")
        improvements = args.improvements or self.get_input(
            "Enter the improvements description: "
        )
        user_guidance = args.user_guidance or self.get_input(
            "Enter additional user guidance (optional): "
        )
        code_gen_input = self.build_input_dict(target_file, improvements, user_guidance)
        try:
            self.validate_input(code_gen_input)
        except ValueError as e:
            self.logger.log_error(f"Validation error: {e}")
            raise
        else:
            pass
        finally:
            pass
        content = self.output_formatter.to_json(code_gen_input, pretty=True)
        output_path = Path(args.output)
        try:
            self.directory_manager.ensure_directory_exists(output_path.parent)
            self.file_generator.save_file(content, output_path)
            self.logger.log_info(f"JSON file successfully saved to: {output_path}")
        except Exception as e:
            self.logger.log_error(f"Error saving JSON file: {e}")
            raise
        else:
            pass
        finally:
            pass
        self.logger.log_info("Process completed successfully.")


def main() -> None:
    """
    Main entry point for the script.
    """
    analyzer = IntegratedO3Analyzer()
    try:
        analyzer.run()
    except Exception as e:
        logger = get_logger()
        logger.log_error(f"Process terminated with errors: {e}")
        sys.exit(1)
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
