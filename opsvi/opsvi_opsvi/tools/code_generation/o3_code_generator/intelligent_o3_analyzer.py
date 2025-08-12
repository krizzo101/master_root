"""Intelligent File Analyzer using the O3 model.

This module provides a command‐line tool to analyze code or data files for potential
improvements using the O3 model. It supports two modes:
  - analysis: prints JSON‐formatted improvement suggestions to stdout
  - full: generates structured improvement request files in a dedicated directory

Usage:
    python intelligent_o3_analyzer.py [paths ...] [--mode analysis|full] [--filter type1,type2,...]
"""

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    setup_logger,
)

setup_logger(LogConfig())
import argparse
import time
from pathlib import Path
from typing import Any

from src.tools.code_generation.o3_code_generator.auto_rules_generation.ast_analyzer import (
    ASTAnalyzer,
)
from src.tools.code_generation.o3_code_generator.o3_code_generator import (
    O3CodeGenerator,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger
from src.tools.code_generation.o3_code_generator.schemas.file_analysis_output import (
    FileAnalysisOutput,
)
from src.tools.code_generation.o3_code_generator.schemas.input_schema import (
    CodeGenerationInput,
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


def get_language_from_extension(file_path: str) -> str:
    """
    Determine the programming language based on the file extension.
    """
    extension = Path(file_path).suffix.lower()
    mapping: dict[str, str] = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
    }
    return mapping.get(extension, "text")


def prepare_analysis_prompt(file_name: str, file_content: str) -> str:
    """
    Prepare the analysis prompt for the O3 model.
    """
    is_test_file = "test" in file_name.lower() or file_name.startswith("test_")
    if is_test_file:
        system_prompt = f"Analyze the test file '{file_name}' for potential improvement opportunities. Consider test coverage, test quality, documentation, and testing best practices."
    else:
        system_prompt = f"Analyze the file '{file_name}' for potential improvement opportunities. Consider performance, security, code quality, documentation, and architecture. Do NOT suggest unit tests for non-test files."
    analysis_data: dict[str, Any] = {
        "file_name": file_name,
        "file_content": file_content,
    }
    input_data = {"file_name": file_name, "file_content": file_content}
    builder = PromptBuilder()
    return builder.build_analysis_prompt(
        input_data=input_data,
        analysis_data=analysis_data,
        system_prompt=system_prompt,
        instructions=None,
    )


class IntelligentFileAnalyzer:
    """
    Intelligent File Analyzer using the O3 model.

    Attributes:
        mode: 'analysis' or 'full'.
        filters: list of improvement types to include or None.
        loader: UniversalInputLoader instance.
        directory_manager: DirectoryManager instance.
        formatter: OutputFormatter instance.
        file_generator: FileGenerator instance.
        generator: O3CodeGenerator instance.
        improvement_dir: Path to save improvement files.
        max_retries: maximum retry attempts for model generation.
        retry_delay: delay in seconds between retries.
        logger: O3Logger instance.
    """

    def __init__(
        self, mode: str = "analysis", filters: list[str] | None = None
    ) -> None:
        self.logger = get_logger()
        self.mode = mode
        self.filters = filters
        self.loader = UniversalInputLoader()
        self.ast_analyzer = ASTAnalyzer()
        self.directory_manager = DirectoryManager()
        self.formatter = OutputFormatter()
        self.file_generator = FileGenerator()
        self.generator = O3CodeGenerator()
        self.improvement_dir = Path("self_improvement")
        try:
            self.directory_manager.ensure_directory_exists(self.improvement_dir)
        except Exception as e:
            self.logger.log_error(f"Failed to create improvement directory: {e}")
            raise RuntimeError("Could not ensure improvement directory") from e
        else:
            pass
        finally:
            pass
        self.max_retries = 3
        self.retry_delay = 2

    def _serialize_for_json(self, obj):
        """Recursively convert Path objects to str for JSON serialization."""
        if isinstance(obj, dict):
            return {k: self._serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_for_json(i) for i in obj]
        elif hasattr(obj, "__dict__"):
            return self._serialize_for_json(obj.__dict__)
        elif isinstance(obj, Path):
            return str(obj)
        else:
            return obj

    def analyze_file(self, file_path: str) -> dict[str, Any]:
        """
        Analyze a single file and return improvement suggestions as a dict.
        """
        ext = Path(file_path).suffix.lower()
        if ext == ".py":
            analysis = self.ast_analyzer.analyze_file(Path(file_path))
            self.logger.log_info(f"AST analysis for {file_path}: {analysis}")
            with open(file_path, encoding="utf-8") as f:
                code_content = f.read()
            analysis_dict = self._serialize_for_json(analysis)
            analysis_summary = self.formatter.to_json(analysis_dict, pretty=False)
            file_name = Path(file_path).name
            schema_example = '{\n  "file": "path/to/file.py",\n  "improvements": [\n    {\n      "issue_type": "code_quality",\n      "message": "Add module-level docstring",\n      "reasoning": "Every Python file should have a module-level docstring for documentation",\n      "confidence": 0.9\n    },\n    {\n      "issue_type": "performance",\n      "message": "Use list comprehension instead of for loop",\n      "reasoning": "List comprehension is more efficient and Pythonic",\n      "confidence": 0.8\n    }\n  ]\n}'
            system_instructions = f"You are an expert AI code analyzer. Respond ONLY with valid JSON matching this exact format. No markdown, no commentary.\nJSON format:\n{schema_example}"
            prompt = (
                system_instructions
                + "\n\n"
                + prepare_analysis_prompt(
                    file_name,
                    code_content + "\n\n# AST Analysis Summary\n" + analysis_summary,
                )
            )
            language = get_language_from_extension(file_path)
        else:
            try:
                loaded = self.loader.load_file_by_extension(Path(file_path))
            except Exception as e:
                self.logger.log_error(f"Error loading file {file_path}: {e}")
                raise RuntimeError(f"Loading failed for {file_path}") from e
            else:
                pass
            finally:
                pass
            code_content = (
                self.formatter.to_json(loaded, pretty=False)
                if isinstance(loaded, dict)
                else loaded
            )
            file_name = Path(file_path).name
            prompt = prepare_analysis_prompt(file_name, code_content)
            language = get_language_from_extension(file_path)
        input_data = CodeGenerationInput(
            prompt=prompt,
            model="o3-mini",
            file_name=f"{file_name}_improvement.json",
            file_path=str(self.improvement_dir),
            language=language,
            requirements=[
                "Ensure output is a valid JSON improvement request adhering to the provided schema."
            ],
            style_guide="Follow project specific guidelines and PEP 8 where applicable.",
            additional_context=f"File path: {file_path}",
        )
        retry = 0
        output = None
        while retry < self.max_retries:
            self.logger.log_info(f"Analyzing {file_path}, attempt {retry + 1}")
            try:
                output = self.generator.generate_code(
                    input_data, output_schema=FileAnalysisOutput
                )
                validated = output
                break
            except Exception as e:
                self.logger.log_error(
                    f"Model error or validation error for {file_path}: {e}"
                )
                retry += 1
                time.sleep(self.retry_delay)
                continue
            else:
                pass
            finally:
                pass
        else:
            pass
        if output is None:
            self.logger.log_error(
                f"Failed after {self.max_retries} retries for {file_path}"
            )
            return {
                "file": file_path,
                "improvements": [
                    {
                        "issue_type": "unknown",
                        "message": "No suggestions could be generated.",
                        "reasoning": "Empty response after retries.",
                        "confidence": 0,
                    }
                ],
            }
        else:
            pass
        try:
            data = validated.dict()
        except Exception as e:
            self.logger.log_error(f"Conversion to dict failed for {file_path}: {e}")
            data = {
                "file": file_path,
                "improvements": [
                    {
                        "issue_type": "parsing_error",
                        "message": "Failed to process structured output.",
                        "reasoning": str(e),
                        "confidence": 0,
                    }
                ],
            }
        else:
            pass
        finally:
            pass
        if self.filters:
            improvements = data.get("improvements", [])
            filtered = [
                imp for imp in improvements if imp.get("issue_type") in self.filters
            ]
            data["improvements"] = filtered
        else:
            pass
        count = len(data.get("improvements", []))
        self.logger.log_info(f"Completed analysis for {file_path}: {count} items")
        return data

    def process_file(self, file_path: str) -> None:
        """
        Process a single file: analyze and display or save improvements.
        """
        try:
            result = self.analyze_file(file_path)
        except Exception as e:
            self.logger.log_error(f"Analysis failed for {file_path}: {e}")
            return
        else:
            pass
        finally:
            pass
        if self.mode == "analysis":
            formatted = self.formatter.to_json(result, pretty=True)
            self.logger.log_info(f"Analysis for {file_path}:\n{formatted}")
            return
        else:
            pass
        if self.mode == "full":
            improvements = result.get("improvements", [])
            if not improvements:
                self.logger.log_info(f"No improvements for {file_path}")
                return
            else:
                pass
            try:
                files = self.file_generator.create_analysis_files(
                    analysis_data=result,
                    module_name=Path(file_path).stem,
                    title="Improvements",
                    formats=["json"],
                )
                for fpath in files:
                    self.logger.log_info(f"Generated improvement file: {fpath}")
                else:
                    pass
            except Exception as e:
                self.logger.log_error(f"Failed to generate files for {file_path}: {e}")
                raise RuntimeError("File generation error") from e
            else:
                pass
            finally:
                pass
            return
        else:
            pass
        self.logger.log_error(f"Invalid mode: {self.mode}")
        raise ValueError(f"Invalid mode: {self.mode}")

    def process_paths(self, paths: list[str]) -> None:
        """
        Process a list of file or directory paths.
        """
        for path_str in paths:
            path = Path(path_str)
            if path.is_file():
                self.process_file(str(path.resolve()))
            elif path.is_dir():
                for ext in ("py", "js", "ts", "json", "yaml", "yml"):
                    for file in path.resolve().rglob(f"*.{ext}"):
                        self.process_file(str(file.resolve()))
                    else:
                        pass
                else:
                    pass
            else:
                self.logger.log_error(f"Invalid path: {path_str}")
        else:
            pass


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Intelligent File Analyzer using O3 model"
    )
    parser.add_argument("paths", nargs="+", help="File or directory paths to analyze")
    parser.add_argument(
        "--mode",
        choices=["analysis", "full"],
        default="analysis",
        help="Mode: 'analysis' to display issues, 'full' to generate files",
    )
    parser.add_argument(
        "--filter",
        type=str,
        help="Comma separated list of improvement types to include",
    )
    return parser.parse_args()


def main() -> None:
    """
    Main entry point.
    """
    args = parse_arguments()
    filters = [f.strip() for f in args.filter.split(",")] if args.filter else None
    analyzer = IntelligentFileAnalyzer(mode=args.mode, filters=filters)
    analyzer.process_paths(args.paths)


if __name__ == "__main__":
    main()
else:
    pass
