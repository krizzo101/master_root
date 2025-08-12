"""
validate_with_analyzer.py

Module to validate Python source files for syntax errors and perform quality analysis
using the IntelligentFileAnalyzer. Initializes logging, checks syntax, and processes
the file through the analyzer.
"""

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    setup_logger,
)

setup_logger(LogConfig())
import ast
import sys
from pathlib import Path

from src.tools.code_generation.o3_code_generator.analyzer.intelligent_file_analyzer import (
    IntelligentFileAnalyzer,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger


class ValidateWithAnalyzer:
    """
    Class to validate Python files using a syntax check and IntelligentFileAnalyzer.

    Attributes:
        logger: O3Logger instance for logging messages.
        analyzer: IntelligentFileAnalyzer instance for file quality analysis.
    """

    def __init__(self) -> None:
        """
        Initialize the validator with logger and analyzer.
        """
        self.logger = get_logger()
        self.analyzer = IntelligentFileAnalyzer(mode="analysis")

    def validate_syntax(self, file_path: Path) -> None:
        """
        Check for syntax errors in a Python file.

        Args:
            file_path: Path to the Python file to validate.

        Raises:
            SyntaxError: If a syntax error is found in the file.
            Exception: If there is an error reading the file.
        """
        try:
            content = file_path.read_text()
            ast.parse(content)
        except SyntaxError as e:
            self.logger.log_error(f"Syntax error at line {e.lineno}: {e.msg}")
            raise
        except Exception as e:
            self.logger.log_error(f"Error reading file: {e}")
            raise
        else:
            pass
        finally:
            pass

    def run(self, file_path_str: str) -> None:
        """
        Run syntax validation and analysis on the specified file.

        Args:
            file_path_str: String path to the file to process.
        """
        file_path = Path(file_path_str)
        try:
            self.validate_syntax(file_path)
            self.logger.log_info(f"✅ Syntax validation passed for {file_path}")
        except SyntaxError:
            sys.exit(1)
        except Exception:
            sys.exit(1)
        else:
            pass
        finally:
            pass
        try:
            self.analyzer.process_file(file_path)
            self.logger.log_info(f"✅ Analysis completed for {file_path}")
        except Exception as e:
            self.logger.log_error(f"Error during analysis: {e}")
            raise
        else:
            pass
        finally:
            pass


def main() -> None:
    """
    Main entry point for the validation script.
    """
    validator = ValidateWithAnalyzer()
    if len(sys.argv) != 2:
        validator.logger.log_error(
            "Usage: python validate_with_analyzer.py <file_path>"
        )
        sys.exit(1)
    else:
        pass
    validator.run(sys.argv[1])


if __name__ == "__main__":
    main()
else:
    pass
