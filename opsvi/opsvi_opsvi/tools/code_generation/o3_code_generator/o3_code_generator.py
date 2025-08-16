"""O3 Code Generator - Advanced AI-powered code generation using OpenAI's O3 models."""

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    setup_logger,
)

setup_logger(LogConfig())
import argparse
import sys
from pathlib import Path

from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
    ConfigManager,
)
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
from src.tools.code_generation.o3_code_generator.utils.prompt_builder import (
    PromptBuilder,
)

DEFAULT_FORMATS: list[str] = ["json", "markdown", "html", "yaml"]


class O3CodeGenerator:
    """Orchestrates the code generation process using shared utilities."""

    def __init__(self, config_path: str | None = None) -> None:
        """
        Initialize O3CodeGenerator.

        Args:
            config_path: Optional path to configuration file.
        """
        self.config_manager = ConfigManager(config_path)
        self.logger = get_logger()
        directory_manager = DirectoryManager()
        paths_config = self.config_manager.get_paths_config()
        directory_manager.ensure_directory_exists(paths_config.generated_files)
        logging_config = self.config_manager.get_logging_config()
        directory_manager.ensure_directory_exists(logging_config.log_dir)
        self.input_loader = UniversalInputLoader()
        self.prompt_builder = PromptBuilder()
        self.file_generator = FileGenerator()
        self.orchestrator = None
        self.o3_model_generator = O3ModelGenerator()

    def generate_code(
        self, input_data: "CodeGenerationInput", output_schema=None
    ) -> "CodeGenerationOutput":
        """
        Generate code based on the input data using O3 models.

        Args:
            input_data: CodeGenerationInput object containing generation parameters.
            output_schema: Optional Pydantic model for output validation.

        Returns:
            Validated output object (using output_schema if provided, else CodeGenerationOutput).
        """
        try:
            from src.tools.code_generation.o3_code_generator.schemas.output_schema import (
                CodeGenerationOutput,
            )

            self.logger.log_info(f"Generating code for: {input_data.file_name}")
            full_prompt = self._build_prompt(input_data)
            model_output = self._generate_with_o3_model(
                full_prompt, input_data.model, output_schema
            )
            cleaned = model_output.strip()
            self.logger.log_info(f"Model output preview: {cleaned[:200]}...")
            import json
            import re

            json_match = re.search(
                "```(?:json)?\\s*(\\{.*?\\})\\s*```", cleaned, re.DOTALL
            )
            if json_match:
                cleaned = json_match.group(1)
            elif cleaned.startswith("```"):
                cleaned = re.sub("^```(?:json)?\\s*", "", cleaned)
                cleaned = re.sub("\\s*```$", "", cleaned)
            else:
                pass
            try:
                parsed = json.loads(cleaned)
            except Exception as e:
                self.logger.log_error(e, "Model output is not valid JSON")
                raise ValueError(f"Model output is not valid JSON: {e}")
            else:
                pass
            finally:
                pass
            if output_schema is not None:
                try:
                    validated = output_schema.parse_obj(parsed)
                    return validated
                except Exception as e:
                    self.logger.log_error(
                        e, f"Output validation failed for schema {output_schema}"
                    )
                    raise
                else:
                    pass
                finally:
                    pass
            else:
                pass
            try:
                validated = CodeGenerationOutput.parse_obj(parsed)
                return validated
            except Exception as e:
                self.logger.log_error(
                    e, "Output validation failed for CodeGenerationOutput"
                )
                raise
            else:
                pass
            finally:
                pass
        except Exception as e:
            self.logger.log_error(
                e, f"Code generation failed for {input_data.file_name}"
            )
            from src.tools.code_generation.o3_code_generator.schemas.output_schema import (
                CodeGenerationOutput,
            )

            return CodeGenerationOutput(
                code="",
                file_name=input_data.file_name,
                success=False,
                error_message=str(e),
            )
        else:
            pass
        finally:
            pass

    def _build_prompt(self, input_data: "CodeGenerationInput") -> str:
        """Build the full prompt with context files, sanitizing all content."""
        prompt = input_data.prompt

        def sanitize(text: str) -> str:
            return text.replace('"""', '"""').replace("'''", "'''")

        if input_data.context_files:
            context_content = []
            for context_file in input_data.context_files:
                try:
                    if Path(context_file).exists():
                        content = Path(context_file).read_text(encoding="utf-8")
                        context_content.append(
                            f"--- {context_file} ---\n{sanitize(content)}\n---"
                        )
                    else:
                        pass
                except Exception as e:
                    self.logger.log_warning(
                        f"Could not load context file {context_file}: {e}"
                    )
                else:
                    pass
                finally:
                    pass
            else:
                pass
            if context_content:
                prompt = f"CONTEXT FILES:\n\n{chr(10).join(context_content)}\n\nENHANCEMENT REQUEST:\n\n{sanitize(prompt)}"
            else:
                prompt = sanitize(prompt)
        else:
            prompt = sanitize(prompt)
        return prompt

    def _generate_with_o3_model(
        self, prompt: str, model: str, output_schema=None
    ) -> str:
        """
        Generate code using O3 model with structured output support.
        """
        response_format = None
        if output_schema:
            if hasattr(output_schema, "model_json_schema"):
                schema = output_schema.model_json_schema()
                schema["additionalProperties"] = False
                if "$defs" in schema:
                    for def_name, def_schema in schema["$defs"].items():
                        if (
                            isinstance(def_schema, dict)
                            and def_schema.get("type") == "object"
                        ):
                            def_schema["additionalProperties"] = False
                        else:
                            pass
                    else:
                        pass
                else:
                    pass
                response_format = schema
            else:
                response_format = output_schema
        else:
            pass
        schema_example = '{\n  "code": "def example_function():\n    return True",\n  "explanation": "This is an example function",\n  "issues": ["Fixed indentation", "Added return type"],\n  "prompt_feedback": "Prompt was clear and specific"\n}'
        system_instructions = (
            "You are an expert AI code generator. Follow all project and universal rules strictly. CRITICAL: You MUST respond with ONLY valid JSON. No markdown, no explanations outside the JSON. The 'code' field must contain the complete Python file content as a string. Your response MUST be parseable by Python's json.loads().\nExample response format:\n"
            + schema_example
            + "\nIMPORTANT: Start your response with { and end with }. No other text."
        )
        messages = [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": prompt},
        ]
        return self.o3_model_generator.generate(
            messages, response_format=response_format
        )

    def validate_generated_code(self, output: "CodeGenerationOutput") -> bool:
        """
        Validate generated code syntax without saving to file.
        Returns True if code is valid, False otherwise.
        """
        import ast

        try:
            if not output.success:
                self.logger.log_error(
                    Exception("Code generation failed"),
                    f"Code generation failed: {output.error_message}",
                )
                return False
            else:
                pass
            try:
                ast.parse(output.code)
                return True
            except SyntaxError as e:
                self.logger.log_error(e, f"Generated code has syntax error: {e}")
                return False
            else:
                pass
            finally:
                pass
        except Exception as e:
            self.logger.log_error(e, "Failed to validate generated code")
            return False
        else:
            pass
        finally:
            pass


def main() -> None:
    """Main entry point for the O3 Code Generator."""
    parser = argparse.ArgumentParser(
        description="O3 Code Generator - Advanced AI-powered code generation"
    )
    parser.add_argument(
        "input_file",
        help="Path to input file (JSON or YAML) containing generation parameters",
    )
    parser.add_argument("--config", help="Path to configuration file", default=None)
    parser.add_argument(
        "--formats",
        help="Comma-separated list of output formats (json, markdown, html, yaml)",
        default=",".join(DEFAULT_FORMATS),
    )
    args = parser.parse_args()
    try:
        generator = O3CodeGenerator(args.config)
        formats_list = [fmt.strip() for fmt in args.formats.split(",") if fmt.strip()]
        file_paths = generator.generate_code(args.input_file, formats_list)
        logger = get_logger()
        for path in file_paths:
            logger.log_info(f"File saved: {path}")
        else:
            pass
        sys.exit(0)
    except Exception as e:
        logger = get_logger()
        logger.log_error(e)
        sys.exit(1)
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
