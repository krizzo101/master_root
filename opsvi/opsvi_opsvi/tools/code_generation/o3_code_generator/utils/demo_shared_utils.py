"""
Demo module for O3 Code Generator shared utilities.

This module demonstrates basic usage of shared utility classes:
DirectoryManager, OutputFormatter, FileGenerator, PromptBuilder, and UniversalInputLoader.
It initializes logging, instantiates each class, invokes sample methods, and logs results.
"""
from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    setup_logger,
    LogConfig,
    get_logger,
)
from src.tools.code_generation.o3_code_generator.utils.directory_manager import (
    DirectoryManager,
)
from src.tools.code_generation.o3_code_generator.utils.output_formatter import (
    OutputFormatter,
)
from src.tools.code_generation.o3_code_generator.utils.file_generator import (
    FileGenerator,
)
from src.tools.code_generation.o3_code_generator.utils.prompt_builder import (
    PromptBuilder,
)
from src.tools.code_generation.o3_code_generator.utils.input_loader import (
    UniversalInputLoader,
)

setup_logger(LogConfig())
logger = get_logger()


def main():
    """Main demonstration function."""
    try:
        logger.log_info("Starting demo of shared utilities")
        dm = DirectoryManager()
        module_name = "demo_module"
        dm.create_module_directories(module_name, additional_dirs=["data", "cache"])
        output_path = dm.get_module_output_path(module_name)
        logger.log_info(
            f"DirectoryManager.get_module_output_path returned: {output_path}"
        )
        formatter = OutputFormatter()
        sample_data = {"key1": "value1", "key2": [1, 2, 3]}
        json_content = formatter.to_json(sample_data)
        logger.log_info(f"OutputFormatter.to_json returned: {json_content}")
        fg = FileGenerator()
        timestamped = fg.create_timestamped_filename("demo_report", ".txt")
        logger.log_info(
            f"FileGenerator.create_timestamped_filename returned: {timestamped}"
        )
        pb = PromptBuilder()
        input_data = {"param": 42}
        analysis_data = {"result": "success"}
        system_prompt = "Analyze data."
        prompt = pb.build_analysis_prompt(input_data, analysis_data, system_prompt)
        logger.log_info(
            f"PromptBuilder.build_analysis_prompt returned prompt of length {len(prompt)}"
        )
        loader = UniversalInputLoader()
        cleaned = loader.clean_template_data({"_meta": "skip", "field": "keep"})
        logger.log_info(f"UniversalInputLoader.clean_template_data returned: {cleaned}")
        loader.validate_required_fields({"field": "value"}, ["field"])
        logger.log_info("UniversalInputLoader.validate_required_fields succeeded")
        logger.log_info("Completed demo of shared utilities")
    except Exception as e:
        logger.log_error(f"Demo encountered an error: {e}")
        raise
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
