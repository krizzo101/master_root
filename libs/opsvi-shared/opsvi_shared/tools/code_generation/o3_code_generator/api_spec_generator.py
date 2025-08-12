"""
API Specification Generator - AI-powered API specification generation using OpenAI's O3 models.

This module provides a CLI and programmatic interface to generate comprehensive API
specifications (OpenAPI 3.0, JSON, Markdown, HTML, YAML) from interface designs and
requirements using OpenAI's O3 models.
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

from openai import OpenAI

from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
    ConfigManager,
)
from src.tools.code_generation.o3_code_generator.prompts.technical_spec_prompts import (
    API_SPEC_SYSTEM_PROMPT,
)
from src.tools.code_generation.o3_code_generator.schemas.technical_spec_schemas import (
    APISpecInput,
    APISpecOutput,
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
from src.tools.code_generation.o3_code_generator.utils.prompt_builder import (
    PromptBuilder,
)


class APISpecGenerator:
    """
    Main API specification generator using OpenAI O3 models.

    Attributes:
        logger: O3Logger instance for logging.
        config_manager: ConfigManager for loading configuration.
        client: OpenAI client instance.
        input_loader: UniversalInputLoader for reading input files.
        directory_manager: DirectoryManager for managing directories.
        file_generator: FileGenerator for writing output files.
        prompt_builder: PromptBuilder for constructing model prompts.
    """

    def __init__(self, config_path: str | None = None) -> None:
        """
        Initialize the APISpecGenerator.

        Args:
            config_path: Optional path to configuration file.
        """
        self.logger = get_logger()
        self.logger.log_info("Initializing APISpecGenerator")
        try:
            self.config_manager = ConfigManager(config_path)
            api_key = self.config_manager.get_api_key()
            api_base = self.config_manager.get_api_base_url()
            self.client = OpenAI(api_key=api_key, base_url=api_base)
            self.input_loader = UniversalInputLoader()
            self.directory_manager = DirectoryManager()
            self.file_generator = FileGenerator()
            self.prompt_builder = PromptBuilder()
            self.directory_manager.create_module_directories(
                module_name="api_spec_generator",
                additional_dirs=["generated_specs", "logs"],
            )
            self.logger.log_debug("Module directories ensured for api_spec_generator")
            self.logger.log_info("APISpecGenerator initialization complete")
        except Exception as e:
            self.logger.log_error(e, "APISpecGenerator initialization failed")
            raise
        else:
            pass
        finally:
            pass

    def generate_api_specs(self, input_data: APISpecInput) -> APISpecOutput:
        """
        Generate comprehensive API specifications.

        Args:
            input_data: APISpecInput containing interface design and requirements.

        Returns:
            APISpecOutput with generated specifications.
        """
        start_time = time.time()
        try:
            self.logger.log_info("Starting API specification generation")
            prompt = self.prompt_builder.build_generation_prompt(
                input_data=input_data,
                context=None,
                system_prompt=API_SPEC_SYSTEM_PROMPT,
            )
            self.logger.log_debug("Prompt built for API spec generation")
            # Updated for OpenAI Python SDK v1.x
            response = self.client.chat.completions.create(
                model=input_data.model,
                messages=[
                    {"role": "system", "content": API_SPEC_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            self.logger.log_debug("Model response received")
            raw_output = response.choices[0].message.content
            api_data = json.loads(raw_output)
            specs = api_data["api_specifications"]
            files = self.file_generator.create_analysis_files(
                analysis_data=specs,
                module_name="api_spec_generator",
                title=f"api_spec_{int(time.time())}",
                formats=[input_data.output_format.value],
            )
            self.logger.log_info(f"API specifications saved: {files}")
            elapsed = time.time() - start_time
            self.logger.log_info(
                f"API specification generation completed in {elapsed:.2f}s"
            )
            return APISpecOutput(
                openapi_spec=specs["openapi_spec"],
                endpoints=specs["endpoints"],
                authentication_spec=specs["authentication_spec"],
                rate_limiting_spec=specs["rate_limiting_spec"],
                error_handling_spec=specs["error_handling_spec"],
                documentation=specs["documentation"],
            )
        except Exception as e:
            self.logger.log_error(e, "API specification generation failed")
            raise
        else:
            pass
        finally:
            pass


def main() -> None:
    """
    Main entry point for the API specification generator CLI.
    """
    parser = argparse.ArgumentParser(
        description="Generate API specifications using O3 models"
    )
    parser.add_argument(
        "input_file", help="Path to JSON/YAML file with API specification requirements"
    )
    parser.add_argument(
        "--config", help="Optional path to configuration file", default=None
    )
    args = parser.parse_args()
    logger = get_logger()
    try:
        generator = APISpecGenerator(config_path=args.config)
        data = generator.input_loader.load_file_by_extension(Path(args.input_file))
        input_obj = APISpecInput(**data)
        _ = generator.generate_api_specs(input_obj)
        logger.log_info("API specification generation succeeded")
        logger.log_user_action(
            "api_spec_generation_completed",
            {
                "format": input_obj.output_format.value,
                "endpoints": len(input_obj.output_format.value and []),
            },
        )
        sys.exit(0)
    except Exception as e:
        logger.log_error(e, "Error in main")
        sys.exit(1)
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
